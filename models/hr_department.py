
from odoo import api, fields, models, _


class hr_department(models.Model):
    _inherit = 'hr.department'

    def _get_default_appraisal_survey_template_id(self):
        return self.env.company.appraisal_survey_template_id

    custom_appraisal_templates = fields.Boolean(string="Custom Appraisal Templates", default=False)
    appraisal_survey_template_id = fields.Many2one('survey.survey', string='Appraisal Survey',
        help='This field is used with 360 Feedback setting on Appraisal App, the aim is to define a default Survey Template related to this department.',
         default=_get_default_appraisal_survey_template_id)