from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from audit.models import Client as ClientModel, ConsultingFirm, PrincipalContractor, Project, Audit
import json
from django.core import mail

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuditAppTests(TestCase):
    def setUp(self):
        # Create a user
        self.username = 'testuser'
        self.password = 'password'
        self.user = User.objects.create_user(username=self.username, password=self.password)

        # Create related models
        self.client_org = ClientModel.objects.create(name='ACME')
        self.client_org.contact_email = 'client@example.com'
        self.client_org.contact_name = 'Client Contact'
        self.client_org.save()
        self.cf = ConsultingFirm.objects.create(name='ConsultCo')
        self.pc = PrincipalContractor.objects.create(name='PrimeBuild')
        self.project = Project.objects.create(title='Test Project', permit_number='P-1', location='Site', client=self.client_org, consulting_engineer=self.cf, principal_contractor=self.pc)

        # Create a sample audit
        self.audit = Audit.objects.create(
            project=self.project,
            audit_date='2026-01-01',
            audit_type='OHS',
            audit_number='001',
            performed_by='Tester',
            report_number='R-001',
            overall_score_percentage=80.00,
            standard_required=75.00,
            improvement_notices=0,
            contravention_notices=0,
            prohibition_notices=0,
        )

        self.client = Client()

    def test_index_shows_login_when_anonymous_and_lorem_when_authenticated(self):
        # anonymous
        resp = self.client.get(reverse('audit:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Please log in to continue')

        # authenticate
        self.client.login(username=self.username, password=self.password)
        resp2 = self.client.get(reverse('audit:index'))
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, 'Lorem ipsum')

    def test_login_form_and_ajax(self):
        # non-AJAX form login should redirect to dashboard
        resp = self.client.post(reverse('audit:login-ajax'), data={'username': self.username, 'password': self.password})
        self.assertIn(resp.status_code, (302, 301))
        # AJAX JSON login
        resp2 = self.client.post(reverse('audit:login-ajax'), data=json.dumps({'username': self.username, 'password': self.password}), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        data = resp2.json()
        self.assertTrue(data.get('success'))
        self.assertIn('redirect', data)

    def test_logout_non_ajax_and_ajax(self):
        # login first
        self.client.login(username=self.username, password=self.password)
        # non-AJAX logout -> redirect
        resp = self.client.post(reverse('audit:logout-ajax'), data={})
        self.assertIn(resp.status_code, (302, 301))
        # AJAX logout: login again then call with JSON
        self.client.login(username=self.username, password=self.password)
        resp2 = self.client.post(reverse('audit:logout-ajax'), data=json.dumps({}), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.json().get('success'))

    def test_reports_create_metadata_and_post(self):
        # login
        self.client.login(username=self.username, password=self.password)
        # GET metadata
        resp = self.client.get(reverse('audit:report-create-ajax'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('fields', data)
        self.assertIn('score_fields', data)
        self.assertIn('notice_fields', data)

        # POST create
        payload = {
            'project': str(self.project.pk),
            'audit_date': '2026-01-02',
            'audit_type': 'OHS',
            'audit_number': '002',
            'performed_by': 'Creator',
            'report_number': 'R-002',
            'overall_score_percentage': '90.00',
            'standard_required': '75.00',
            'improvement_notices': 0,
            'contravention_notices': 0,
            'prohibition_notices': 0,
        }
        resp2 = self.client.post(reverse('audit:report-create-ajax'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        d2 = resp2.json()
        self.assertTrue(d2.get('success'))
        new_id = d2.get('id')
        self.assertIsNotNone(new_id)
        self.assertTrue(Audit.objects.filter(pk=new_id).exists())

    def test_share_report_success_and_invalid(self):
        self.client.login(username=self.username, password=self.password)
        # valid share
        resp = self.client.post(reverse('audit:report-share-ajax', args=[self.audit.pk]), data=json.dumps({'to_email': 'receiver@example.com', 'message': 'Please see report'}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        self.assertTrue(d.get('success'))
        # check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Audit Report', mail.outbox[0].subject)

        # invalid email
        resp2 = self.client.post(reverse('audit:report-share-ajax', args=[self.audit.pk]), data=json.dumps({'to_email': 'bad-email', 'message': ''}), content_type='application/json')
        self.assertEqual(resp2.status_code, 400)
        d2 = resp2.json()
        self.assertFalse(d2.get('success'))
        self.assertIn('to_email', d2.get('errors', {}))

    def test_client_detail_and_update(self):
        self.client.login(username=self.username, password=self.password)
        resp = self.client.get(reverse('audit:client-detail-ajax', args=[self.client_org.pk]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('name'), self.client_org.name)

        # update via JSON
        payload = {'contact_name': 'New Contact', 'contact_email': 'new@example.com', 'contact_phone': '012345', 'address': 'New Address'}
        resp2 = self.client.post(reverse('audit:client-update-ajax', args=[self.client_org.pk]), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        d2 = resp2.json()
        self.assertTrue(d2.get('success'))
        self.client_org.refresh_from_db()
        self.assertEqual(self.client_org.contact_name, 'New Contact')
        self.assertEqual(self.client_org.contact_email, 'new@example.com')

    def test_report_detail_view_requires_login_and_shows_data(self):
        # anonymous -> redirected to login (login_url='/') because of login_url set in view
        resp = self.client.get(reverse('audit:report-detail', args=[self.audit.pk]))
        # Should be a redirect to index (since LoginRequiredMixin default behavior is redirect)
        self.assertIn(resp.status_code, (302, 301))

        # login and try again
        self.client.login(username=self.username, password=self.password)
        resp2 = self.client.get(reverse('audit:report-detail', args=[self.audit.pk]))
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, self.audit.report_number)

    def test_report_dashboard_requires_login(self):
        resp = self.client.get(reverse('audit:report-dashboard'))
        self.assertIn(resp.status_code, (302, 301))
        self.client.login(username=self.username, password=self.password)
        resp2 = self.client.get(reverse('audit:report-dashboard'))
        self.assertEqual(resp2.status_code, 200)
        # should contain report_number for at least one audit
        self.assertContains(resp2, self.audit.report_number)
