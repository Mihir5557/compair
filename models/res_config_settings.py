# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hr_appraisal_plan = fields.Boolean(related='company_id.hr_appraisal_plan', readonly=False)
    assessment_note_ids = fields.One2many(
        related='company_id.assessment_note_ids', string="Appraisal Notes", readonly=False)
    send_feedback_employee = fields.Html(related='company_id.send_feedback_employee', readonly=False)
    send_feedback_manager = fields.Html(related='company_id.send_feedback_manager', readonly=False)
    duration_after_recruitment = fields.Integer(related='company_id.duration_after_recruitment', readonly=False)
    month_first = fields.Integer(related='company_id.month_first', readonly=False)
    month_next = fields.Integer(related='company_id.month_next', readonly=False)
    module_hr_appraisal_survey = fields.Boolean(string="360 Feedback")
    appraisal_survey_template_id = fields.Many2one(
        'survey.survey', related='company_id.appraisal_survey_template_id', domain=[('is_appraisal', '=', True)], readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        # Get the value from ir.config_parameter
        res['module_hr_appraisal_survey'] = self.env['ir.config_parameter'].sudo().get_param('module_hr_appraisal_survey', default=False)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        # Save the value in ir.config_parameter
        self.env['ir.config_parameter'].sudo().set_param('module_hr_appraisal_survey', self.module_hr_appraisal_survey)