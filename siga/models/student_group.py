from odoo import models, fields, api


class StudentGroup(models.Model):
    _name = 'siga.student.group'
    _description = 'Student Group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Group Name', required=True, tracking=True)
    code = fields.Char(string='Group Code', required=True, tracking=True)
    active = fields.Boolean(default=True)
    
    # Academic Information
    grade_level_id = fields.Many2one('siga.grade.level', string='Grade Level', required=True, tracking=True)
    academic_year = fields.Char(string='Academic Year', required=True, tracking=True)
    
    # Relations
    student_ids = fields.One2many('siga.student', 'group_id', string='Students')
    schedule_ids = fields.One2many('siga.class.schedule', 'group_id', string='Class Schedule')
    
    # Statistics
    student_count = fields.Integer(string='Number of Students', compute='_compute_counts')
    schedule_count = fields.Integer(string='Number of Classes', compute='_compute_counts')
    
    _sql_constraints = [
        ('unique_code_year', 'unique(code, academic_year)',
         'The combination of group code and academic year must be unique!')
    ]
    
    @api.depends('student_ids', 'schedule_ids')
    def _compute_counts(self):
        for record in self:
            record.student_count = len(record.student_ids)
            record.schedule_count = len(record.schedule_ids)
    
    def name_get(self):
        result = []
        for record in self:
            name = f'[{record.code}] {record.name} ({record.academic_year})'
            result.append((record.id, name))
        return result
