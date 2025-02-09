from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time, timedelta
import pytz


class Attendance(models.Model):
    _name = 'siga.attendance'
    _description = 'Student Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    student_id = fields.Many2one('siga.student', string='Student', required=True, tracking=True)
    schedule_id = fields.Many2one(
        'siga.class.schedule',
        string='Class Schedule',
        required=True,
        domain="[('state', '=', 'confirmed'), ('group_id', '=', student_group_id)]",
        tracking=True
    )
    course_id = fields.Many2one('siga.course', string='Course', related='schedule_id.course_id', store=True)
    group_id = fields.Many2one('siga.student.group', string='Group', related='schedule_id.group_id', store=True)
    student_group_id = fields.Many2one('siga.student.group', related='student_id.group_id', store=True)
    
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today, tracking=True)
    day_of_week = fields.Selection(related='schedule_id.day_of_week', string='Day of Week', store=True)
    
    state = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ], string='Status', required=True, default='present', tracking=True)
    
    remarks = fields.Text(string='Remarks')
    
    # Time Information
    check_in = fields.Datetime(string='Check In Time', tracking=True)
    check_out = fields.Datetime(string='Check Out Time', tracking=True)
    expected_start = fields.Float(related='schedule_id.start_time', string='Expected Start Time')
    expected_end = fields.Float(related='schedule_id.end_time', string='Expected End Time')
    
    # Computed Fields
    attendance_percentage = fields.Float(
        compute='_compute_attendance_percentage', 
        string='Attendance Percentage',
        digits=(5, 2),  # 5 dígitos en total, 2 decimales
        help="Porcentaje de asistencia del estudiante en este curso"
    )
    minutes_late = fields.Integer(compute='_compute_minutes_late', string='Minutes Late', store=True)
    minutes_early = fields.Integer(compute='_compute_minutes_early', string='Minutes Early', store=True)

    _sql_constraints = [
        ('unique_student_schedule_date', 'unique(student_id, schedule_id, date)',
         'Attendance record already exists for this student in this schedule on this date!')
    ]

    @api.onchange('schedule_id', 'date')
    def _onchange_schedule_date(self):
        """Actualiza los tiempos de check-in y check-out basados en el horario"""
        if self.schedule_id and self.date:
            # Convertir las horas float a datetime
            start_hour = int(self.schedule_id.start_time)
            start_minutes = int((self.schedule_id.start_time % 1) * 60)
            end_hour = int(self.schedule_id.end_time)
            end_minutes = int((self.schedule_id.end_time % 1) * 60)
            
            # Crear datetime combinando la fecha con las horas del horario
            user_tz = self.env.user.tz or 'UTC'
            local = pytz.timezone(user_tz)
            
            # Crear datetime en la zona horaria local
            check_in_local = datetime.combine(
                self.date,
                time(hour=start_hour, minute=start_minutes)
            )
            check_out_local = datetime.combine(
                self.date,
                time(hour=end_hour, minute=end_minutes)
            )
            
            # Convertir a UTC para almacenar
            check_in_utc = local.localize(check_in_local).astimezone(pytz.UTC)
            check_out_utc = local.localize(check_out_local).astimezone(pytz.UTC)
            
            self.check_in = check_in_utc.replace(tzinfo=None)
            self.check_out = check_out_utc.replace(tzinfo=None)

    @api.constrains('check_in', 'check_out')
    def _check_times(self):
        """Validar que check-out sea después de check-in"""
        for record in self:
            if record.check_in and record.check_out and record.check_out < record.check_in:
                raise ValidationError('La hora de salida no puede ser anterior a la hora de entrada')

    @api.constrains('student_id', 'schedule_id', 'date')
    def _check_student_schedule(self):
        # Mapeo de días en español a inglés
        day_mapping = {
            'lunes': 'monday',
            'martes': 'tuesday',
            'miércoles': 'wednesday',
            'miercoles': 'wednesday',
            'jueves': 'thursday',
            'viernes': 'friday',
            'sábado': 'saturday',
            'sabado': 'saturday',
            'domingo': 'sunday',
            'monday': 'monday',
            'tuesday': 'tuesday',
            'wednesday': 'wednesday',
            'thursday': 'thursday',
            'friday': 'friday',
            'saturday': 'saturday',
            'sunday': 'sunday'
        }

        for record in self:
            if record.student_id.group_id != record.schedule_id.group_id:
                raise ValidationError(
                    f"El estudiante {record.student_id.name} no pertenece al grupo "
                    f"{record.schedule_id.group_id.name} de este horario."
                )
            
            # Verificar que el día de la semana coincida
            attendance_day = record.date.strftime('%A').lower()
            # Convertir el día al formato esperado usando el mapeo
            normalized_day = day_mapping.get(attendance_day, attendance_day)
            if normalized_day != record.schedule_id.day_of_week:
                # Obtener el nombre del día en el idioma actual para el mensaje
                day_names = dict(record.schedule_id._fields['day_of_week'].selection)
                schedule_day_name = day_names.get(record.schedule_id.day_of_week, record.schedule_id.day_of_week)
                raise ValidationError(
                    f"La fecha {record.date} es {attendance_day.capitalize()}, "
                    f"pero el horario está programado para {schedule_day_name}"
                )

    @api.onchange('check_in', 'check_out', 'expected_start', 'expected_end')
    def _onchange_times(self):
        """Recalcular minutos de retraso y estado cuando cambien los tiempos"""
        if not self.check_in:
            self.minutes_late = 0
            self.state = 'absent'
            return

        if not self.expected_start:
            return

        # Obtener zona horaria del usuario
        user_tz = self.env.user.tz or 'UTC'
        local = pytz.timezone(user_tz)
        utc = pytz.UTC
        
        # Convertir check_in a la zona horaria local
        check_in_utc = utc.localize(fields.Datetime.from_string(self.check_in))
        check_in_local = check_in_utc.astimezone(local)
        
        # Obtener la hora esperada en la zona horaria local
        expected_time = self._float_to_time(self.expected_start)
        expected_datetime = datetime.combine(check_in_local.date(), expected_time)
        expected_local = local.localize(expected_datetime)
        
        # Calcular minutos de retraso y establecer estado inicial
        if check_in_local > expected_local:
            td = check_in_local - expected_local
            self.minutes_late = int(td.total_seconds() / 60)
            self.state = 'late'
        else:
            self.minutes_late = 0
            self.state = 'present'

        # Verificar check_out si existe
        if self.check_out and self.expected_end:
            check_out_utc = utc.localize(fields.Datetime.from_string(self.check_out))
            check_out_local = check_out_utc.astimezone(local)
            
            expected_end_time = self._float_to_time(self.expected_end)
            expected_end_datetime = datetime.combine(check_out_local.date(), expected_end_time)
            expected_end_local = local.localize(expected_end_datetime)
            
            # Si salió antes de tiempo, marcar como ausente
            if check_out_local < expected_end_local:
                time_diff = expected_end_local - check_out_local
                self.minutes_early = int(time_diff.total_seconds() / 60)
                # Si salió más de 15 minutos antes, marcar como ausente
                if time_diff.total_seconds() / 60 > 15:
                    self.state = 'absent'
                    self._onchange_state()  # Trigger para actualizar otros campos si es necesario

    @api.onchange('state')
    def _onchange_state(self):
        """Manejar cambios cuando el estado cambia"""
        if self.state == 'absent':
            self.remarks = self.remarks or 'Salida anticipada'
        elif self.state == 'late':
            self.remarks = self.remarks or f'Llegó {self.minutes_late} minutos tarde'

    @api.depends('check_in', 'expected_start')
    def _compute_minutes_late(self):
        """Compute para mantener el valor calculado en la base de datos"""
        for record in self:
            if record.check_in and record.expected_start:
                # Obtener zona horaria del usuario
                user_tz = self.env.user.tz or 'UTC'
                local = pytz.timezone(user_tz)
                utc = pytz.UTC
                
                # Convertir check_in a la zona horaria local
                check_in_utc = utc.localize(fields.Datetime.from_string(record.check_in))
                check_in_local = check_in_utc.astimezone(local)
                
                # Obtener la hora esperada en la zona horaria local
                expected_time = self._float_to_time(record.expected_start)
                expected_datetime = datetime.combine(check_in_local.date(), expected_time)
                expected_local = local.localize(expected_datetime)
                
                if check_in_local > expected_local:
                    td = check_in_local - expected_local
                    record.minutes_late = int(td.total_seconds() / 60)
                else:
                    record.minutes_late = 0
            else:
                record.minutes_late = 0

    @api.depends('check_out', 'expected_end')
    def _compute_minutes_early(self):
        """Compute para mantener el valor calculado en la base de datos"""
        for record in self:
            if record.check_out and record.expected_end:
                # Obtener zona horaria del usuario
                user_tz = self.env.user.tz or 'UTC'
                local = pytz.timezone(user_tz)
                utc = pytz.UTC
                
                # Convertir check_out a la zona horaria local
                check_out_utc = utc.localize(fields.Datetime.from_string(record.check_out))
                check_out_local = check_out_utc.astimezone(local)
                
                # Obtener la hora esperada en la zona horaria local
                expected_time = self._float_to_time(record.expected_end)
                expected_datetime = datetime.combine(check_out_local.date(), expected_time)
                expected_local = local.localize(expected_datetime)
                
                if check_out_local < expected_local:
                    td = expected_local - check_out_local
                    record.minutes_early = int(td.total_seconds() / 60)
                else:
                    record.minutes_early = 0
            else:
                record.minutes_early = 0

    @api.onchange('check_in')
    def _onchange_check_in(self):
        """Actualizar el estado basado en el tiempo de llegada"""
        if self.check_in and self.expected_start:
            # Obtener zona horaria del usuario
            user_tz = self.env.user.tz or 'UTC'
            local = pytz.timezone(user_tz)
            utc = pytz.UTC
            
            # Convertir check_in a la zona horaria local
            check_in_utc = utc.localize(fields.Datetime.from_string(self.check_in))
            check_in_local = check_in_utc.astimezone(local)
            
            # Obtener la hora esperada en la zona horaria local
            expected_time = self._float_to_time(self.expected_start)
            expected_datetime = datetime.combine(check_in_local.date(), expected_time)
            expected_local = local.localize(expected_datetime)
            
            if check_in_local > expected_local:
                self.state = 'late'
            else:
                self.state = 'present'

    @api.depends('student_id', 'course_id', 'date', 'state')
    def _compute_attendance_percentage(self):
        for record in self:
            # Obtener todas las asistencias del estudiante para este curso
            domain = [
                ('student_id', '=', record.student_id.id),
                ('course_id', '=', record.course_id.id),
                ('date', '<=', record.date),  # Solo considerar hasta la fecha actual
            ]
            
            # Si es un registro existente, excluirlo del conteo total
            if not record._origin.id:
                total_classes = self.search_count(domain)
                if total_classes == 0:
                    # Si es la primera clase, el porcentaje depende del estado actual
                    record.attendance_percentage = 1.0 if record.state in ['present', 'late'] else 0.0
                    return
            else:
                total_classes = self.search_count(domain) - 1  # Excluir el registro actual
            
            # Contar clases donde estuvo presente o llegó tarde
            present_domain = domain + [('state', 'in', ['present', 'late'])]
            present_classes = self.search_count(present_domain)
            
            # Si es un registro existente y el estado actual es presente o tarde, sumarlo
            if record._origin.id and record.state in ['present', 'late']:
                present_classes -= 1  # Restar el registro actual del conteo
            
            # Calcular el porcentaje incluyendo la asistencia actual
            total = total_classes + 1  # Sumar 1 para incluir la asistencia actual
            present = present_classes + (1 if record.state in ['present', 'late'] else 0)
            
            record.attendance_percentage = present / float(total)

    @api.onchange('student_id')
    def _onchange_student(self):
        """Al cambiar el estudiante, limpiamos el horario"""
        self.schedule_id = False

    def _float_to_time(self, float_time):
        """Convierte un tiempo en formato float a time"""
        hours = int(float_time)
        minutes = int((float_time % 1) * 60)
        return time(hours, minutes)
