# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

import werkzeug

from odoo import http, fields, tools
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_blog.controllers.main import WebsiteBlog
from odoo.http import request

_logger = logging.getLogger(__name__)


class CustomWebsiteBlog(WebsiteBlog):
    """Override blog routes to resolve blog/post by name instead of the
    default `<model(...)>` slug-with-id converter, matching legacy URLs
    of the form /blog/<blog-name>/<post-name>.
    """

    def _find_blog_by_name(self, blog_slug):
        """Resolve a blog.blog record from a free-text slug.

        :param str blog_slug: hyphenated or spaced blog name fragment
        :return: blog.blog recordset (possibly empty)
        """
        blog_space = blog_slug.replace('-', ' ')
        blog_hyphen = blog_slug.replace(' ', '-')
        return request.env['blog.blog'].search([
            '|', '|',
            ('name', 'ilike', blog_slug),
            ('name', 'ilike', blog_space),
            ('name', 'ilike', blog_hyphen),
        ])

    def _find_post_in_blogs(self, blog_records, post_slug):
        """Resolve a blog.post within a set of candidate blogs by name.

        Iterates blogs in order and returns the first match found, since
        post names are not guaranteed unique across blogs.

        :param blog_records: blog.blog recordset to search within
        :param str post_slug: hyphenated post name fragment
        :return: blog.post recordset (empty if not found)
        """
        post_name = post_slug.lower()
        post_space = post_name.replace('-', ' ')
        BlogPost = request.env['blog.post']

        for record in blog_records:
            _logger.debug("Searching post '%s' in blog ID=%s", post_name, record.id)
            blog_post = BlogPost.search([
                ('blog_id', '=', record.id),
                '|',
                ('name', 'ilike', post_name),
                ('name', 'ilike', post_space),
            ], limit=1)
            if blog_post:
                return blog_post
        return BlogPost

    @http.route(['/blog/<string:blog>/<string:post>'], type='http', auth="public", website=True)
    def blog_post(self, blog, post, tag_id=None, page=1, enable_editor=None, **kwargs):
        """Render a blog post resolved by name-based slugs.

        :param str blog: blog name slug
        :param str post: post name slug
        :param str tag_id: optional blog.tag id to highlight
        """
        _logger.info("Blog post request: blog='%s' post='%s'", blog, post)

        blog_record = self._find_blog_by_name(blog)
        if not blog_record:
            _logger.warning("No blog found for slug='%s'", blog)
            return request.not_found()

        blog_post = self._find_post_in_blogs(blog_record, post)
        if not blog_post or not blog_post.exists():
            _logger.warning("No post found for blog='%s', post='%s'", blog, post)
            return request.not_found()

        tag = request.env['blog.tag'].browse(int(tag_id)) if tag_id else None
        all_blogs = request.env['blog.blog'].search([])
        blog_url = QueryURL('', ['blog', 'tag'], blog=blog_post.blog_id, tag=tag, date_begin=None, date_end=None)

        return request.render("website_blog.blog_post_complete", {
            'tag': tag,
            'blog': blog_post.blog_id,
            'blog_post': blog_post,
            'main_object': blog_post,
            'blogs': all_blogs,
            'blog_url': blog_url,
        })

    @http.route([
        '/blog',
        '/blog/page/<int:page>',
        '/blog/tag/<string:tag>',
        '/blog/tag/<string:tag>/page/<int:page>',
        '/blog/<string:blog>',
        '/blog/<string:blog>/page/<int:page>',
        '/blog/<string:blog>/tag/<string:tag>',
        '/blog/<string:blog>/tag/<string:tag>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=True)
    def blog(self, blog=None, tag=None, page=1, search=None, **opt):
        """Render the blog listing page, resolving an optional blog by name slug."""
        _logger.info("Blog listing request: blog='%s'", blog)

        date_begin, date_end = opt.get('date_begin'), opt.get('date_end')
        Blog = request.env['blog.blog']
        blogs = tools.lazy(lambda: Blog.search(request.website.website_domain(), order="create_date asc, id asc"))

        blog_record = None
        if blog:
            blog_record = self._find_blog_by_name(blog)[:1]
            if not blog_record:
                _logger.warning("No blog found for slug='%s'", blog)
                return request.not_found()

        domain = []
        if blog_record:
            domain.append(('blog_id', '=', blog_record.id))
        if tag:
            domain.append(('tag_ids', 'in', int(tag)))
        if date_begin and date_end:
            domain += [('post_date', '>=', date_begin), ('post_date', '<=', date_end)]

        # blog_posts is fetched for parity with stock behaviour; _prepare_blog_values
        # performs its own pagination/search internally.
        request.env['blog.post'].search(domain, order="post_date desc")

        values = self._prepare_blog_values(
            blogs=blogs,
            blog=blog_record,
            tags=tag,
            page=page,
            search=search,
            **opt
        )
        values['blog_url'] = QueryURL(
            '/blog', ['blog', 'tag'], blog=blog_record, tag=tag,
            date_begin=date_begin, date_end=date_end, search=search,
        )

        return request.render("website_blog.blog_post_short", values)