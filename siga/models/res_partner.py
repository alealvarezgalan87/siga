from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_parent = fields.Boolean(string='Is Parent/Guardian', default=False,
                             help="Check this box if this contact is a parent or guardian of a student")
    student_ids = fields.Many2many('siga.student',
                                 'siga_student_parent_rel',
                                 'parent_id',
                                 'student_id',
                                 string='Related Students')
