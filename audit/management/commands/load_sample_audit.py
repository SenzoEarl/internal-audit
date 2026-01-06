# your_app/management/commands/load_sample_audit.py
from django.core.management.base import BaseCommand
from audit.models import (
    Client, ConsultingFirm, PrincipalContractor, Project, Audit,
    LegalAppointment, RiskRating, ActionItem
)
from django.utils import timezone


class Command(BaseCommand):
    help = 'Loads sample audit data from the Gabby Construction report'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading sample audit data...')

        # Clear existing sample data (optional)
        # Project.objects.filter(permit_number="MP-CWP/328/09/2024").delete()

        # Create entities
        mbombela, created = Client.objects.get_or_create(
            name="MBOMBELA MUNICIPALITY",
            defaults={'name': "MBOMBELA MUNICIPALITY"}
        )

        mk_dube, created = ConsultingFirm.objects.get_or_create(
            name="MK DUBE CONSULTING",
            defaults={'name': "MK DUBE CONSULTING"}
        )

        gabby, created = PrincipalContractor.objects.get_or_create(
            name="GABBY CONSTRUCTION",
            defaults={
                'name': "GABBY CONSTRUCTION",
                'registration_number': "CONSTR12345"
            }
        )

        # Create project
        project, created = Project.objects.get_or_create(
            permit_number="MP-CWP/328/09/2024",
            defaults={
                'title': "PAVING OF GOROMANE TO KAMABUZA (VIA TFOLINHLANHLA) AT SHABALALA WARD 1",
                'permit_number': "MP-CWP/328/09/2024",
                'location': "Shabalala Ward 1",
                'client': mbombela,
                'consulting_engineer': mk_dube,
                'principal_contractor': gabby
            }
        )

        if created:
            self.stdout.write(f'Created project: {project.title}')

        # Create main audit
        audit, created = Audit.objects.get_or_create(
            report_number="CHS-LSC-2025/06",
            defaults={
                'project': project,
                'audit_date': timezone.datetime(2025, 7, 17).date(),
                'audit_type': 'OHS',
                'audit_number': '001',
                'performed_by': 'LETHU SAFETY CONSULTANTS (PTY) LTD',
                'report_number': 'CHS-LSC-2025/06',
                'overall_score_percentage': 84.00,
                'standard_required': 75.00,
                'improvement_notices': 1,
                'contravention_notices': 0,
                'prohibition_notices': 0
            }
        )

        if created:
            self.stdout.write(f'Created audit: {audit.report_number}')

        # Create sample legal appointments
        legal_appointments = [
            {
                'appointment_type': 'CEO_16_1',
                'appointed_person': 'PRECIOUS MORGAN',
                'actual_score': 2
            },
            {
                'appointment_type': 'CEO_16_2',
                'appointed_person': 'EUGENE NDLOVU',
                'actual_score': 2
            },
            {
                'appointment_type': 'CONSTR_MGR_8_1',
                'appointed_person': 'THULANI KHUMALO',
                'actual_score': 2
            },
            {
                'appointment_type': 'CHS_OFFICER_8_5',
                'appointed_person': 'CHOEU SERAME',
                'actual_score': 2
            },
            {
                'appointment_type': 'ELECT_INSP',
                'appointed_person': '',
                'actual_score': 0,
                'comments': 'NONE COMPLIANCE.'
            }
        ]

        for appt_data in legal_appointments:
            LegalAppointment.objects.get_or_create(
                audit=audit,
                appointment_type=appt_data['appointment_type'],
                defaults={
                    'required_score': 2,
                    'actual_score': appt_data['actual_score'],
                    'appointed_person': appt_data['appointed_person'],
                    'comments': appt_data.get('comments', '')
                }
            )

        # Create risk ratings
        risk_ratings = [
            ('CRITICAL', 'Immediate'),
            ('HIGH', 'Within 24 hours'),
            ('MEDIUM', 'Within 3 days'),
            ('LOW', 'Within 7 days'),
        ]

        for level, time_frame in risk_ratings:
            RiskRating.objects.get_or_create(
                level=level,
                defaults={'time_frame': time_frame}
            )

        # Create action items
        action_items = [
            {
                'description': 'To ensure that all management and supervision personnel are appointed in writing and their competency certificates are attached to those appointments and accepted by appointees',
                'regulation_reference': 'CR 8(5)',
                'assigned_to': 'Principal Contractor'
            },
            {
                'description': 'Ensure that a breathalyser is readily available on site. Random alcohol testing and records kept on site. Drug and Alcohol policy to be communicated regularly',
                'regulation_reference': 'GSR.2(a)',
                'assigned_to': 'Principal Contractor'
            },
            {
                'description': 'Ensure Traffic Accommodation Layout Plan is displayed clearly and updated regularly as project progress',
                'regulation_reference': '',
                'assigned_to': 'Principal Contractor'
            }
        ]

        for item_data in action_items:
            ActionItem.objects.get_or_create(
                audit=audit,
                description=item_data['description'],
                defaults={
                    'regulation_reference': item_data['regulation_reference'],
                    'assigned_to': item_data['assigned_to']
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample audit data!'))
