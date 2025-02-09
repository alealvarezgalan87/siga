from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers import portal
from odoo.osv.expression import OR

import logging
_logger = logging.getLogger(__name__)


class SigaPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        Student = request.env['siga.student']
        if 'student_count' in counters:
            domain = self._get_students_domain(partner)
            student_count = Student.search_count(domain) if Student.check_access_rights('read', raise_exception=False) else 0
            values['student_count'] = student_count
            _logger.info(f"Student count: {student_count}")  # Agregado para depuración

        return values

    def _get_students_domain(self, partner):
        return OR([
            [('user_id.partner_id', '=', partner.id)],  # Estudiante
            [('parent_ids', 'in', [partner.id])]  # Padre/Tutor
        ])

    @http.route(['/my/students', '/my/students/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_students(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Student = request.env['siga.student']

        domain = self._get_students_domain(partner)

        searchbar_sortings = {
            'name': {'label': _('Nombre'), 'order': 'name'},
            'registration_number': {'label': _('Matrícula'), 'order': 'registration_number'},
            'grade': {'label': _('Grado'), 'order': 'grade_level_id'},
        }

        # default sortby order
        if not sortby:
            sortby = 'name'
        sort_order = searchbar_sortings[sortby]['order']

        # count for pager
        student_count = Student.search_count(domain)

        # make pager
        pager = portal_pager(
            url="/my/students",
            url_args={'sortby': sortby},
            total=student_count,
            page=page,
            step=self._items_per_page
        )

        # search the count to display, according to the pager data
        students = Student.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'students': students,
            'page_name': 'students',
            'pager': pager,
            'default_url': '/my/students',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("siga.portal_my_students", values)

    @http.route(['/my/student/<int:student_id>'], type='http', auth="user", website=True)
    def portal_student_page(self, student_id, **kw):
        try:
            student_sudo = self._document_check_access('siga.student', student_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        terms_display = {}
        for grade in student_sudo.grade_ids:
            term_display = dict(request.env['siga.grade'].fields_get()['term']['selection']).get(grade.term)
            terms_display[grade.id] = term_display

        attendance_states_display = {}
        for attendance in student_sudo.attendance_ids:
            state_display = dict(request.env['siga.attendance'].fields_get()['state']['selection']).get(attendance.state)
            attendance_states_display[attendance.id] = state_display

        values = {
            'page_name': 'student',
            'student': student_sudo,
            'attendances': student_sudo.attendance_ids[:10],  # últimas 10 asistencias
            'grades': student_sudo.grade_ids,
            'terms_display': terms_display,  # Diccionario con términos legibles por ID de grado
            'attendance_states_display': attendance_states_display, # Diccionario con estados legibles por ID de asistencia
        }
        return request.render("siga.portal_student_page", values)

    # @http.route(['/','/my', '/my/home'], type='http', auth="user", website=True)
    # def home(self, **kw):
    #     values = self._prepare_portal_layout_values()
    #     return request.render("portal.portal_my_home", values)
