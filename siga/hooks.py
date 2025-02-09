from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Post-install script"""
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Configurar plantillas de correo por defecto
    student_template = env.ref('siga.email_template_student_portal_access', raise_if_not_found=False)
    parent_template = env.ref('siga.email_template_parent_portal_access', raise_if_not_found=False)

    if student_template:
        env['ir.config_parameter'].sudo().set_param('siga.portal_student_template_id', str(student_template.id))
    if parent_template:
        env['ir.config_parameter'].sudo().set_param('siga.portal_parent_template_id', str(parent_template.id))

    # Habilitar invitación automática al portal
    env['ir.config_parameter'].sudo().set_param('siga.auto_invite_portal', '1')
