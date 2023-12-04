# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo.http import request
from odoo.osv import expression
from odoo import conf, http, _

from odoo.addons.project.controllers.portal import CustomerPortal

from odoo.tools import groupby as groupbyelem
from operator import itemgetter

from odoo.osv.expression import OR, AND


class ProjectCustomerPortal(CustomerPortal):

    def _task_get_searchbar_sortings(self, milestones_allowed):
        values = super()._task_get_searchbar_sortings(milestones_allowed)
        values['planned_date_begin'] = {'label': _('Planned Date'), 'order': 'planned_date_begin asc', 'sequence': -1}
        return values

    def _project_get_page_view_values(self, project, access_token, page=1, date_begin=None, date_end=None, sortby=None,
                                      search=None, search_in='content', groupby=None, **kwargs):
        if not sortby:
            sortby = 'planned_date_begin'
        if not groupby:
            groupby = 'milestone'
        values = super()._project_get_page_view_values(project, access_token, page=page, date_begin=date_begin,
                                                       date_end=date_end, sortby=sortby, search=search,
                                                       search_in=search_in, groupby=groupby, **kwargs)
        return values
