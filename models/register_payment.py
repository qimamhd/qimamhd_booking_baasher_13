# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class xx_register_payment(models.Model):
    _inherit = 'account.payment'

    booking_id = fields.Many2one('hotel.master', readonly=True, string="رقم الحجز",copy=False)

    # @api.model
    # def create(self, vals ):
    #     active_ids = self._context.get('active_ids', []) or []
    #     for record in self.env['hotel.master'].browse(active_ids):
    #         if vals.get("booking_id"):
    #             print(vals.get("amount"))
    #             record.update({'advance_amount': vals.get("amount")})
    #     return super(xx_register_payment, self).create(vals)
