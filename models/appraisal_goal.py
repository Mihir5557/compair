from odoo import fields, api, models
from odoo.tools import html2plaintext, is_html_empty


class HrAppraisalGoal(models.Model):
    _name = "appraisal.goal"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Appraisal Goal"

    name = fields.Char(required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee",
        default=lambda self: self.env.user.employee_id, required=True)
    manager_id = fields.Many2one('hr.employee', string="Manager", required=True)
    manager_user_id = fields.Many2one('res.users', related='manager_id.user_id')
    description = fields.Html()
    deadline = fields.Date()
    notes = fields.Html(string="Description", help="The content of this description is not visible by the Employee.")
    show_attachments = fields.Boolean(string="Show Attachments", default=False)
    attachment_file = fields.Binary(string="Attachment")
    attachment_filename = fields.Char(string="Attachment Filename")
    progression = fields.Selection(selection=[
        ('0', '0 %'),
        ('25', '25 %'),
        ('50', '50 %'),
        ('75', '75 %'),
        ('100', '100 %')
    ], string="Progress", compute="_compute_progress", store=True)
    tag_ids = fields.Many2many('hr.appraisal.goal.tag', string="AppraisalTags")
    
    @api.depends('attachment_file', 'description', 'deadline')
    def _compute_progress(self):
        for record in self:
            filled_fields_count = 0
            total_fields_count = 3  # Number of fields to track (attachment_file, description, deadline)
            
            # Check if each field is filled, and count it
            if record.attachment_file:
                filled_fields_count += 1
            if record.description:
                filled_fields_count += 1
            if record.deadline:
                filled_fields_count += 1

            # Calculate the percentage
            progress_percentage = (filled_fields_count / total_fields_count) * 100
            
            # Assign the corresponding selection value based on percentage
            if progress_percentage == 0:
                record.progression = '0'
            elif progress_percentage <= 25:
                record.progression = '25'
            elif progress_percentage <= 50:
                record.progression = '50'
            elif progress_percentage <= 75:
                record.progression = '75'
            else:
                record.progression = '100'
