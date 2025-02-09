from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Portal
    siga_portal_student_template_id = fields.Many2one(
        'mail.template',
        string='Plantilla de Correo para Estudiantes',
        domain=[('model', '=', 'siga.student')],
        config_parameter='siga.portal_student_template_id'
    )
    siga_portal_parent_template_id = fields.Many2one(
        'mail.template',
        string='Plantilla de Correo para Padres',
        domain=[('model', '=', 'res.partner')],
        config_parameter='siga.portal_parent_template_id'
    )
    siga_auto_invite_portal = fields.Boolean(
        string='Invitar Automáticamente al Portal',
        help='Si está marcado, se enviará automáticamente una invitación al portal cuando se cree un nuevo estudiante',
        config_parameter='siga.auto_invite_portal'
    )
