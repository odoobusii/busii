# -*- coding: utf-8 -*-
from odoo import models, fields
# from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_blog.models.website_blog import BlogPost
import logging
_logger = logging.getLogger(__name__)

class BlogPostUrl(BlogPost):
    _inherit = 'blog.post'


    def _compute_website_url(self):
        """
        Override to modify the URL structure to '/blog/<blog_slug>/<post_slug>'.
        Log each step to monitor the URL generation process.
        """
        for post in self:
            try:
                # Use the name as a fallback if `slug` is unavailable
                # blog_slug = post.blog_id.slug if hasattr(post.blog_id, 'slug') else post.blog_id.name
                # post_slug = post.slug if hasattr(post.blog_id, 'slug') else post.name  # Get the post's slug
                blog_slug = post.blog_id.name
                post_slug = post.name  # Get the post's slug


                # Ensure no spaces and lowercase for URLs
                blog_slug = blog_slug.replace(" ", "-").lower()
                post_slug = post_slug.replace(" ", "-").lower()

                # Log slug information
                # _logger.info(f"Generating URL for BlogPost ID {post.id}: blog_slug='{blog_slug}', post_slug='{post_slug}'")
                
                # Set the custom URL format
                post.website_url = f"/blog/{blog_slug}/{post_slug}"
                # _logger.info(f"URL set for BlogPost ID {post.id}: {post.website_url}")

            except Exception as e:
                # Log any exception that occurs during URL generation
                _logger.error(f"Error computing URL for BlogPost ID {post.id}: {str(e)}")
                raise