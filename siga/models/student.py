from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Student(models.Model):
    _name = 'siga.student'
    _description = 'Student'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    registration_number = fields.Char(string='Registration Number', readonly=True, tracking=True, copy=False, default=lambda self: _('New'))
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Usuario del Portal', help='Usuario asociado al estudiante')

    # Personal Information
    birth_date = fields.Date(string='Birth Date')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', required=True, tracking=True)
    
    # Contact Information
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone')
    address = fields.Text(string='Address')
    partner_id = fields.Many2one('res.partner', string='Contact', required=True, tracking=True)
    
    # Academic Information
    grade_level = fields.Many2one('siga.grade.level', string='Grade Level', required=True, tracking=True)
    group_id = fields.Many2one('siga.student.group', string='Group', required=True, tracking=True,
                             domain="[('grade_level_id', '=', grade_level)]")
    section = fields.Char(string='Section')
    admission_date = fields.Date(string='Admission Date', default=fields.Date.context_today)
    
    # Parent/Guardian Information
    parent_ids = fields.Many2many('res.partner',
                                'siga_student_parent_rel',
                                'student_id',
                                'parent_id',
                                string='Parents/Guardians',
                                domain=[('is_parent', '=', True)])
    
    # Academic Records
    course_ids = fields.Many2many('siga.course', 
                                'siga_student_course_rel',
                                'student_id',
                                'course_id',
                                string='Enrolled Courses')
    grade_ids = fields.One2many('siga.grade', 'student_id', string='Grades')
    attendance_ids = fields.One2many('siga.attendance', 'student_id', string='Attendances')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('alumni', 'Alumni'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    _sql_constraints = [
        ('unique_registration_number', 'unique(registration_number)',
         'The registration number must be unique!')
    ]

    def _compute_access_url(self):
        super()._compute_access_url()
        for student in self:
            student.access_url = f'/my/student/{student.id}'

    @api.model_create_multi
    def create(self, vals_list):
        students = super().create(vals_list)
        
        for student in students:
            # Asignar un número de registro si no se proporciona
            if not student.registration_number or student.registration_number in ['Nuevo']:
                student.registration_number = self.env['ir.sequence'].next_by_code('siga.student') or _('New')

            # Asignar un usuario de portal por defecto
        if not student.user_id:
            user = self.env['res.users'].sudo().create({
                'name': student.name,
                'login': student.registration_number,
                'email': student.partner_id.email,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],  # Asignar al grupo de portal
                'partner_id': student.partner_id.id
            })
            student.user_id = user.id  # Asignar el ID del nuevo usuario al estudiante

            # Invitar al portal
            student.action_invite_to_portal()
        
        return students


    def action_invite_to_portal(self):
        """Enviar invitación al portal al estudiante y sus padres"""
        self.ensure_one()
        # Obtener plantillas
        student_template_id = int(self.env['ir.config_parameter'].sudo().get_param('siga.portal_student_template_id', '0'))
        parent_template_id = int(self.env['ir.config_parameter'].sudo().get_param('siga.portal_parent_template_id', '0'))

        # Invitar al estudiante
        if student_template_id and self.partner_id.email:
            self.partner_id.with_context(portal_template_id=student_template_id).action_send_portal_invite()

        # Invitar a los padres
        if parent_template_id:
            for parent in self.parent_ids.filtered(lambda p: p.email):
                parent.with_context(portal_template_id=parent_template_id).action_send_portal_invite()

        return True

    @api.constrains('birth_date')
    def _check_birth_date(self):
        for record in self:
            if record.birth_date and record.birth_date > fields.Date.today():
                raise ValidationError("Birth date cannot be in the future!")

    def name_get(self):
        result = []
        for record in self:
            name = f'[{record.registration_number}] {record.name}'
            result.append((record.id, name))
        return result

    def action_enroll(self):
        """Matricular estudiante"""
        return self.write({'state': 'enrolled'})

    def action_graduate(self):
        """Graduar estudiante"""
        return self.write({'state': 'alumni'})

    def action_cancel(self):
        """Cancelar matrícula"""
        return self.write({'state': 'cancelled'})

    def action_draft(self):
        """Volver a borrador"""
        return self.write({'state': 'draft'})
