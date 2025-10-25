# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class xx_categorys_in_product(models.Model):
    _inherit = 'product.template'

    booking_flag = fields.Boolean(string="خدمة قاعات ")
