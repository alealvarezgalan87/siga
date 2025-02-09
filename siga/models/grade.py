from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Grade(models.Model):
    _name = 'siga.grade'
    _description = 'Student Grade'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    student_id = fields.Many2one('siga.student', string='Student', required=True, tracking=True)
    course_id = fields.Many2one('siga.course', string='Course', required=True, tracking=True)
    academic_year = fields.Char(string='Academic Year', required=True, tracking=True)
    term = fields.Selection([
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
        ('fourth', 'Fourth Term')
    ], string='Term', required=True, tracking=True)
    
    # Grades
    midterm_grade = fields.Float(string='Midterm Grade', tracking=True)
    final_exam = fields.Float(string='Final Exam', tracking=True)
    final_grade = fields.Float(string='Final Grade', compute='_compute_final_grade', store=True)
    
    # Additional Information
    comments = fields.Text(string='Comments')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('published', 'Published')
    ], string='Status', default='draft', tracking=True)
    
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('student_id', 'course_id', 'academic_year', 'term')
    def _compute_display_name(self):
        for record in self:
            if record.student_id and record.course_id:
                record.display_name = f'{record.student_id.name} - {record.course_id.name} ({record.academic_year}, {record.term})'
            else:
                record.display_name = 'New Grade'

    @api.depends('midterm_grade', 'final_exam')
    def _compute_final_grade(self):
        for record in self:
            record.final_grade = (record.midterm_grade * 0.4) + (record.final_exam * 0.6)

    @api.constrains('midterm_grade', 'final_exam')
    def _check_grades(self):
        for record in self:
            if record.midterm_grade and (record.midterm_grade < 0 or record.midterm_grade > 100):
                raise ValidationError('Midterm grade must be between 0 and 100')
            if record.final_exam and (record.final_exam < 0 or record.final_exam > 100):
                raise ValidationError('Final exam grade must be between 0 and 100')

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_publish(self):
        self.write({'state': 'published'})

    def action_draft(self):
        self.write({'state': 'draft'})
