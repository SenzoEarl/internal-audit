from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

# ========== COMPANY & PROJECT MODELS ==========
class Client(models.Model):
    """Client organization commissioning the work"""
    name = models.CharField(max_length=200)
    # Editable contact details
    contact_name = models.CharField(max_length=200, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ConsultingFirm(models.Model):
    """Consulting/Engineering firm"""
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class PrincipalContractor(models.Model):
    """Main contractor responsible for the project"""
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    """Construction project being audited"""
    title = models.CharField(max_length=500)
    permit_number = models.CharField(max_length=100)
    location = models.CharField(max_length=500)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    consulting_engineer = models.ForeignKey(ConsultingFirm, on_delete=models.CASCADE)
    principal_contractor = models.ForeignKey(PrincipalContractor, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} - {self.permit_number}"


# ========== AUDIT & COMPLIANCE MODELS ==========
class Audit(models.Model):
    """Main audit record"""
    AUDIT_TYPES = [
        ('OHS', 'Occupational Health & Safety Audit'),
        ('ENV', 'Environmental Audit'),
        ('QUAL', 'Quality Audit'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    audit_date = models.DateField()
    audit_type = models.CharField(max_length=10, choices=AUDIT_TYPES, default='OHS')
    audit_number = models.CharField(max_length=50)  # e.g., "001"
    performed_by = models.CharField(max_length=200)  # e.g., "LETHU SAFETY CONSULTANTS (PTY) LTD"
    report_number = models.CharField(max_length=100)  # e.g., "CHS-LSC-2025/06"
    overall_score_percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                                   validators=[MinValueValidator(0), MaxValueValidator(100)])
    standard_required = models.DecimalField(max_digits=5, decimal_places=2, default=75.00,
                                            validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Notices issued during audit
    improvement_notices = models.IntegerField(default=0)
    contravention_notices = models.IntegerField(default=0)
    prohibition_notices = models.IntegerField(default=0)

    def __str__(self):
        return f"Audit {self.audit_number} - {self.audit_date} - {self.project}"


class LegalAppointment(models.Model):
    """Legal appointments as per regulations"""
    APPOINTMENT_TYPES = [
        ('CEO_16_1', 'Chief Executive Officer Sec 16.1'),
        ('CEO_16_2', 'Assistant CEO Sec 16.2'),
        ('CONSTR_MGR_8_1', 'Construction Manager CR 8.1'),
        ('HCA', 'HCA (Reg 2020)'),
        ('CONSTR_SUP_8_7', 'Construction Supervisor CR 8.7'),
        ('ELEC_INSP', 'Electrical Equipment Inspector Controller'),
        ('CHS_OFFICER_8_5', 'Construction Health and Safety Officer CR 8.5'),
        ('FIRE_INSP_29H', 'Fire Equipment Inspector CR 29(h)'),
        ('ENV_OFFICER', 'Environmental Officer'),
        ('EMERGENCY_COORD', 'Emergency Coordinator'),
        ('HS_REP_17_1', 'Health and Safety Representative Sec 17.1'),
        ('EXCAVATION_SUP_13_1', 'Excavation Supervisor CR 13(1)'),
        ('RISK_ASSESSOR_9_1', 'Risk Assessor CR 9.(1)'),
        ('PPE_INSP', 'PPE Inspector'),
        ('FIRST_AIDER', 'First Aider'),
        ('HAND_TOOLS_INSP', 'Hand Tools Inspector Sec 8.2i'),
        ('STACKING_STORAGE', 'Stacking and Storage Supervisor CR 28(a)'),
        ('HS_COMMITTEE', 'Health and Safety Committee Member'),
        ('HYGIENE_INSP', 'Hygiene and Facility Inspector'),
        ('INCIDENT_INVEST', 'Incident Investigator CR 29(h)'),
        ('PORTABLE_ELEC_INSP', 'Portable Elec. Tools Inspector EMR 10'),
        ('HOUSEKEEPING', 'Housekeeping CR 27'),
        ('VEHICLE_INSP', 'CR 23 Construction Vehicle and Mobile Plant Inspector'),
        ('TRAFFIC_SAFETY', 'Traffic Safety Officer'),
        ('HS_CHAIRPERSON', 'Chairperson Health and Safety Committee Sec 19'),
        ('VEHICLE_OPERATOR', 'CR 23 Construction vehicle and Mobile Plant operator'),
    ]

    COMPLIANCE_STATUS = [
        (0, 'Non-Compliant'),
        (1, 'Partial Compliance'),
        (2, 'Fully Compliant'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='legal_appointments')
    appointment_type = models.CharField(max_length=50, choices=APPOINTMENT_TYPES)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=COMPLIANCE_STATUS)
    appointed_person = models.CharField(max_length=200, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'appointment_type']

    def __str__(self):
        return f"{self.get_appointment_type_display()} - Score: {self.actual_score}/2"


class OHSDocumentation(models.Model):
    """OHS Documentation compliance"""
    DOCUMENT_TYPES = [
        ('SHE_FILE', 'SHE File on site'),
        ('CLIENT_SPECS', 'Clients Safety Specifications CR 9'),
        ('RISK_ASSESSMENT', 'Baseline Risk Assessment'),
        ('CONSTRUCTION_NOTICE', 'Notification of Construction'),
        ('COIDA', 'COIDA Letter of good standing'),
        ('INCIDENT_REGISTERS', 'Incident Registers'),
        ('WCL_FORMS', 'WCL1 – WCL6 Forms'),
        ('ACT_DISPLAY', 'Copy of Act display on site'),
        ('CONTRACTOR_APPOINTMENT', 'Contractors Appointment CR.5(1)(K)'),
        ('MANDATORY_AGREEMENTS', 'Signed Mandatory Agreements'),
        ('POLICIES', 'Polices to be updated'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='ohs_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'document_type']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.actual_score}/2"


class TrainingCommunication(models.Model):
    """Training and Communication compliance"""
    TRAINING_TYPES = [
        ('INDUCTION_MANUAL', 'Health and Safety Induction Manual'),
        ('SAFETY_TALKS', 'Health and Safety Talks'),
        ('DAILY_RISK_ASSESS', 'Daily Task Risk Assessments'),
        ('TRAFFIC_MEETINGS', 'Daily Traffic Accommodation Meetings'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='training_items')
    item_type = models.CharField(max_length=50, choices=TRAINING_TYPES)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


class InspectionRegister(models.Model):
    """Inspection registers compliance"""
    REGISTER_TYPES = [
        ('HS_REP_CHECKLIST', 'Health and Safety Rep Inspection Checklist'),
        ('FIRST_AID_BOX', 'First Aid Box Inspection Registers'),
        ('FIRE_EQUIPMENT', 'Fire Extinguishing Equipment Register'),
        ('FACILITIES_HYGIENE', 'Facilities/hygiene Inspection Register'),
        ('STACKING_STORAGE', 'Stacking & Storage Register'),
        ('HAND_TOOL', 'Hand Tool Register'),
        ('MOBILE_PLANT', 'Mobile Plant Checklists'),
        ('PPE_REGISTER', 'PPE Registers'),
        ('INCIDENT_REGISTER', 'Incident Registers'),
        ('EXCAVATION', 'Excavation Inspection Register'),
        ('HOUSEKEEPING', 'Housekeeping Checklist'),
        ('VEHICLE_PRE_START', 'Construction Vehicle Pre-Start Checklist'),
        ('SIGNAGE', 'Signage Checklist'),
        ('HYGIENE', 'Hygiene Checklist'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='inspection_registers')
    register_type = models.CharField(max_length=50, choices=REGISTER_TYPES)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'register_type']

    def __str__(self):
        return f"{self.get_register_type_display()} - {self.actual_score}/2"


class PublicSafetySecurity(models.Model):
    """Public Safety and Security compliance"""
    SECURITY_ITEMS = [
        ('ACCESS_CONTROL', 'Access Control Register'),
        ('GUARDHOUSE', 'Guardhouse On site'),
        ('SECURITY_PERSONNEL', 'Security Personnel on site'),
        ('PSIRA_REGISTRATION', 'PSIRA Registered security appointment'),
        ('SECURITY_RISK_ASSESS', 'Security Risk Assessment'),
        ('FIRE_EXTINGUISHER', 'Fire Extinguisher'),
        ('SECURITY_LETTER', 'Letter of Good Standing (Security)'),
        ('SECURITY_MEDICAL', 'Medical certificate (Security)'),
        ('SECURITY_AGREEMENT', 'Mandatory Agreement (Security)'),
        ('SECURITY_APPOINTMENT', 'Appointment Letter (Security)'),
        ('PSIRA_REG', 'PSIRA Registration'),
        ('SECURITY_PPE', 'PPE (Security)'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='security_items')
    item_type = models.CharField(max_length=50, choices=SECURITY_ITEMS)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


class EmployeeProtection(models.Model):
    """Employee Protection and Welfare compliance"""
    PROTECTION_ITEMS = [
        ('PPE_ISSUED', 'PPE Issued and being worn (free of charge)'),
        ('AWARENESS', 'Employees are aware of their OHS duties'),
        ('PROCEDURES', 'Procedure for addressing OHS concerns'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='protection_items')
    item_type = models.CharField(max_length=50, choices=PROTECTION_ITEMS)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


class FirePrevention(models.Model):
    """Fire Prevention and Emergencies compliance"""
    FIRE_ITEMS = [
        ('EQUIPMENT_AVAILABLE', 'Suitable fire extinguishing equipment available'),
        ('FIRE_FIGHTER_APPOINT', 'Fire fighter Appointment'),
        ('AWARENESS', 'Employees aware of emergency procedures'),
        ('COMPETENCIES', 'Fire Fighter Competencies'),
        ('EVACUATION_PLAN', 'Fire emergency evacuation layout plan visible'),
        ('EVACUATION_DRILL', 'Fire emergency evacuation drill conducted'),
        ('EMERGENCY_CONTACTS', 'Emergency Contact numbers in place'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='fire_prevention_items')
    item_type = models.CharField(max_length=50, choices=FIRE_ITEMS)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


class OccupationalHealth(models.Model):
    """Occupational Health compliance"""
    HEALTH_ITEMS = [
        ('ENTRY_MEDICAL_EXAM', 'Entry Medical Examinations'),
        ('MEDICAL_COPIES', 'Copies of medical examinations on file'),
        ('ID_COPIES', 'ID copies on site'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='occupational_health_items')
    item_type = models.CharField(max_length=50, choices=HEALTH_ITEMS)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


class IncidentManagement(models.Model):
    """Incident Management compliance"""
    INCIDENT_ITEMS = [
        ('PROCEDURE', 'Incident Management Procedure'),
        ('ANNEXURE', 'Annexure.1'),
        ('WCL_FORMS', 'WCL1 - WCL6 forms available'),
        ('DISCIPLINARY_PROC', 'Disciplinary Procedure in place'),
        ('NEAR_MISS', 'Near – miss records'),
        ('FIRST_AID_RECORDS', 'First Aid Injury Records'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='incident_items')
    item_type = models.CharField(max_length=50, choices=INCIDENT_ITEMS)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


class IntoxicationManagement(models.Model):
    """Intoxication Management compliance"""
    INTOXICATION_ITEMS = [
        ('RANDOM_TESTING', 'Random Alcohol testing'),
        ('DISCIPLINARY_PROC', 'Disciplinary Procedure in place'),
        ('ALCOHOL_DRUGS_POLICY', 'Alcohol and Drugs Policy'),
        ('BREATHALYSER', 'Breathalyser'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='intoxication_items')
    item_type = models.CharField(max_length=50, choices=INTOXICATION_ITEMS)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


class TrafficAccommodation(models.Model):
    """Traffic Accommodation compliance"""
    TRAFFIC_ITEMS = [
        ('FLAG_PEOPLE_TRAINED', 'Flag people trained for this job'),
        ('SIGNS_UPDATED', 'Signs updated before start and end of shift'),
        ('UPDATE_REGISTER', 'Register for update records'),
        ('ROAD_CLEAN', 'Existing road is clean and free from danger'),
        ('DEVIATION_DAMPED', 'Deviations damped with water to minimize dust'),
        ('DEVIATION_BLADED', 'Deviation bladed if required'),
        ('CHILDREN_PROTECTION', 'Children free from being injured'),
        ('VEHICLES_CONDITION', 'Construction vehicles in good conditions'),
        ('SAFETY_FEATURES', 'Safety features on construction vehicles'),
        ('OPENINGS_BARRICADED', 'All openings are barricaded'),
        ('FLAG_POSITIONS', 'Flag people always in required positions'),
        ('SIGNS_PLACEMENT', 'Signs placed according to specifications'),
        ('SIGNS_REGISTER', 'Signs register updated daily'),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='traffic_items')
    item_type = models.CharField(max_length=50, choices=TRAFFIC_ITEMS)
    required_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)], default=2)
    actual_score = models.IntegerField(choices=[(0, 0), (1, 1), (2, 2)])
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['audit', 'item_type']

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.actual_score}/2"


# ========== ACTION ITEMS & FOLLOW-UP ==========
class RiskRating(models.Model):
    """Standard risk rating timeframes"""
    RISK_LEVELS = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    level = models.CharField(max_length=20, choices=RISK_LEVELS, unique=True)
    time_frame = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.level}: {self.time_frame}"


class ActionItem(models.Model):
    """Corrective action items identified during audit"""
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='action_items')
    description = models.TextField()
    regulation_reference = models.CharField(max_length=100, blank=True, null=True)  # e.g., "CR 8(5)"
    assigned_to = models.CharField(max_length=200)  # e.g., "Principal Contractor"
    risk_rating = models.ForeignKey(RiskRating, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Action Item: {self.description[:50]}..."


class SitePersonnel(models.Model):
    """Site personnel count"""
    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name='personnel')
    total_personnel = models.IntegerField(default=0)
    management_count = models.IntegerField(default=0, blank=True, null=True)
    worker_count = models.IntegerField(default=0, blank=True, null=True)
    subcontractor_count = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return f"Personnel for {self.audit}: {self.total_personnel} total"


class VisualObservation(models.Model):
    """Visual observations/photo reports"""
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='visual_observations')
    description = models.TextField()
    observation_type = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Housekeeping", "Excavation"
    photo_reference = models.CharField(max_length=200, blank=True, null=True)  # File path or reference to photo
    date_recorded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Observation: {self.description[:50]}..."