import logging

from odoo.addons.website_blog.models.website_blog import BlogPost

_logger = logging.getLogger(__name__)


class BlogPostUrl(BlogPost):
    _inherit = 'blog.post'

    def _compute_website_url(self):
        """Override to produce '/blog/<blog-slug>/<post-slug>' URLs.

        Falls back to a simple lowercase/hyphenated name slug rather than
        the stock id-suffixed slug, to match the custom name-based routes
        in CustomWebsiteBlog.
        """
        for post in self:
            blog_slug = post.blog_id.name.replace(" ", "-").lower()
            post_slug = post.name.replace(" ", "-").lower()
            post.website_url = f"/blog/{blog_slug}/{post_slug}"
            _logger.debug("Computed website_url for BlogPost ID=%s: %s", post.id, post.website_url)