# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    houzz_product_description = fields.Html()

