# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

# from odoo.addons.hr_appraisal.models.hr_appraisal import HrAppraisal

COLORS_BY_STATE = {
    'new': 0,
    'cancel': 1,
    'pending': 2,
    'done': 3,
}

class AppraisalAnalysisReport(models.Model):
    _name = "appraisal.analysis.report"
    _description = "Appraisal Statistics"
    _order = 'create_date desc'
    _auto = False

    name = fields.Char(related='employee_id.name')
    create_date = fields.Date(string='Create Date', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    deadline = fields.Date(string="Deadline", readonly=True)
    final_date = fields.Date(string="Interview", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    state = fields.Selection([
        ('new', 'To Start'),
        ('pending', 'Appraisal Sent'),
        ('done', 'Done'),
        ('cancel', "Cancelled"),
    ], 'Status', readonly=True)
    color = fields.Integer(compute='_compute_color')

    def _compute_color(self):
        for record in self:
            record.color = COLORS_BY_STATE[record.state]

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'appraisal_analysis_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW appraisal_analysis_report AS (
                SELECT
                    MIN(a.id) AS id,
                    DATE(a.create_date) AS create_date,
                    a.employee_id AS employee_id,
                    e.department_id AS department_id,
                    a.date_close AS deadline,
                    CASE
                        WHEN MIN(ce.start) >= NOW() AT TIME ZONE 'UTC'
                        THEN MIN(ce.start)
                        ELSE MAX(ce.start)
                    END AS final_date,
                    a.state AS state
                FROM appraisal_appraisal a  -- Corrected table name
                LEFT JOIN hr_employee e ON e.id = a.employee_id
                LEFT JOIN calendar_event ce ON ce.res_id = a.id AND ce.res_model = 'appraisal.appraisal'
                GROUP BY
                    a.id,
                    a.create_date,
                    a.employee_id,
                    e.department_id,
                    a.date_close,
                    a.state
            )
        """)
