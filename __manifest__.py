# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Appraisal',
    'version': '15.0',
    'category': 'Human Resources/Appraisal',
    'sequence': 10,
    'summary': 'Appraisal Management',
    'website': 'https://www.odoo.com/app/appraisals',
    'description': 'Module to manage employee appraisals',
    'depends': ['base','hr','mail','calendar', 'hr_skills', 'survey'],
    'data': [
        'security/ir.model.access.csv',
        "security/hr_appraisal_security.xml",
        'data/data.xml',
        "data/mail_template_data.xml",
        'data/hr_appraisal_survey_data.xml',
        'views/appraisal_menu.xml',
        'views/appraisal_views.xml',
        'views/appraisal_note_views.xml',
        "views/res_config_settings.xml",
        "views/appraisal_goal.xml",
        "views/hr_employee_views.xml",
        'views/hr_appraisal_goal_tag_views.xml',
        'views/hr_appraisal_skills_templates.xml',
        "views/hr_department_views.xml",
        "wizard/request_appraisal_views.xml",
        "wizard/appraisal_ask_feedback_views.xml",
        'report/appraisal_analysis_report_view.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'aspl_hr_appraisal/static/src/**/**',
        ],
        'web.assets_qweb': [
            'aspl_hr_appraisal/static/src/xml/**/*',
        ],
    },
    'auto_install': False,
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
