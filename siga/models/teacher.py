from odoo import models, fields, api


class Teacher(models.Model):
    _name = 'siga.teacher'
    _description = 'Teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Related Employee', required=True)
    active = fields.Boolean(default=True)
    
    # Contact Information
    email = fields.Char(related='employee_id.work_email', string='Email', readonly=True)
    phone = fields.Char(related='employee_id.work_phone', string='Phone', readonly=True)
    
    # Academic Information
    department = fields.Char(string='Department')
    specialization = fields.Char(string='Specialization')
    qualification = fields.Text(string='Qualifications')
    
    # Teaching Information
    course_ids = fields.One2many('siga.course', 'teacher_id', string='Courses')
    schedule_ids = fields.One2many('siga.class.schedule', 'teacher_id', string='Class Schedule')
    
    # Statistics
    total_students = fields.Integer(compute='_compute_statistics', string='Total Students')
    total_courses = fields.Integer(compute='_compute_statistics', string='Total Courses')

    @api.depends('course_ids', 'course_ids.student_ids')
    def _compute_statistics(self):
        for teacher in self:
            teacher.total_courses = len(teacher.course_ids)
            student_ids = teacher.course_ids.mapped('student_ids')
            teacher.total_students = len(set(student_ids.ids))

    def name_get(self):
        result = []
        for record in self:
            name = f'{record.name} ({record.department})'
            result.append((record.id, name))
        return result
