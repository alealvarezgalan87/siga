from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, time


class ClassSchedule(models.Model):
    _name = 'siga.class.schedule'
    _description = 'Class Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    course_id = fields.Many2one('siga.course', string='Course', required=True, tracking=True)
    teacher_id = fields.Many2one('siga.teacher', string='Teacher', required=True, tracking=True)
    group_id = fields.Many2one('siga.student.group', string='Student Group', required=True, tracking=True)
    
    day_of_week = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    ], string='Day of Week', required=True, tracking=True)
    
    start_time = fields.Float(string='Start Time', required=True, tracking=True)
    end_time = fields.Float(string='End Time', required=True, tracking=True)
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    color = fields.Integer(string='Color Index')

    @api.depends('course_id', 'group_id', 'day_of_week', 'start_time', 'end_time')
    def _compute_name(self):
        for record in self:
            if record.course_id and record.group_id:
                start_time_str = self._float_to_time_str(record.start_time)
                end_time_str = self._float_to_time_str(record.end_time)
                record.name = f"{record.course_id.name} - {record.group_id.name} - {record.day_of_week.capitalize()} ({start_time_str}-{end_time_str})"
            else:
                record.name = False

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Calcular la duración en horas entre la hora de inicio y fin"""
        for record in self:
            if record.start_time and record.end_time:
                record.duration = record.end_time - record.start_time
            else:
                record.duration = 0.0

    @api.model
    def create(self, vals):
        return super(ClassSchedule, self).create(vals)

    def write(self, vals):
        return super(ClassSchedule, self).write(vals)

    def action_confirm(self):
        """Confirmar el horario"""
        for record in self:
            # Verificar si ya existe un horario similar
            existing = self.search([
                ('group_id', '=', record.group_id.id),
                ('day_of_week', '=', record.day_of_week),
                ('state', '=', 'confirmed'),
                ('id', '!=', record.id),  # Excluir el registro actual
                '|',
                '&',
                ('start_time', '<=', record.start_time),
                ('end_time', '>', record.start_time),
                '&',
                ('start_time', '<', record.end_time),
                ('end_time', '>=', record.end_time)
            ])
            
            if existing:
                raise ValidationError(_('¡Este horario ya existe para este grupo!'))
        
        return self.write({'state': 'confirmed'})

    def action_draft(self):
        """Volver a borrador"""
        return self.write({'state': 'draft'})

    def action_cancel(self):
        """Cancelar el horario"""
        return self.write({'state': 'cancelled'})

    @api.onchange('course_id')
    def _onchange_course_id(self):
        """Al cambiar el curso, limpia y filtra los grupos disponibles"""
        self.group_id = False
        if self.course_id:
            return {'domain': {'group_id': [('course_id', '=', self.course_id.id)]}}
        return {'domain': {'group_id': []}}

    @api.constrains('start_time', 'end_time')
    def _check_times(self):
        """Validar que la hora de inicio sea menor que la hora de fin"""
        for record in self:
            if record.start_time >= record.end_time:
                raise ValidationError(_('La hora de inicio debe ser menor que la hora de fin'))

    def _float_to_time_str(self, time_float):
        """Convertir float a string de tiempo (HH:MM)"""
        hours = int(time_float)
        minutes = int((time_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
