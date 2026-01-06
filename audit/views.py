from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
import json
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from audit.forms import ClientForm, AuditForm, AuditScoreForm, AuditNoticesForm, AuditModelForm


# Create your views here.
class IndexView(TemplateView):
    template_name = 'index.html'


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'
    login_url = '/'  # redirect to index (login form) if unauthenticated


class ClientDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/clients/index.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from audit.models import Client
        # Query all clients ordered by name
        ctx['clients'] = Client.objects.all().order_by('name')
        return ctx


class ReportDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/reports/index.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from audit.models import Audit
        # Fetch audits with related project and client to avoid N+1 queries
        audit_qs = Audit.objects.select_related('project', 'project__client').order_by('-audit_date')
        # Paginate
        paginator = Paginator(audit_qs, 10)  # 10 audits per page
        page = self.request.GET.get('page')
        try:
            audits_page = paginator.page(page)
        except PageNotAnInteger:
            audits_page = paginator.page(1)
        except EmptyPage:
            audits_page = paginator.page(paginator.num_pages)

        ctx['audits'] = audits_page.object_list
        ctx['page_obj'] = audits_page
        ctx['paginator'] = paginator
        return ctx


class LoginAjaxView(View):
    """
    Handle AJAX (and form) login requests.
    Accepts JSON payloads (Content-Type: application/json) or regular form POSTs.
    Returns JSON with detailed, safe error messages and a redirect URL on success.
    """

    def post(self, request, *args, **kwargs):
        # Parse data from JSON body or form-encoded POST
        username = ''
        password = ''
        is_json = request.content_type == 'application/json'
        if is_json:
            try:
                payload = json.loads(request.body.decode('utf-8') or '{}')
            except Exception:
                # For non-AJAX we'll redirect with message; for AJAX return JSON
                if not is_json:
                    messages.error(request, 'Invalid request payload.')
                    return redirect('audit:index')
                return JsonResponse({'success': False, 'errors': {'__all__': 'Invalid request payload.'}}, status=400)
            username = (payload.get('username') or '').strip()
            password = payload.get('password') or ''
        else:
            username = (request.POST.get('username') or '').strip()
            password = request.POST.get('password') or ''

        errors = {}
        if not username:
            errors['username'] = 'Please enter your username.'
        if not password:
            errors['password'] = 'Please enter your password.'
        if errors:
            if not is_json:
                # Attach messages and redirect back to index so regular form gets feedback via messages
                for v in errors.values():
                    messages.error(request, v)
                return redirect('audit:index')
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        user = authenticate(request, username=username, password=password)
        if user is None:
            # Don't reveal whether username exists for security; keep message generic
            if not is_json:
                messages.error(request, 'Invalid username or password.')
                return redirect('audit:index')
            return JsonResponse({'success': False, 'errors': {'__all__': 'Invalid username or password.'}}, status=400)
        if not user.is_active:
            if not is_json:
                messages.error(request, 'This account is inactive.')
                return redirect('audit:index')
            return JsonResponse({'success': False, 'errors': {'__all__': 'This account is inactive.'}}, status=400)

        # Log the user in (Django handles password hashing and session security)
        login(request, user)

        # Determine a safe redirect. Prefer reversing the named URL if available.
        try:
            from django.urls import reverse

            redirect_url = reverse('audit:dashboard')
        except Exception:
            redirect_url = '/dash/'

        # If the request was AJAX/JSON prefer JSON response, otherwise redirect
        if is_json or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect': redirect_url})
        return HttpResponseRedirect(redirect_url)

    def get(self, request, *args, **kwargs):
        # Disallow GET for login endpoint
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)


class LogoutAjaxView(View):
    """AJAX logout endpoint. Accepts POST to log the user out and returns JSON."""

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # If this is an AJAX/JSON request return JSON error, otherwise redirect to index
            if request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': {'__all__': 'Not authenticated.'}}, status=400)
            messages.error(request, 'Not authenticated.')
            return redirect('audit:index')
        # perform logout
        logout(request)
        # If AJAX/JSON request, return JSON indicating redirect; otherwise perform a redirect to index
        if request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect': '/'})
        return HttpResponseRedirect('/')

    def get(self, request, *args, **kwargs):
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)


class ClientDetailAjaxView(LoginRequiredMixin, View):
    """Return client details as JSON for display in modal."""

    def get(self, request, pk, *args, **kwargs):
        from audit.models import Client
        client = get_object_or_404(Client, pk=pk)
        data = {
            'id': client.id,
            'name': client.name,
            'contact_name': client.contact_name or '',
            'contact_email': client.contact_email or '',
            'contact_phone': client.contact_phone or '',
            'address': client.address or '',
        }
        return JsonResponse(data, encoder=DjangoJSONEncoder)


class ClientUpdateAjaxView(LoginRequiredMixin, View):
    """Accept POST with updated client fields and save via ClientForm."""

    def post(self, request, pk, *args, **kwargs):
        from audit.models import Client
        client = get_object_or_404(Client, pk=pk)
        # Support JSON body or form-encoded
        if request.content_type == 'application/json':
            try:
                payload = json.loads(request.body.decode('utf-8') or '{}')
            except Exception:
                return JsonResponse({'success': False, 'errors': {'__all__': 'Invalid JSON payload.'}}, status=400)
            # only pass allowed fields
            allowed = {k: payload.get(k) for k in ['contact_name', 'contact_email', 'contact_phone', 'address']}
            form = ClientForm(allowed, instance=client)
        else:
            form = ClientForm(request.POST, instance=client)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            # Return form errors in a simple dict
            errors = {k: v.get_json_data() for k, v in form.errors.items()}
            # Convert to simple messages
            simple = {k: [err['message'] for err in v] for k, v in errors.items()}
            return JsonResponse({'success': False, 'errors': simple}, status=400)


class AuditDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/reports/detail.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from audit.models import Audit
        audit = get_object_or_404(Audit, pk=kwargs.get('pk'))
        ctx['audit'] = audit
        return ctx


class AuditCreateView(LoginRequiredMixin, View):
    """Handle segmented creation of a new Audit via AJAX (accepts JSON)."""

    def get(self, request, *args, **kwargs):
        # Return structured field metadata so client can render appropriate inputs
        form = AuditForm()
        score_form = AuditScoreForm()
        notices_form = AuditNoticesForm()

        def field_meta(f):
            meta = {'name': f.name}
            field = form.fields.get(f.name) if f in form else None
            # try to detect choices
            try:
                fld = form.fields[f.name]
            except Exception:
                fld = None
            if fld is not None and getattr(fld, 'choices', None):
                meta['choices'] = [{'value': c[0], 'label': c[1]} for c in fld.choices]
            # type hints
            if fld is not None:
                from django.forms import DateField
                if isinstance(fld, DateField):
                    meta['type'] = 'date'
                else:
                    meta['type'] = 'text'
            return meta

        # Build metadata lists
        fields_meta = []
        for f in AuditForm().fields:
            fld = AuditForm().fields[f]
            meta = {'name': f}
            # ModelChoiceField: include queryset choices (serialize PKs and labels)
            if getattr(fld, 'queryset', None) is not None:
                try:
                    meta['choices'] = [{'value': str(o.pk), 'label': str(o)} for o in fld.queryset.all()]
                except Exception:
                    # Fallback to using field.choices if queryset iteration fails
                    if getattr(fld, 'choices', None):
                        meta['choices'] = [{'value': str(c[0]), 'label': str(c[1])} for c in fld.choices]
            # choices for simple ChoiceField
            elif getattr(fld, 'choices', None):
                meta['choices'] = [{'value': str(c[0]), 'label': str(c[1])} for c in fld.choices]
            # widget type
            if fld.__class__.__name__.lower().find('date') != -1 or getattr(fld, 'input_type', '') == 'date':
                meta['type'] = 'date'
            else:
                meta['type'] = 'text'
            fields_meta.append(meta)

        score_meta = []
        for f in AuditScoreForm().fields:
            fld = AuditScoreForm().fields[f]
            meta = {'name': f, 'type': 'number'}
            score_meta.append(meta)

        notice_meta = []
        for f in AuditNoticesForm().fields:
            fld = AuditNoticesForm().fields[f]
            meta = {'name': f, 'type': 'number'}
            notice_meta.append(meta)

        return JsonResponse({
            'fields': fields_meta,
            'score_fields': score_meta,
            'notice_fields': notice_meta,
        })

    def post(self, request, *args, **kwargs):
        # Accept combined JSON payload and validate with AuditModelForm
        if request.content_type != 'application/json':
            return JsonResponse({'success': False, 'errors': {'__all__': 'Expected JSON payload.'}}, status=400)
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            return JsonResponse({'success': False, 'errors': {'__all__': 'Invalid JSON payload.'}}, status=400)

        form = AuditModelForm(payload)
        if form.is_valid():
            audit = form.save()
            return JsonResponse({'success': True, 'id': audit.id})
        else:
            errors = {k: v.get_json_data() for k, v in form.errors.items()}
            simple = {k: [err['message'] for err in v] for k, v in errors.items()}
            return JsonResponse({'success': False, 'errors': simple}, status=400)


class AuditShareAjaxView(LoginRequiredMixin, View):
    """Share a report via email. Accepts POST JSON: {to_email, message}
    Sends email with a link to the report detail view."""

    def post(self, request, pk, *args, **kwargs):
        from audit.models import Audit
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError

        audit = get_object_or_404(Audit, pk=pk)
        if request.content_type != 'application/json':
            return JsonResponse({'success': False, 'errors': {'__all__': 'Expected JSON payload.'}}, status=400)
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            return JsonResponse({'success': False, 'errors': {'__all__': 'Invalid JSON payload.'}}, status=400)
        to_email = (payload.get('to_email') or '').strip()
        message = payload.get('message', '')
        if not to_email:
            return JsonResponse({'success': False, 'errors': {'to_email': ['Recipient email required.']}}, status=400)
        # Validate email format
        try:
            validate_email(to_email)
        except ValidationError:
            return JsonResponse({'success': False, 'errors': {'to_email': ['Enter a valid email address.']}}, status=400)

        # Build absolute URL to the report detail
        try:
            from django.urls import reverse
            url = request.build_absolute_uri(reverse('audit:report-detail', args=[audit.id]))
        except Exception:
            url = request.build_absolute_uri(f"/reports/{audit.id}/")

        subject = f"Audit Report: {audit.report_number}"
        body = f"{message}\n\nView the report: {url}"

        # Determine from email
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None) or 'no-reply@localhost'

        # Send email — relies on Django email settings; in production ensure TLS and creds configured
        try:
            send_mail(subject, body, from_email, [to_email], fail_silently=False)
            return JsonResponse({'success': True})
        except Exception as e:
            # Return sanitized error message
            return JsonResponse({'success': False, 'errors': {'__all__': 'Failed to send email: ' + str(e)}}, status=500)
