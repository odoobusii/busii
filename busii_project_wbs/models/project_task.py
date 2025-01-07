# from odoo import models, fields, api

# class ProjectTask(models.Model):
#     _inherit = 'project.task'

#     parent_task_id = fields.Many2one('project.task', string='Parent Task', ondelete='cascade')
#     child_task_ids = fields.One2many('project.task', 'parent_task_id', string='Subtasks')
#     wbs_level = fields.Integer(string='WBS Level', compute='_compute_wbs_level', store=True)
#     progress = fields.Float(string='Progress', compute='_compute_progress', store=True)

#     @api.depends('child_task_ids.progress')
#     def _compute_progress(self):
#         for task in self:
#             if task.child_task_ids:
#                 task.progress = sum(child.progress for child in task.child_task_ids) / len(task.child_task_ids)
#             else:
#                 task.progress = 0.0

#     @api.depends('parent_task_id')
#     def _compute_wbs_level(self):
#         for task in self:
#             level = 0
#             parent = task.parent_task_id
#             while parent:
#                 level += 1
#                 parent = parent.parent_task_id
#             task.wbs_level = level

# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)

class SimpleGantt(models.Model):
    _inherit = 'project.task'

    partner_id = fields.Many2one('res.partner')
    allocated_hours = fields.Float('project.task')
    child_ids = fields.One2many('project.task')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    # Define fields for task dependencies
    depends_on_task_ids = fields.Many2many('project.task', 'task_dependency_rel', 'task_id', 'dependency_id', string="Depends On")
    dependent_task_ids = fields.Many2many('project.task', 'task_dependency_rel', 'dependency_id', 'task_id', string="Dependent Tasks")

    # parent_task_id = fields.Many2one('project.task', string='Parent Task', ondelete='cascade')
    wbs_level = fields.Integer(string='WBS Level', compute='_compute_wbs_level', store=True)

    # New field for color mapping
    gantt_color = fields.Integer(string='Gantt Color', compute='_compute_gantt_color', store=True)

    # Display a list of projects an assignee is involved in
    project_list = fields.Char(string="Projects Assigned", compute='_compute_project_list')
    subtask_list = fields.Char(string="Subtasks", compute='_compute_subtask_list')

    subtask_indicator = fields.Char(
        string='Subtask Indicator',
        compute='_compute_subtask_indicator',
        help="Determines the visual indicator for subtasks."
    )

    @api.depends('child_ids')
    def _compute_subtask_indicator(self):
        for task in self:
            task.subtask_indicator = 'has_subtasks' if task.child_ids else 'no_subtasks'


    @api.depends('partner_id')
    def _compute_gantt_color(self):
        # _logger.info(f"Checking: {self.name} for partner_id: {self.partner_id.name}")
        for task in self:
            _logger.info(f"Found: {task.partner_id.name}")
            if task.partner_id:
                _logger.info(f"We have: {task.partner_id}")
                task.gantt_color = hash(task.partner_id.id) % 10
                _logger.info(f"Computed Gantt Color for Task {task.name} with Partner ID {task.partner_id.id}: {task.gantt_color}")
            else:
                task.gantt_color = 0
                _logger.info(f"Default Gantt Color applied for Task {task.name}")
    
    @api.depends('parent_id')
    def _compute_wbs_level(self):
        # _logger.info(f"Checking: {self.name} for parent_id {self.parent_id.name}")
        for task in self:
            _logger.info(f"Found: {task.name}")
            level = 0
            parent = task.parent_id
            _logger.info(f"We have parent id: {task.parent_id.name} and wbs level: {task.wbs_level}")
            while parent:
                level += 1
                parent = parent.parent_id
            task.wbs_level = level
            _logger.info(f"WBS Level computed for Task {task.name}: {task.wbs_level}")

    
    @api.model
    def update_existing_records(self):
        """Log detailed processing of all existing project tasks."""
        tasks = self.search([])
        _logger.info(f"Starting WBS Level and Gantt Color update for {len(tasks)} tasks.")
        
        for task in tasks:
            _logger.info(f"Processing Task: '{task.name}' (ID: {task.id})")
            
            # Recompute WBS Level
            task._compute_wbs_level()
            
            # Recompute Gantt Color
            task._compute_gantt_color()

        _logger.info("Completed WBS Level and Gantt Color update for all tasks.")

    
    @api.depends('partner_id')
    def _compute_project_list(self):
        _logger.info(f"Checking {self.partner_id}.")

        for task in self:
            _logger.info(f"Found {task.name}.")
            assigned_projects = self.env['project.task'].search([
                ('partner_id', '=', task.partner_id.id),
                ('id', '!=', task.id)  # Exclude current task to avoid redundancy
            ])
            task.project_list = ", ".join(assigned_projects.mapped('name'))

    @api.depends('child_ids')
    def _compute_subtask_list(self):
        _logger.info(f"Found {self.child_ids}.")
        for task in self:
            task.subtask_list = ", ".join(task.child_ids.mapped('name'))

    
    def action_view_subtasks(self):
        """Returns an action to view subtasks of the current task."""
        self.ensure_one()
        action = self.env.ref('busii_project_wbs.action_view_subtasks_popup').read()[0]
        action['domain'] = [('parent_id', '=', self.id)]
        return action

    @api.model
    def create(self, values):
        task = super(SimpleGantt, self).create(values)
        # Ensure dependencies are set up after task creation
        if task.depends_on_task_ids:
            task._update_dependencies()
        return task

    def _update_dependencies(self):
        """ Update the dependent tasks after a task's dependencies are set. """
        for task in self:
            for dependency in task.depends_on_task_ids:
                dependency.write({'dependent_task_ids': [(4, task.id)]})

    @api.model
    def unlink(self):
        """ Ensure dependencies are removed when deleting a task. """
        for task in self:
            task.dependent_task_ids.write({'depends_on_task_ids': [(3, task.id)]})
        return super(SimpleGantt, self).unlink()

