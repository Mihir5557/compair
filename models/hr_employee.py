from odoo import api, models, _, fields
from odoo.exceptions import UserError

class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    next_appraisal_date = fields.Date(string="Next Appraisal Date")
    goals_count = fields.Integer(compute='_compute_goals_count')
    related_partner_id = fields.Many2one('res.partner', compute='_compute_related_partner')
    appraisal_child_ids = fields.Many2many('hr.employee', compute='_compute_appraisal_child_ids')
    appraisal_ids = fields.One2many('appraisal.appraisal', 'employee_id')

    def _compute_appraisal_child_ids(self):
        for employee in self:
            employee.appraisal_child_ids = self.env['appraisal.appraisal'].search([('manager_ids', '=', employee.id)]).employee_id

    def _compute_related_partner(self):
        for rec in self:
            rec.related_partner_id = rec.user_id.partner_id
    

    def _compute_goals_count(self):
        read_group_result = self.env['appraisal.goal'].read_group([('employee_id', 'in', self.ids), ('progression', '!=', '100')], ['employee_id'], ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in read_group_result)
        for employee in self:
            employee.goals_count = result.get(employee.id, 0)