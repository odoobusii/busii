from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    parent_project_id = fields.Many2one(
        'project.project',
        string='Parent Project',
        help="Select a parent project to make this project a sub-project."
    )


    sub_project_ids = fields.One2many(
        'project.project',
        'parent_project_id',
        string='Sub-Projects',
        help="Sub-projects created under this project."
    )

    user_id = fields.Many2one('res.users', string='Project Manager', default=lambda self: self.env.user, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, tracking=True, domain="['|', ('company_id', '=?', company_id), ('company_id', '=', False)]")
    company_id = fields.Many2one('res.company', string='Company', compute="_compute_company_id", inverse="_inverse_company_id", store=True, readonly=False)


    sub_project_count = fields.Integer(
        string='Sub-Projects Count',
        compute='_compute_sub_project_count'
    )

    parent_project_name = fields.Char(
        string='Parent Project Name',
        compute='_compute_parent_project_name'
    )

    def _compute_parent_project_name(self):
        for project in self:
            project.parent_project_name = project.parent_project_id.name if project.parent_project_id else ''

    def _compute_sub_project_count(self):
        for project in self:
            project.sub_project_count = len(project.sub_project_ids)
   

    @api.model
    def create(self, vals):
        """Ensure that sub-project relationships are maintained when creating a new project."""
        new_project = super(ProjectProject, self).create(vals)
        if new_project.parent_project_id:
            parent_project = new_project.parent_project_id
            parent_project.sub_project_ids = [(4, new_project.id)]
        return new_project

    def write(self, vals):
        """Handle updates to parent project relationships."""
        res = super(ProjectProject, self).write(vals)
        if 'parent_project_id' in vals:
            for project in self:
                if project.parent_project_id:
                    parent_project = project.parent_project_id
                    if project.id not in parent_project.sub_project_ids.ids:
                        parent_project.sub_project_ids = [(4, project.id)]
        return res

    
    def action_view_sub_projects(self):
        """Open a view displaying all sub-projects of the current project."""
        self.ensure_one()
        return {
            'name': 'Sub-Projects',
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.sub_project_ids.ids)],
            'context': {'default_parent_project_id': self.id},
            'target': 'current',
        }

    def action_view_parent_project(self):
        """Open the form view of the parent project."""
        self.ensure_one()
        if not self.parent_project_id:
            return
        return {
            'name': 'Parent Project',
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'view_mode': 'form',
            'res_id': self.parent_project_id.id,
            'target': 'current',
        }
