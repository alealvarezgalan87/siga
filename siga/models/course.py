from odoo import models, fields, api


class Course(models.Model):
    _name = 'siga.course'
    _description = 'Course'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Course Name', required=True, tracking=True)
    code = fields.Char(string='Course Code', required=True, tracking=True)
    active = fields.Boolean(default=True)
    
    # Course Information
    description = fields.Text(string='Description')
    credits = fields.Integer(string='Credits')
    grade_level_id = fields.Many2one('siga.grade.level', string='Grade Level')
    
    # Relations
    teacher_id = fields.Many2one('siga.teacher', string='Teacher', tracking=True)
    student_ids = fields.Many2many('siga.student',
                                 'siga_student_course_rel',
                                 'course_id',
                                 'student_id',
                                 string='Enrolled Students')
    
    # Schedule
    schedule_ids = fields.One2many('siga.class.schedule', 'course_id', string='Class Schedule')
    
    # Academic Information
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    
    # Statistics
    total_students = fields.Integer(compute='_compute_statistics', string='Total Students')
    average_grade = fields.Float(compute='_compute_statistics', string='Average Grade')

    _sql_constraints = [
        ('unique_course_code', 'unique(code)',
         'The course code must be unique!')
    ]

    @api.depends('student_ids', 'student_ids.grade_ids')
    def _compute_statistics(self):
        for course in self:
            course.total_students = len(course.student_ids)
            grades = self.env['siga.grade'].search([
                ('course_id', '=', course.id),
                ('state', '=', 'published')
            ])
            if grades:
                course.average_grade = sum(grades.mapped('final_grade')) / len(grades)
            else:
                course.average_grade = 0.0

    def name_get(self):
        result = []
        for record in self:
            name = f'[{record.code}] {record.name}'
            result.append((record.id, name))
        return result
