from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
import datetime

class Appraisal(models.Model):
    _name = 'appraisal.appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _description = 'Employee Appraisal'

    name = fields.Char(string='Title', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    image_emp = fields.Image(related='employee_id.avatar_128')
    manager_ids = fields.Many2many('hr.employee', 'appraisal_managers_rel', 'appraisal_id', context={'active_test': False}, string='Manager',required=True)
    score = fields.Integer(string='Score', required=True)
    comments = fields.Text(string='Comments')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True)
    note = fields.Html(string="Private Note", help="The content of this note is not visible by the Employee.")
    state = fields.Selection(
        [('new', 'To Confirm'),
         ('pending', 'Confirmed'),
         ('done', 'Done'),
         ('cancel', "Cancelled")],
        string='Status', tracking=True, required=True, copy=False,
        default='new', index=True, group_expand='_group_expand_states')
    prev_appraisal_id = fields.Many2one('appraisal.appraisal')
    prev_appraisal_date = fields.Date(related='prev_appraisal_id.date_close', string='Previous Appraisal Date')
    date_close = fields.Date(
        string='Date Appraisal', help='Date of the appraisal, automatically updated when the appraisal is Done or Cancelled.', required=True, index=True,
        default=lambda self: datetime.date.today() + relativedelta(months=+1))
    last_appraisal_date = fields.Date(string="Last Appraisal Date")
    next_appraisal_date = fields.Date(string="Next Appraisal Date", compute="_compute_next_appraisal_date", store=True)
    meeting_ids = fields.Many2many('calendar.event', string='Meetings')
    waiting_feedback = fields.Boolean(
        string="Waiting Feedback from Employee/Managers", compute='_compute_waiting_feedback', tracking=True)
    is_employee_feedback_published = fields.Boolean(string="Employee Feedback Published", tracking=True)
    is_manager_feedback_published = fields.Boolean(string="Manager Feedback Published", tracking=True)
    final_date_interview = fields.Date(string="Final Interview")
    department_id = fields.Many2one(
        'hr.department', related='employee_id.department_id', string='Department', store=True)
    meeting_count = fields.Char(string='Meeting Count', compute='_compute_meeting_count')
    final_date = fields.Date(string="Final Interview", compute='_compute_final_date')
    manager_feedback = fields.Boolean(compute='_compute_manager_feedback')
    can_see_employee_publish = fields.Boolean(compute='_compute_buttons_display')
    can_see_manager_publish = fields.Boolean(compute='_compute_buttons_display')
    goals_count = fields.Integer(related='employee_id.goals_count')
    employee_feedback = fields.Html(compute='_compute_employee_feedback', store=True, readonly=False)
    show_manager_feedback_full = fields.Boolean(compute='_compute_show_manager_feedback_full')
    employee_feedback_template = fields.Html(compute='_compute_feedback_templates')
    manager_feedback_template = fields.Html(compute='_compute_feedback_templates')
    show_employee_feedback_full = fields.Boolean(compute='_compute_show_employee_feedback_full')
    employee_user_id = fields.Many2one('res.users', string="Employee User", related='employee_id.user_id')
    assessment_note = fields.Many2one('appraisal.note', string="Final Rating", help="This field is not visible to the Employee.", domain="[('company_id', '=', company_id)]")
    manager_user_ids = fields.Many2many('res.users', string="Manager Users", compute='_compute_user_manager_rights')
    is_implicit_manager = fields.Boolean(compute='_compute_user_manager_rights')
    is_appraisal_manager = fields.Boolean(compute='_compute_user_manager_rights')
    employee_autocomplete_ids = fields.Many2many('hr.employee', compute='_compute_user_manager_rights')
    skill_ids = fields.One2many('hr.appraisal.skill', 'appraisal_id', string="Skills")
    employee_feedback_ids = fields.Many2many('hr.employee', string="Asked Feedback")
    survey_ids = fields.Many2many('survey.survey', help="Sent out surveys")

    def action_ask_feedback(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'appraisal.ask.feedback',
            'target': 'new',
            'name': 'Ask Feedback',
        }

    def action_open_survey_inputs(self):
        self.ensure_one()
        if (self.user_has_groups('aspl_hr_appraisal.group_hr_appraisal_manager') or self.env.user.employee_id in self.manager_ids) and len(self.survey_ids) > 1:
            return {
                'name': _("Survey Feedback"),
                'type': 'ir.actions.act_window',
                "views": [[self.env.ref('hr_appraisal_survey.survey_user_input_view_tree').id, 'tree']],
                'view_mode': 'tree',
                'res_model': 'survey.user_input',
                'domain': [('appraisal_id', 'in', self.ids)],
            }
        return {
            'type': 'ir.actions.act_url',
            'name': _("Survey Feedback"),
            'target': 'self',
            'url': '/appraisal/%s/results/' % (self.id)
        }

    def write(self, vals):
        if 'state' in vals and vals['state'] == 'pending':
            new_appraisals = self.filtered(lambda a: a.state == 'new')
            new_appraisals._copy_skills_when_confirmed()

        if 'state' in vals and vals['state'] == 'done':
            for appraisal in self:
                employee_skills = appraisal.employee_id.employee_skill_ids
                appraisal_skills = appraisal.skill_ids
                updated_skills = []
                deleted_skills = []
                added_skills = []
                for employee_skill in employee_skills.filtered(lambda s: s.skill_id in appraisal_skills.skill_id):
                    appraisal_skill = appraisal_skills.filtered(lambda a: a.skill_id == employee_skill.skill_id)
                    if employee_skill.level_progress != appraisal_skill.level_progress:
                        updated_skills.append({
                            'name': employee_skill.skill_id.name,
                            'old_level': employee_skill.level_progress,
                            'new_level': appraisal_skill.level_progress,
                            'justification': appraisal_skill.justification,
                        })

                deleted_skills = employee_skills.filtered(lambda s: s.skill_id not in appraisal_skills.skill_id).mapped('skill_id.name')
                added_skills = appraisal_skills.filtered(lambda a: a.skill_id not in employee_skills.skill_id).mapped('skill_id.name')

                employee_skills.sudo().unlink()
                self.env['hr.employee.skill'].sudo().create([{
                    'employee_id': appraisal.employee_id.id,
                    'skill_id': skill.skill_id.id,
                    'skill_level_id': skill.skill_level_id.id,
                    'skill_type_id': skill.skill_type_id.id,
                } for skill in appraisal_skills])

                if len(updated_skills + added_skills + deleted_skills) > 0:
                    template = self.env.ref('hr_appraisal_skills.appraisal_skills_update_template', raise_if_not_found=False)
                    rendered = template._render({
                        'updated_skills': updated_skills,
                        'added_skills': added_skills,
                        'deleted_skills': deleted_skills,
                    }, engine='ir.qweb')
                    appraisal.message_post(body=rendered)
        result = super(Appraisal, self).write(vals)
        return result

    def _copy_skills_when_confirmed(self):
        for appraisal in self:
            employee_skills = appraisal.employee_id.employee_skill_ids
            for skill in employee_skills:
                # in case the employee confirms its appraisal
                self.env['hr.appraisal.skill'].sudo().create({
                    'appraisal_id': appraisal.id,
                    'skill_id': skill.skill_id.id,
                    'skill_level_id': skill.skill_level_id.id,
                    'skill_type_id': skill.skill_type_id.id,
                    'employee_skill_id': skill.id,
                })
    
    @api.depends_context('uid')
    @api.depends('employee_id', 'manager_ids')
    def _compute_user_manager_rights(self):
        for appraisal in self:
            appraisal.manager_user_ids = appraisal.manager_ids.mapped('user_id')
        self.is_appraisal_manager = self.user_has_groups('hr_appraisal.group_hr_appraisal_user')
        if self.is_appraisal_manager:
            self.is_implicit_manager = False
            self.employee_autocomplete_ids = self.env['hr.employee'].search([('company_id', '=', self.env.company.id)])
        else:
            child_ids = self.env.user.employee_id.child_ids
            appraisal_child_ids = self.env.user.employee_id.appraisal_child_ids
            self.employee_autocomplete_ids = child_ids + appraisal_child_ids + self.env.user.employee_id
            self.is_implicit_manager = len(self.employee_autocomplete_ids) > 1

    @api.depends('employee_id', 'manager_ids')
    def _compute_buttons_display(self):
        new_appraisals = self.filtered(lambda a: a.state == 'new')
        new_appraisals.update({
            'can_see_employee_publish': False,
            'can_see_manager_publish': False,
        })
        user_employee = self.env.user.employee_id
        is_manager = self.env.user.user_has_groups('aspl_hr_appraisal.group_hr_appraisal_manager')
        for appraisal in self:
            appraisal.can_see_employee_publish = user_employee == appraisal.employee_id
            appraisal.can_see_manager_publish = user_employee.id in appraisal.manager_ids.ids
        for appraisal in self - new_appraisals:
            if is_manager and not appraisal.can_see_employee_publish and not appraisal.can_see_manager_publish:
                appraisal.can_see_employee_publish, appraisal.can_see_manager_publish = True, True

    @api.depends_context('uid')
    @api.depends('employee_id', 'is_employee_feedback_published')
    def _compute_show_employee_feedback_full(self):
        for appraisal in self:
            is_appraisee = appraisal.employee_id.user_id == self.env.user
            appraisal.show_employee_feedback_full = is_appraisee and not appraisal.is_employee_feedback_published

    @api.depends('department_id', 'company_id')
    def _compute_feedback_templates(self):
        for appraisal in self:
            appraisal.employee_feedback_template = appraisal.department_id.employee_feedback_template if appraisal.department_id.custom_appraisal_templates \
                else appraisal.company_id.send_feedback_employee
            appraisal.manager_feedback_template = appraisal.department_id.manager_feedback_template if appraisal.department_id.custom_appraisal_templates \
                else appraisal.company_id.send_feedback_manager

    @api.depends('department_id')
    def _compute_employee_feedback(self):
        for appraisal in self.filtered(lambda a: a.state == 'new'):
            appraisal.employee_feedback = appraisal.department_id.employee_feedback_template if appraisal.department_id.custom_appraisal_templates \
                else appraisal.company_id.send_feedback_employee

    @api.depends('is_employee_feedback_published', 'is_manager_feedback_published')
    def _compute_waiting_feedback(self):
        for appraisal in self:
            appraisal.waiting_feedback = not appraisal.is_employee_feedback_published or not appraisal.is_manager_feedback_published

    @api.depends('last_appraisal_date')
    def _compute_next_appraisal_date(self):
        config_param = self.env['ir.config_parameter'].sudo()
        month_next_value = config_param.get_param('month_next')
        months = int(month_next_value) if month_next_value else 12
        for record in self:
            if record.last_appraisal_date:
                record.next_appraisal_date = record.last_appraisal_date + relativedelta(months=months)
            else:
                record.next_appraisal_date = False
    
    @api.depends_context('uid')
    @api.depends('manager_ids', 'is_manager_feedback_published')
    def _compute_show_manager_feedback_full(self):
        for appraisal in self:
            is_appraiser = self.env.user in appraisal.manager_ids.user_id
            appraisal.show_manager_feedback_full = is_appraiser and not appraisal.is_manager_feedback_published

    @api.depends_context('uid')
    @api.depends('manager_ids', 'is_employee_feedback_published')
    def _compute_manager_feedback(self):
        for appraisal in self:
            is_appraiser = self.env.user in appraisal.manager_ids.user_id
            appraisal.manager_feedback = is_appraiser and not appraisal.is_employee_feedback_published

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in self._fields['state'].selection]
    
    def auto_create_appraisal(self):
        today = fields.Date.context_today(self)
        # Find employees whose next appraisal is due today or earlier
        employees = self.env['appraisal.employee'].search([
            ('next_appraisal_date', '<=', today)
        ])
        
        for employee in employees:
            # Check if the employee has a parent (manager)
            if employee.parent_id:
                # Create a meaningful name for the appraisal
                appraisal_name = f"Appraisal for {employee.name} on {today}"
                
                # Create the appraisal record
                self.env['appraisal.appraisal'].create({
                    'name': appraisal_name,  # Provide a name for the appraisal
                    'employee_id': employee.id,
                    'manager_ids': [(6, 0, [employee.parent_id.id])],  # Assign the parent (manager) to the Many2many field
                    'last_appraisal_date': today,
                })
            
            # Update employee's next appraisal date (6 months later)
            employee.write({
                'next_appraisal_date': today + relativedelta(months=6)
            })

    def action_open_last_appraisal(self):
        self.ensure_one()
        return {
            'view_mode': 'form',
            'res_model': 'appraisal.appraisal',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.prev_appraisal_id.id,
        }

    def action_calendar_event(self):
        self.ensure_one()
        partners = self.manager_ids.mapped(
            'related_partner_id') | self.employee_id.related_partner_id | self.env.user.partner_id
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        action['context'] = {
            'default_partner_ids': partners.ids,
            'default_res_model': 'appraisal.appraisal',
            'default_res_id': self.id,
            'default_name': _('Appraisal of %s', self.employee_id.name),
        }
        return action

    def action_appraisal_goals(self):
        self.ensure_one()
        return {
            'name': _('%s Goals') % self.employee_id.name,
            'view_mode': 'kanban,tree,form',
            'res_model': 'appraisal.goal',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('employee_id', '=', self.employee_id.id)],
            'context': {'default_employee_id': self.employee_id.id},
        }

    @api.depends_context('lang')
    @api.depends('meeting_ids')
    def _compute_meeting_count(self):
        today = fields.Date.today()
        for appraisal in self:
            count = len(appraisal.meeting_ids)
            if not count:
                appraisal.meeting_count = _('No Meeting')
            elif count == 1:
                appraisal.meeting_count = _('1 Meeting')
            elif appraisal.final_date >= today:
                appraisal.meeting_count = _('Next Meeting')
            else:
                appraisal.meeting_count = _('Last Meeting')

    @api.depends('meeting_ids.start')
    def _compute_final_date(self):
        today = fields.Date.today()
        with_meeting = self.filtered('meeting_ids')
        (self - with_meeting).final_date = False
        for appraisal in with_meeting:
            all_dates = appraisal.meeting_ids.mapped('start')
            min_date, max_date = min(all_dates), max(all_dates)
            if min_date.date() >= today:
                appraisal.final_date = min_date
            else:
                appraisal.final_date = max_date

    def action_confirm(self):
        self.state = 'pending'

    def action_cancel(self):
        self.state = 'cancel'

    def action_done(self):
        self.state = 'done'

    def action_back(self):
        self.state = 'new'

    def action_send_appraisal_request(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'request.appraisal',
            'target': 'new',
            'name': _('Appraisal Request'),
            'context': {'default_appraisal_id': self.id},
        }


class HrAppraisalSkill(models.Model):
    _name = 'hr.appraisal.skill'
    _description = "Employee Skills"

    appraisal_id = fields.Many2one('appraisal.appraisal', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', related='appraisal_id.employee_id', store=True)
    manager_ids = fields.Many2many('hr.employee', compute='_compute_manager_ids', store=True)

    skill_id = fields.Many2one('hr.skill', required=True)
    skill_level_id = fields.Many2one('hr.skill.level', required=True)
    skill_type_id = fields.Many2one(related='skill_id.skill_type_id')
    level_progress = fields.Integer(related='skill_level_id.level_progress', string="Improvement")
    justification = fields.Char(string="apology")
    employee_skill_id = fields.Many2one('hr.employee.skill')

    _sql_constraints = [
        ('_unique_skill', 'unique (appraisal_id, skill_id)', "Two levels for the same skill is not allowed"),
    ]

    @api.depends('appraisal_id')
    def _compute_manager_ids(self):
        for skill in self:
            skill.manager_ids = skill.appraisal_id.manager_ids
