import logging

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def check_no_capitals(name):
    """Raise if the given name contains any uppercase character.

    Shared by blog.blog and blog.post since both enforce the same
    lowercase-only naming convention (required for the hyphenated URL slugs).

    :param str name: text to validate
    :raises UserError: if name contains an uppercase letter
    """
    if name and any(char.isupper() for char in name):
        raise UserError(_("The Blog or blog Title cannot contain capital letters!"))


class BlogBlogNaming(models.Model):
    _inherit = 'blog.blog'

    @api.model_create_multi
    def create(self, vals_list):
        """Validate naming convention (no capitals) before delegating to super.

        :param list[dict] vals_list: create values for each blog.blog
        :return: created blog.blog recordset
        """
        _logger.info("Creating %s blog(s)", len(vals_list))
        for vals in vals_list:
            check_no_capitals(vals.get('name'))
        return super().create(vals_list)

    def write(self, vals):
        """Validate naming convention (no capitals) on rename before delegating to super.

        :param dict vals: write values
        """
        check_no_capitals(vals.get('name'))
        return super().write(vals)