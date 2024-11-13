from odoo import http
from odoo.addons.website_blog.controllers.main import WebsiteBlog
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
import logging
_logger = logging.getLogger(__name__)

class CustomWebsiteBlog(WebsiteBlog):
    @http.route(['/blog/<string:blog>/<string:post>'], type='http', auth="public", website=True)
    def blog_post(self, blog, post, tag_id=None, page=1, enable_editor=None, **kwargs):
        """
        Render the blog post page using the new URL format.
        Log each step to monitor the routing and search process.
        """
        # _logger.info(f"Received request for blog post: blog='{blog}', post='{post}")
        
        try:

            def strip_numeric_id(slug):
                parts = slug.rsplit('-', 1)
                # Check if the last part is a number (indicating an ID)
                if len(parts) > 1 and parts[-1].isdigit():
                    _logger.info(f"Detected numeric ID in slug '{slug}', stripping it out.")
                    return parts[0]  # Return slug without numeric ID
                else:
                    _logger.info(f"No numeric ID detected in slug '{slug}', keeping as is.")
                    return slug 

            # blog_slug = blog.rsplit('-', 1)[0]  # Remove anything after the last '-'
            # post_slug = post.rsplit('-', 1)[0]  # Remove anything after the last '-'
            blog_slug = strip_numeric_id(blog)  
            post_slug = strip_numeric_id(post)
            # _logger.info(f"Sanitized slugs: blog='{blog_slug}', post='{post_slug}'")

            all_blogs = request.env['blog.blog'].search([])  # Search for all blogs
            all_blog_posts = request.env['blog.post'].search([])
            # _logger.info("Listing all blogs:")
            # for b in all_blogs:
            #     _logger.info(f"Blog ID={b.id}, Name='{b.name}', Slug='{b.slug if hasattr(b, 'slug') else 'N/A'}'")
            # for bp in all_blog_posts:
            #     _logger.info(f"Blog ID={bp.id}, Name='{bp.name}', Slug='{bp.slug if hasattr(bp, 'slug') else 'N/A'}'")

            blog_title = blog_slug.replace('-', ' ').title()
            # _logger.info(f"Transformed blog slug to name format: '{blog_title}'")
            blog_record = request.env['blog.blog'].search([('name', '=', blog_title)], limit=1)
            if not blog_record:
                _logger.warning(f"No Blog found with slug='{blog}'")
                return request.not_found()
            
            # _logger.info(f"Found blog: ID={blog_record.id}, Name='{blog_record.name}', Slug='{blog_record.name}'")

            post_name = post_slug.replace('-', ' ').title()  # Convert 'sierra-tarahumara' to 'Sierra Tarahumara'
            # _logger.info(f"Transformed post slug to name format: '{post_name}'")

            BlogPost = request.env['blog.post']
            date_begin, date_end = kwargs.get('date_begin'), kwargs.get('date_end')
           
            # _logger.info(f"checking blogs.....{BlogPost.name}")

            # search_criteria = [('blog_id.name', '=', blog), ('name', '=', post)]
            # _logger.info(f"Searching for blog post with criteria: {search_criteria}")
            
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
            # _logger.info(f"Generated blog URL: {blog_url}")
            # _logger.info(f"Rendering page for BlogPost ID={blog_post.id}, Title='{blog_post.name}'")
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