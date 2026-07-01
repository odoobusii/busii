# -*- coding: utf-8 -*-
import logging

from odoo import http, _
from odoo.http import request
from odoo.addons.project.controllers.portal import ProjectCustomerPortal
from odoo.addons.hr_timesheet.controllers.portal import TimesheetCustomerPortal

_logger = logging.getLogger(__name__)


class BusiiProjectCustomerPortal(ProjectCustomerPortal):

    def _task_get_searchbar_sortings(self, milestones_allowed, project=False):
        values = super()._task_get_searchbar_sortings(milestones_allowed, project)
        _logger.info("busii_portal: injecting planned_date_begin sort option")
        values['planned_date_begin'] = {
            'label': _('Planned Date'),
            'order': 'planned_date_begin asc',
            'sequence': 5,
        }
        return values

    @http.route(
        ['/my/projects/<int:project_id>', '/my/projects/<int:project_id>/page/<int:page>'],
        type='http', auth="public", website=True
    )
    def portal_my_project(self, project_id=None, access_token=None, page=1, date_begin=None,
                          date_end=None, sortby=None, search=None, search_in='content',
                          groupby=None, task_id=None, **kw):
        """Override to force default sortby and groupby for busii portal."""
        if not sortby:
            sortby = 'planned_date_begin'
        if not groupby or groupby == 'project_id':
            project = request.env['project.project'].browse(project_id)
            groupby = 'milestone_id' if project.allow_milestones else 'none'

        _logger.info(
            "busii_portal: portal_my_project called — sortby=%s, groupby=%s", sortby, groupby
        )

        return super().portal_my_project(
            project_id=project_id, access_token=access_token, page=page,
            date_begin=date_begin, date_end=date_end, sortby=sortby,
            search=search, search_in=search_in, groupby=groupby,
            task_id=task_id, **kw
        )
    
    class BusiiTimesheetPortal(TimesheetCustomerPortal):

        def _prepare_home_portal_values(self, counters):
            if request.env.user.share:
                counters = [c for c in counters if c != 'timesheet_count']
            return super()._prepare_home_portal_values(counters)