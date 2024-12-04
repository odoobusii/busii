from odoo import http
from odoo.addons.website_blog.controllers.main import WebsiteBlog
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
import logging
_logger = logging.getLogger(__name__)

import werkzeug
import itertools
import pytz
import babel.dates
from collections import defaultdict

from odoo import http, fields, tools, models
from odoo.addons.website.controllers.main import QueryURL
from odoo.tools import html2plaintext
from odoo.tools.misc import get_lang
from odoo.tools import sql

class CustomWebsiteBlog(WebsiteBlog):
    @http.route(['/blog/<string:blog>/<string:post>'], type='http', auth="public", website=True)
    def blog_post(self, blog, post, tag_id=None, page=1, enable_editor=None, **kwargs):
        """
        Render the blog post page using the new URL format.
        Log each step to monitor the routing and search process.
        """
        _logger.info(f"Received request for blog post: blog='{blog}', post='{post}")
        
        try:

            # Fetch all valid blogs and posts
            valid_blogs = request.env['blog.blog'].search([])
            valid_blog_posts = request.env['blog.post'].search([])
            
            # Create a dictionary of valid blog and post names mapped to their IDs
            valid_blog_ids = {blog_record.id: blog_record.name for blog_record in valid_blogs}
            valid_post_ids = {post_record.id: post_record.name for post_record in valid_blog_posts}
            
            _logger.info(f"Valid blogs: {[f'{k}: {v}' for k, v in valid_blog_ids.items()]}")
            _logger.info(f"Valid posts: {[f'{k}: {v}' for k, v in valid_post_ids.items()]}")

            def sanitize_slug(slug, valid_ids):
                """
                Check if the slug ends with a numeric ID and if the name part matches
                the corresponding name in valid_ids. If so, strip the numeric ID.
                Otherwise, leave the slug unchanged.
                """
                _logger.info(f"Sanitize_slug called with slug='{slug}' and valid_ids='{valid_ids}'")
                
                if '-' in slug:
                    # Split the slug into the name part and the potential numeric ID
                    name_part, possible_id = slug.rsplit('-', 1)
                    _logger.info(f"Split slug into name_part='{name_part}' and possible_id='{possible_id}'")
                    
                    # Check if the last part is numeric
                    if possible_id.isdigit():
                        possible_id = int(possible_id)
                        _logger.info(f"Possible numeric ID detected: '{possible_id}'")
                        
                        # Validate against the valid IDs
                        if possible_id in valid_ids:
                            _logger.info(f"Numeric ID '{possible_id}' found in valid_ids")
                            
                            # Check if the name part matches the corresponding valid ID name
                            expected_name = valid_ids[possible_id]
                            title_case_name = name_part.replace('-', ' ').title()
                            _logger.info(f"Comparing name_part '{title_case_name}' with expected name '{expected_name}'")
                    
                            if title_case_name == expected_name:
                                _logger.info(f"Match found! Stripping numeric ID from slug: '{slug}' -> '{name_part}'")
                                return name_part
                            else:
                                _logger.warning(f"Name mismatch! '{title_case_name}' does not match '{expected_name}'. Keeping slug unchanged.")
                        else:
                            _logger.warning(f"Numeric ID '{possible_id}' not found in valid_ids. Keeping slug unchanged.")
                    else:
                        _logger.info(f"Last part '{possible_id}' is not numeric. Keeping slug unchanged.")
                else:
                    _logger.info(f"No '-' found in slug. Keeping slug unchanged.")

                # Return the original slug if no numeric ID to strip
                _logger.info(f"Returning slug unchanged: '{slug}'")
                return slug

            # Sanitize blog and post slugs
            blog_slug = sanitize_slug(blog, valid_blog_ids)
            post_slug = sanitize_slug(post, valid_post_ids)
            _logger.info(f"Sanitized slugs: blog='{blog_slug}', post='{post_slug}'")

            all_blogs = request.env['blog.blog'].search([])  # Search for all blogs
            all_blog_posts = request.env['blog.post'].search([])
            _logger.info("Listing all blogs:")
            for b in all_blogs:
                _logger.info(f"Blog ID={b.id}, Name='{b.name}', Slug='{b.slug if hasattr(b, 'slug') else 'N/A'}'")
            for bp in all_blog_posts:
                _logger.info(f"Blog ID={bp.id}, Name='{bp.name}', Slug='{bp.slug if hasattr(bp, 'slug') else 'N/A'}'")

            blog_title = blog_slug.replace('-', ' ')
            _logger.info(f"Transformed blog slug to name format: '{blog_title}'")
            blog_record = request.env['blog.blog'].search([('name', 'ilike', blog_slug)], limit=1)
            if not blog_record:
                _logger.warning(f"No Blog found with slug='{blog}'")
                return request.not_found()
            
            _logger.info(f"Found blog: ID={blog_record.id}, Name='{blog_record.name}', Slug='{blog_record.name}'")

            post_name = post_slug.replace('-', ' ')  # Convert 'sierra-tarahumara' to 'Sierra Tarahumara'
            _logger.info(f"Transformed post slug to name format: '{post_name}'")

            BlogPost = request.env['blog.post']
            date_begin, date_end = kwargs.get('date_begin'), kwargs.get('date_end')
           
            _logger.info(f"checking blogs.....{BlogPost.name}")
            
            # Search for the blog post using the slugs
            blog_post = BlogPost.search([
                ('blog_id.id', '=', blog_record.id),
                ('name', 'ilike', post_name),
            ], limit=1)
            
            # Log the search results
            if blog_post:
                _logger.info(f"BlogPost found: ID {blog_post.id}, title='{blog_post.name}'")
            else:
                _logger.warning(f"No BlogPost found for blog='{blog}', post='{post}'")
                return request.not_found()
            
            tag = None
            if tag_id:
                tag = request.env['blog.tag'].browse(int(tag_id))

            blog_url = QueryURL('', ['blog', 'tag'], blog=blog_post.blog_id, tag=tag, date_begin=None, date_end=None)
            _logger.info(f"Generated blog URL: {blog_url}")
            _logger.info(f"Rendering page for BlogPost ID={blog_post.id}, Title='{blog_post.name}'")
            # Render the blog post page with the found post
            return request.render("website_blog.blog_post_complete", {
                'tag': tag,
                'blog': blog_record,
                'blog_post': blog_post,
                'main_object': blog_post,
                'blogs': all_blogs,
                'blog_url': blog_url
            })

        except Exception as e:
            # Log any exception that occurs during request handling
            _logger.error(f"Error rendering blog post page for blog='{blog}', post='{post}': {str(e)}")
            return request.not_found()
    

    @http.route([
    '/blog',
    '/blog/page/<int:page>',
    '/blog/tag/<string:tag>',
    '/blog/tag/<string:tag>/page/<int:page>',
    '''/blog/<string:blog>''',
    '''/blog/<string:blog>/page/<int:page>''',
    '''/blog/<string:blog>/tag/<string:tag>''',
    '''/blog/<string:blog>/tag/<string:tag>/page/<int:page>''',
    ], type='http', auth="public", website=True, sitemap=True)
    def blog(self, blog=None, tag=None, page=1, search=None, **opt):
        """
        Render the blog page using the new URL format.
        """
        _logger.info(f"Received request for blog: blog='{blog}'")

        date_begin, date_end = opt.get('date_begin'), opt.get('date_end')

        try:
            # Fetch all valid blogs
            valid_blogs = request.env['blog.blog'].search([])
            Blog = request.env['blog.blog']
            blogs = tools.lazy(lambda: Blog.search(request.website.website_domain(), order="create_date asc, id asc"))

            # Create a dictionary of valid blog names mapped to their IDs
            valid_blog_ids = {blog_record.id: blog_record.name for blog_record in valid_blogs}

            _logger.info(f"Valid blogs: {[f'{k}: {v}' for k, v in valid_blog_ids.items()]}")

            # Sanitize blog slug only if provided
            blog_slug = None
            blog_record = None
            
            if blog:
                blog_slug = self.sanitize_slug(blog, valid_blog_ids)
                _logger.info(f"Sanitized slug for blog='{blog_slug}'")

                # Search for the blog using the slug
                blog_record = request.env['blog.blog'].search([('name', 'ilike', blog_slug)], limit=1)
                if not blog_record:
                    _logger.warning(f"No Blog found with slug='{blog}'")
                    return request.not_found()
                _logger.info(f"Found blog: ID={blog_record.id}, Name='{blog_record.name}'")

            # Prepare the QueryURL for navigation links
            blog_url = QueryURL('', ['blog', 'tag'], blog=blog_record, tag=tag, date_begin=date_begin, date_end=date_end)

            # Get blog posts related to the blog
            BlogPost = request.env['blog.post']
            domain = []
            if blog_record:
                domain.append(('blog_id', '=', blog_record.id))
            if tag:
                domain.append(('tag_ids', 'in', int(tag)))
            if date_begin and date_end:
                domain.append(('post_date', '>=', date_begin))
                domain.append(('post_date', '<=', date_end))

            blog_posts = BlogPost.search(domain, order="post_date desc")

            # Pass the `blog_record` instead of `blog` to `_prepare_blog_values`
            values = self._prepare_blog_values(
                blogs=valid_blogs,
                blog=blog_record,  # Pass the record
                tags=tag,
                page=page,
                search=search,
                **opt
            )

            values['blog_url'] = QueryURL(
                '/blog', ['blog', 'tag'], blog=blog_record, tag=tag, date_begin=date_begin, date_end=date_end, search=search
            )

            # Render the blog page
            return request.render("website_blog.blog_post_short", values)

        except Exception as e:
            _logger.error(f"Error rendering blog for blog='{blog}': {str(e)}")
            return request.not_found()


        # try:
        #     # Fetch all valid blogs
        #     valid_blogs = request.env['blog.blog'].search([])
        #     Blog = request.env['blog.blog']
        #     blogs = tools.lazy(lambda: Blog.search(request.website.website_domain(), order="create_date asc, id asc"))

        #     # Create a dictionary of valid blog names mapped to their IDs
        #     valid_blog_ids = {blog_record.id: blog_record.name for blog_record in valid_blogs}

        #     _logger.info(f"Valid blogs: {[f'{k}: {v}' for k, v in valid_blog_ids.items()]}")

        #     # Sanitize blog slug only if provided
        #     blog_slug = None
        #     if blog:
        #         blog_slug = self.sanitize_slug(blog, valid_blog_ids)
        #         _logger.info(f"Sanitized slug for blog='{blog_slug}'")

        #     # Search for the blog using the slug (if provided)
        #     blog_record = None
        #     if blog_slug:
        #         blog_record = request.env['blog.blog'].search([('name', 'ilike', blog_slug)], limit=1)
        #         if not blog_record:
        #             _logger.warning(f"No Blog found with slug='{blog}'")
        #             return request.not_found()
        #         _logger.info(f"Found blog: ID={blog_record.id}, Name='{blog_record.name}'")

        #     # Prepare the QueryURL for navigation links
        #     blog_url = QueryURL('', ['blog', 'tag'], blog=blog_record, tag=tag, date_begin=date_begin, date_end=date_end)

        #     # Get blog posts related to the blog
        #     BlogPost = request.env['blog.post']
        #     domain = []
        #     if blog_record:
        #         domain.append(('blog_id.id', '=', blog_record.id))
        #     if tag:
        #         domain.append(('tag_ids', 'in', int(tag)))
        #     if date_begin and date_end:
        #         domain.append(('post_date', '>=', date_begin))
        #         domain.append(('post_date', '<=', date_end))

        #     blog_posts = BlogPost.search(domain, order="post_date desc")

        #     values = self._prepare_blog_values(blogs=valid_blogs, blog=blog, tags=tag, page=page, search=search, **opt)

        #     values['blog_url'] = QueryURL('/blog', ['blog', 'tag'], blog=blog, tag=tag, date_begin=date_begin, date_end=date_end, search=search) 

        #     # Render the blog page
        #     return request.render("website_blog.blog_post_short", values)


        # except Exception as e:
        #     _logger.error(f"Error rendering blog for blog='{blog}': {str(e)}")
        #     return request.not_found()

    def sanitize_slug(self, slug, valid_ids):
        """
        Check if the slug ends with a numeric ID and if the name part matches
        the corresponding name in valid_ids. If so, strip the numeric ID.
        Otherwise, leave the slug unchanged.
        """
        if not slug:
            return None  # Handle None slug gracefully

        _logger.info(f"Sanitize_slug called with slug='{slug}' and valid_ids='{valid_ids}'")

        if '-' in slug:
            # Split the slug into the name part and the potential numeric ID
            name_part, possible_id = slug.rsplit('-', 1)
            _logger.info(f"Split slug into name_part='{name_part}' and possible_id='{possible_id}'")

            # Check if the last part is numeric
            if possible_id.isdigit():
                possible_id = int(possible_id)
                _logger.info(f"Possible numeric ID detected: '{possible_id}'")

                # Validate against the valid IDs
                if possible_id in valid_ids:
                    _logger.info(f"Numeric ID '{possible_id}' found in valid_ids")

                    # Check if the name part matches the corresponding valid ID name
                    expected_name = valid_ids[possible_id]
                    title_case_name = name_part.replace('-', ' ').title()
                    _logger.info(f"Comparing name_part '{title_case_name}' with expected name '{expected_name}'")

                    if title_case_name == expected_name:
                        _logger.info(f"Match found! Stripping numeric ID from slug: '{slug}' -> '{name_part}'")
                        return name_part
                    else:
                        _logger.warning(f"Name mismatch! '{title_case_name}' does not match '{expected_name}'. Keeping slug unchanged.")
                else:
                    _logger.warning(f"Numeric ID '{possible_id}' not found in valid_ids. Keeping slug unchanged.")
            else:
                _logger.info(f"Last part '{possible_id}' is not numeric. Keeping slug unchanged.")
        else:
            _logger.info(f"No '-' found in slug. Keeping slug unchanged.")

        # Return the original slug if no numeric ID to strip
        _logger.info(f"Returning slug unchanged: '{slug}'")
        return slug






    # @http.route([
    #     '/blog',
    #     '/blog/page/<int:page>',
    #     '/blog/tag/<string:tag>',
    #     '/blog/tag/<string:tag>/page/<int:page>',
    #     '''/blog/<string:blog>''',
    #     '''/blog/<string:blog>/page/<int:page>''',
    #     '''/blog/<string:blog>/tag/<string:tag>''',
    #     '''/blog/<string:blog>/tag/<string:tag>/page/<int:page>''',
    # ],  type='http', auth="public", website=True, sitemap=True)
    # def blog(self, blog=None, tag=None, date_begin=None, date_end=None, **kwargs):
    #     """
    #     Render the blog page using the new URL format.
    #     """
    #     _logger.info(f"Received request for blog: blog='{blog}'")

    #     try:
    #         # Fetch all valid blogs
    #         valid_blogs = request.env['blog.blog'].search([])

    #         # Create a dictionary of valid blog names mapped to their IDs
    #         valid_blog_ids = {blog_record.id: blog_record.name for blog_record in valid_blogs}

    #         _logger.info(f"Valid blogs: {[f'{k}: {v}' for k, v in valid_blog_ids.items()]}")

    #         def sanitize_slug(slug, valid_ids):
    #             """
    #             Check if the slug ends with a numeric ID and if the name part matches
    #             the corresponding name in valid_ids. If so, strip the numeric ID.
    #             Otherwise, leave the slug unchanged.
    #             """
    #             _logger.info(f"Sanitize_slug called with slug='{slug}' and valid_ids='{valid_ids}'")

    #             if '-' in slug:
    #                 # Split the slug into the name part and the potential numeric ID
    #                 name_part, possible_id = slug.rsplit('-', 1)
    #                 _logger.info(f"Split slug into name_part='{name_part}' and possible_id='{possible_id}'")

    #                 # Check if the last part is numeric
    #                 if possible_id.isdigit():
    #                     possible_id = int(possible_id)
    #                     _logger.info(f"Possible numeric ID detected: '{possible_id}'")

    #                     # Validate against the valid IDs
    #                     if possible_id in valid_ids:
    #                         _logger.info(f"Numeric ID '{possible_id}' found in valid_ids")

    #                         # Check if the name part matches the corresponding valid ID name
    #                         expected_name = valid_ids[possible_id]
    #                         title_case_name = name_part.replace('-', ' ').title()
    #                         _logger.info(f"Comparing name_part '{title_case_name}' with expected name '{expected_name}'")

    #                         if title_case_name == expected_name:
    #                             _logger.info(f"Match found! Stripping numeric ID from slug: '{slug}' -> '{name_part}'")
    #                             return name_part
    #                         else:
    #                             _logger.warning(f"Name mismatch! '{title_case_name}' does not match '{expected_name}'. Keeping slug unchanged.")
    #                     else:
    #                         _logger.warning(f"Numeric ID '{possible_id}' not found in valid_ids. Keeping slug unchanged.")
    #                 else:
    #                     _logger.info(f"Last part '{possible_id}' is not numeric. Keeping slug unchanged.")
    #             else:
    #                 _logger.info(f"No '-' found in slug. Keeping slug unchanged.")

    #             # Return the original slug if no numeric ID to strip
    #             _logger.info(f"Returning slug unchanged: '{slug}'")
    #             return slug

    #         # Sanitize blog slug
    #         blog_slug = sanitize_slug(blog, valid_blog_ids)
    #         _logger.info(f"Sanitized slug for blog='{blog_slug}'")

    #         # Search for the blog using the slug
    #         blog_record = request.env['blog.blog'].search([('name', 'ilike', blog_slug)], limit=1)
    #         if not blog_record:
    #             _logger.warning(f"No Blog found with slug='{blog}'")
    #             return request.not_found()

    #         _logger.info(f"Found blog: ID={blog_record.id}, Name='{blog_record.name}'")

    #         # Prepare the QueryURL for navigation links
    #         blog_url = QueryURL('', ['blog', 'tag'], blog=blog_record, tag=tag, date_begin=date_begin, date_end=date_end)

    #         # Get blog posts related to the blog
    #         BlogPost = request.env['blog.post']
    #         domain = [('blog_id', '=', blog_record.id)]
    #         if tag:
    #             domain.append(('tag_ids', 'in', int(tag)))
    #         if date_begin and date_end:
    #             domain.append(('post_date', '>=', date_begin))
    #             domain.append(('post_date', '<=', date_end))

    #         blog_posts = BlogPost.search(domain, order="post_date desc")

    #         # Render the blog page
    #         return request.render("website_blog.blog_post_complete", {
    #             'blog': blog_record,
    #             'blogs': valid_blogs,
    #             'blog_posts': blog_posts,
    #             'blog_url': blog_url,
    #             'tag': tag,
    #         })

    #     except Exception as e:
    #         _logger.error(f"Error rendering blog page for blog='{blog}': {str(e)}")
    #         return request.not_found()
