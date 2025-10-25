# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class xx_services(models.Model):
    _name = 'booking.services'
    
    _rec_name = 'name'
    
    name = fields.Char(string="الاسم",required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

    active = fields.Boolean(default=True,string="تفعيل")
    _sql_constraints = [
        ("service_kind_unique",
         "UNIQUE(name)",
         "تنبيه .. الخدمة تم اضافتة مسبقا لا يمكن الاستمرار"),
        ]
     
    
class xx_department(models.Model):
    _name = 'booking.departments'
    
    _rec_name = 'name'
    
    name = fields.Char(string="الاسم",required=True)
    dept_price = fields.Float(string="مبلغ الايجار",required=True)
    product_id = fields.Many2one('product.product',domain=[('type','!=','storable')], string="تحديد الصنف الخدمي", reuired=True)
    tax_ids = fields.Many2one('account.tax',  string='نوع الضريبة', domain=[('type_tax_use','=','sale')],help="Taxes that apply on the base amount")
    max_discount_percentage = fields.Float(string="نسبة الخصم %")
    active = fields.Boolean(default=True,string="تفعيل")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

    lines = fields.One2many('booking.departments.lines', 'header_id',ondelete="cascade", required=True, )

    _sql_constraints = [
        ("service_kind_unique",
         "UNIQUE(name)",
         "تنبيه .. القسم تم اضافتة مسبقا لا يمكن الاستمرار"),
        ]
    
    @api.constrains('product_id','name')
    def create_product_service(self):
        for rec in self:
            if not rec.product_id:
                prod = rec.create_product(rec.name)
                if prod:
                    rec.write({'product_id': prod.id})
        
    def create_product(self,service_name):
       
            if service_name:
                prod = self.env['product.product'].search([('name','=', service_name)])
                if not prod:
                    prod_tmp = self.env['product.template'].create({'name': service_name,
                                                                   'type': 'service',
                                                                   'branch_required': True,
                                                                   'branch_id': False,
                                                                  
                                                                   })
                    prod = self.env['product.product'].search([('product_tmpl_id', '=', prod_tmp.id)])
                if prod:
                    return prod
       
class xx_department_lines(models.Model):
    _name = 'booking.departments.lines'
    
    product_id = fields.Many2one('product.product', string="الخدمة", required=True,domain=[('booking_flag','=',True)])
    person_count = fields.Float(string="السعة الاستيعابية" )

    header_id = fields.Many2one('booking.departments',ondelete="cascade")


    _sql_constraints = [
        ("service_kind_unique",
         "UNIQUE(product_id,header_id)",
         "تنبيه .. الخدمة تم اضافتة مسبقا لا يمكن الاستمرار"),
    ]
 