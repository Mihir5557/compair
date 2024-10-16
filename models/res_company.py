# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.misc import format_date


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_default_employee_feedback_template(self):
        return """
    <p><b>Does my company recognize my value ?</b></p><p><br><br></p>
    <p><b>What are the elements that would have the best impact on my work performance?</b></p><p><br><br></p>
    <p><b>What are my best achievement(s) since my last appraisal?</b></p><p><br><br></p>
    <p><b>What do I like / dislike about my job, the company or the management?</b></p><p><br><br></p>
    <p><b>How can I improve (skills, attitude, etc)?</b></p><p><br><br></p>"""

    def _get_default_manager_feedback_template(self):
        return """
    <p><b>What are the responsibilities that the employee performs effectively?</b></p><p><br><br></p>
    <p><b>How could the employee improve?</b></p><p><br><br></p>
    <p><b>Short term (6-months) actions / decisions / objectives</b></p><p><br><br></p>
    <p><b>Long term (>6months) career discussion, where does the employee want to go, how to help him reach this path?</b></p><p><br><br></p>"""

    def _get_default_appraisal_survey_template_id(self):
        return self.env.ref('hr_appraisal_survey.appraisal_feedback_template', raise_if_not_found=False)

    appraisal_survey_template_id = fields.Many2one('survey.survey')
    hr_appraisal_plan = fields.Boolean(string='Automatically Generate Appraisals', default=True)
    assessment_note_ids = fields.One2many('appraisal.note', 'company_id')
    send_feedback_employee = fields.Html(default=_get_default_employee_feedback_template)
    send_feedback_manager = fields.Html(default=_get_default_manager_feedback_template)
    duration_after_recruitment = fields.Integer(string="Create an Appraisal after recruitment", default=6)
    month_first = fields.Integer(string="Create a first Appraisal after", default=6)
    month_next = fields.Integer(string="Create a second Appraisal after")


