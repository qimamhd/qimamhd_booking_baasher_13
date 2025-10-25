# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class add_cost_invoice(models.Model):
    _inherit = 'res.users'
    
    max_discount_percentage = fields.Float(string="نسبه الخصم المسموح")
