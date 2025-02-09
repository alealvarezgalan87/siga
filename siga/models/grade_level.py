from odoo import models, fields


class GradeLevel(models.Model):
    _name = 'siga.grade.level'
    _description = 'Grade Level'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    student_ids = fields.One2many('siga.student', 'grade_level', string='Students')
    course_ids = fields.One2many('siga.course', 'grade_level_id', string='Courses')

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'The grade level code must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f'[{record.code}] {record.name}'))
        return result
