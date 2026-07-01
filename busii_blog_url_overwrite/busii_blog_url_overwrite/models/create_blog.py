import logging

from odoo import api
from odoo.addons.website_blog.models.website_blog import BlogPost

from .blog_blog import check_no_capitals

_logger = logging.getLogger(__name__)


class CreateWebsiteBlog(BlogPost):
    _inherit = 'blog.post'

    @api.model_create_multi
    def create(self, vals_list):
        """Validate naming convention (no capitals) before delegating to super.

        blog_id's own name is no longer checked here: blog.blog enforces the
        same rule on its own create()/write(), so it can't reach this point
        with an invalid name.

        :param list[dict] vals_list: create values for each blog.post
        :return: created blog.post recordset
        """
        _logger.info("Creating %s blog post(s)", len(vals_list))

        for vals in vals_list:
            check_no_capitals(vals.get('name'))

        posts = super(CreateWebsiteBlog, self.with_context(mail_create_nolog=True)).create(vals_list)

        for post, vals in zip(posts, vals_list):
            post._check_for_publication(vals)

        return posts