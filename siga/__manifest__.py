{
    'name': 'Sistema Integrado de Gestión Académica',
    'version': '15.0.1.0.0',
    'summary': 'Sistema integral para la gestión académica',
    'description': '''
        Sistema Integrado de Gestión Académica (SIGA) para instituciones educativas.
        Características principales:
        - Gestión de estudiantes
        - Gestión de profesores
        - Portal para padres
        - Administración académica
        - Reportes y estadísticas
    ''',
    'category': 'Education',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
        'portal',
        'calendar',
        'hr',
        'website',
    ],
    'data': [
        # Datos de Seguridad
        'security/siga_security.xml',
        'security/ir.model.access.csv',
        
        # Datos de Secuencia y Configuración
        'data/sequence_data.xml',
        'data/grade_level_data.xml',
        
        # Vistas de Modelos Base
        'views/res_partner_views.xml',
        'views/student_views.xml',
        'views/teacher_views.xml',
        'views/course_views.xml',
        'views/grade_views.xml',
        'views/attendance_views.xml',
        'views/schedule_views.xml',
        'views/grade_level_views.xml',
        'views/student_group_views.xml',
        'views/menu_views.xml',
        
        # Portal Web y Configuración
        'views/portal_templates.xml',
        'views/res_config_settings_views.xml',
        
        # Datos de Inicialización (debe ir al final)
        'data/init_data.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'assets': {
        'web.assets_frontend': [
            '/siga/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    
    # Configuración de idiomas
    'i18n_languages': ['es'],
}
