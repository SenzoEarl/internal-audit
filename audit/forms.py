from django import forms
from audit.models import Client, Audit, Project


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['contact_name', 'contact_email', 'contact_phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class AuditForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['project', 'audit_date', 'audit_type', 'audit_number', 'performed_by', 'report_number']
        widgets = {
            'audit_date': forms.DateInput(attrs={'type': 'date'}),
        }


class AuditScoreForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['overall_score_percentage', 'standard_required']


class AuditNoticesForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['improvement_notices', 'contravention_notices', 'prohibition_notices']


class AuditModelForm(forms.ModelForm):
    """Full audit form used server-side to validate combined data."""

    class Meta:
        model = Audit
        fields = [
            'project', 'audit_date', 'audit_type', 'audit_number', 'performed_by', 'report_number',
            'overall_score_percentage', 'standard_required',
            'improvement_notices', 'contravention_notices', 'prohibition_notices'
        ]
        widgets = {
            'audit_date': forms.DateInput(attrs={'type': 'date'})
        }
