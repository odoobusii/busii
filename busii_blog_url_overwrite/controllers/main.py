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

            # def strip_numeric_id(slug):
            #     parts = slug.rsplit('-', 1)
            #     # Check if the last part is a number (indicating an ID)
            #     if len(parts) > 1 and parts[-1].isdigit():
            #         _logger.info(f"Detected numeric ID in slug '{slug}', stripping it out.")
            #         return parts[0]  # Return slug without numeric ID
            #     else:
            #         _logger.info(f"No numeric ID detected in slug '{slug}', keeping as is.")
            #         return slug 
            # def strip_numeric_id(slug, valid_names):
            #     """
            #     Strip numeric IDs only if they match the known IDs for old URLs.
            #     Otherwise, keep the slug as is.
            #     """
            #     # if '-' in slug:
            #     #     parts = slug.rsplit('-', 1)
            #     #     if parts[-1].isdigit():
            #     #         numeric_id = int(parts[-1])
            #     #         # Check if the numeric ID exists in the list of valid IDs
            #     #         if numeric_id in valid_ids:
            #     #             _logger.info(f"Stripping numeric ID '{numeric_id}' from slug '{slug}'")
            #     #             return parts[0]  # Remove the numeric ID
            #     # # If no numeric ID or not a valid ID, return the original slug
            #     # _logger.info(f"No numeric ID to strip for slug '{slug}'")
            #     # return slug
            #     if '-' in slug:
            #         parts = slug.rsplit('-', 1)
            #         if parts[-1].isdigit():
            #             numeric_id = int(parts[-1])
            #             # Check if the numeric ID exists in the list of valid IDs
            #             if slug in valid_names:
            #                 _logger.info(f"Slug '{slug}' matches a valid name, keeping as is")
            #                 return slug
            #             if numeric_id in valid_ids:
            #                 _logger.info(f"Stripping numeric ID '{numeric_id}' from slug '{slug}'")
            #                 return parts[0]  # Remove the numeric ID
            #         # Check if the slug matches a valid name, including its numeric part
                    
            #     # If no numeric ID or not a valid ID, return the original slug
            #     _logger.info(f"No numeric ID to strip for slug '{slug}'")
            #     return slug

            # blog_slug = blog.rsplit('-', 1)[0]  # Remove anything after the last '-'
            # post_slug = post.rsplit('-', 1)[0]  # Remove anything after the last '-'
            # valid_blog_ids = request.env['blog.blog'].search([]).mapped('id')  # List of valid blog IDs
            # valid_blog_names = request.env['blog.blog'].search([])

            # valid_post_ids = request.env['blog.post'].search([]).mapped('id')  # List of valid post IDs
            # valid_post_names = request.env['blog.post'].search([])
            # _logger.info("Listing all valid blogs:")
            # for b in valid_blog_names:
            #     _logger.info(f"Blog name: {b.name.replace(" ", "-").lower()}, blog id: {b.id}'")
            # for bp in valid_post_names:
            #     _logger.info(f"Blog poat name: {bp.name.replace(" ", "-").lower()}, post id: {bp.id}'")
            # def sanitize_slug(slug, valid_ids):
            #     """
            #     Check if the slug ends with a numeric ID and if the name part matches
            #     the corresponding name in valid_ids. If so, strip the numeric ID.
            #     """
            #     _logger.info(f"Sanitize_slug called with slug='{slug}' and valid_ids='{valid_ids}'")
            #     if '-' in slug:
            #         # Split the slug into name and potential numeric ID
            #         name_part, possible_id = slug.rsplit('-', 1)
            #         _logger.info(f"Split slug into name_part='{name_part}' and possible_id='{possible_id}'")
            #         if possible_id.isdigit():
            #             possible_id = int(possible_id)
            #             _logger.info(f"Possible numeric ID detected: '{possible_id}'")
            #             # Check if the ID exists and if the name matches
            #             if possible_id in valid_ids and name_part.replace('-', ' ').title() in valid_ids[possible_id]:
            #                 _logger.info(f"Stripping numeric ID '{possible_id}' from slug '{slug}'")
            #                 return name_part  # Return the name without the numeric ID
            #     return slug  # Return the original slug if no match or ID
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

            # blog_slug = strip_numeric_id(blog, valid_blog_names)  
            # post_slug = strip_numeric_id(post, valid_post_names)
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

            blog_title = blog_slug.replace('-', ' ').title()
            _logger.info(f"Transformed blog slug to name format: '{blog_title}'")
            blog_record = request.env['blog.blog'].search([('name', '=', blog_slug)], limit=1)
            if not blog_record:
                _logger.warning(f"No Blog found with slug='{blog}'")
                return request.not_found()
            
            _logger.info(f"Found blog: ID={blog_record.id}, Name='{blog_record.name}', Slug='{blog_record.name}'")

            post_name = post_slug.replace('-', ' ').title()  # Convert 'sierra-tarahumara' to 'Sierra Tarahumara'
            _logger.info(f"Transformed post slug to name format: '{post_name}'")

            BlogPost = request.env['blog.post']
            date_begin, date_end = kwargs.get('date_begin'), kwargs.get('date_end')
           
            _logger.info(f"checking blogs.....{BlogPost.name}")

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