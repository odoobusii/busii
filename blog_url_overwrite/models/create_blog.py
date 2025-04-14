from odoo import http, fields, tools, models
from odoo.addons.website_blog.models.website_blog import BlogPost
from odoo.tools import html2plaintext
from odoo.tools.misc import get_lang
from odoo.tools import sql
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class CreateWebsiteBlog(BlogPost): 
    _inherit = 'blog.post'

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info(f"Creating new blog post: {vals_list}")

        for vals in vals_list:
            # Check if 'name' contains capital letters
            if 'name' in vals and any(char.isupper() for char in vals['name']):
                raise UserError("The Blog or blog Title cannot contain capital letters!")
            
            # Check if 'blog_id' is an integer and fetch the blog name
            if 'blog_id' in vals:
                blog_id = vals['blog_id']
                if isinstance(blog_id, int):
                    blog_name = self.env['blog.blog'].browse(blog_id).name
                    if any(char.isupper() for char in blog_name):
                        raise UserError("The Blog or blog Title cannot contain capital letters!")

        # Create the posts after validation
        posts = super(CreateWebsiteBlog, self.with_context(mail_create_nolog=True)).create(vals_list)

        # Additional publication checks (if needed)
        for post, vals in zip(posts, vals_list):
            post._check_for_publication(vals)

        return posts
