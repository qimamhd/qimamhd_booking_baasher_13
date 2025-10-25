from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from num2words import num2words
from datetime import timedelta
from datetime import datetime,time
from hijri_converter import convert


class xx_account_move(models.Model):
    _inherit = 'account.move'

    booking_id = fields.Many2one('hotel.master', string="رقم الحجز", readony=True, copy=False)
    partner_mobile = fields.Char(string="رقم الجوال")
    
    def unlink(self):
        for rec in self:
            if rec.booking_id:
                 rec.booking_id.write({'state': 'booking_done'})
        return super(xx_account_move, self).unlink()

class xx_hotel_master(models.Model):
    _name = 'hotel.master'
    _inherit = ['mail.thread']
    
    _rec_name="partner_id"

    seq_number = fields.Integer(compute="get_sequence_number")



    seq = fields.Integer(
        string='التسلسل',
        copy=False,
        
        default=lambda self: self._get_sequence(),)
    
    order_date = fields.Date(required=True, string="تاريخ العملية",default=fields.Date.today)
    order_from_higri_date = fields.Char(required=True, string="من الهجري")
    order_to_higri_date = fields.Char(required=True, string="الى الهجري")
    booking_start_date = fields.Date(string=" من تاريخ")
    booking_end_date = fields.Date(string=" الى تاريخ")
    partner_id = fields.Many2one('res.partner',required=True, string="العميل")
    partner_nationality = fields.Many2one('res.country', string="الجنسية")
    partner_mobile1 = fields.Char(string="جوال1")
    partner_mobile2 = fields.Char(string="جوال2")
    partner_identifier = fields.Char(string="الهوية")
    partner_identifier_source = fields.Many2one('res.country.state',string="مصدر الهوية")
    partner_identifier_date = fields.Date(string="تاريخ الاصدار")
    advance_amount = fields.Float(string="المبلغ المدفوع مقدما",readonly=True,copy=False)
    remaining_amount = fields.Float(string="المبلغ المتبقي",readonly=True,copy=False,compute="_calc_remain_amount")
    booking_day = fields.Char(string="اليوم",compute="_get_day_name")
    booking_night = fields.Char(string="الليلة",compute="_get_night_name")
    service_id = fields.Many2one('booking.services',string="الخدمة",required=True)
    department_id = fields.Many2one('booking.departments',string="القسم",required=True)
    department_price = fields.Float(string="مبلغ الايجار",required=True)
    dept_tax_ids = fields.Many2one('account.tax', string='نوع الضريبة', domain=[('type_tax_use','=','sale')],help="Taxes that apply on the base amount")
    dept_discount_total = fields.Float(store=True,compute="_calc_department_price", string="مبلغ الخصم")
    dept_discount_perc = fields.Float(store=True,compute="_calc_department_price",string="نسبة الخصم المحتسبة")
    dept_base_amount = fields.Float(store=True,compute="_calc_department_price")
    dept_price_after_discount = fields.Float(store=True,compute="_calc_department_price")
    dept_discount_type = fields.Selection([('amount', 'مبلغ'), ('percentage', 'نسبة'),('discount_from_total','الخصم من الاجمالي')], string="نوع الخصم",
                                     default='percentage') 
    dept_discount = fields.Float( string="نسبة الخصم")
    dept_after_discount_with_tax = fields.Float( string="الاجمالي بعد الخصم شامل الضريبة",store=True,compute="_calc_department_price")
    service_price = fields.Float(string="الاجمالي",store=True,compute="_cal_tot_price")
    service_discount_total = fields.Float(store=True,compute="_cal_tot_price")
    service_discount_perc = fields.Float(store=True,compute="_cal_tot_price")
    service_base_amount = fields.Float(store=True,compute="_cal_tot_price")
    service_price_after_discount = fields.Float(store=True,compute="_cal_tot_price")
    service_after_discount_with_tax = fields.Float( string="الاجمالي بعد الخصم شامل الضريبة",store=True,compute="_cal_tot_price")
    discount_type = fields.Selection([('amount', 'مبلغ'), ('percentage', 'نسبة'),('discount_from_total','الخصم من الاجمالي')], 
                                             string="نوع الخصم",  default='percentage') 
    discount = fields.Float( string="نسبة الخصم")
    finish_booking_date = fields.Date(string="انتهاء الحجز")
    state = fields.Selection([('initial_booking','حجز مبدئ'),('booking_done','تم الحجز'),
                              ('finish_booking','انتهاء الحجز'),('cancel_booking','حجز ملغي')],
                             default='initial_booking',string="حالة الحجز")
    desc = fields.Char(string="الوصف")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    branch_id = fields.Many2one('custom.branches', string='الفرع', readonly=True, copy=False,
                                default=lambda self: self.env.user.branch_id.id)
    user_id = fields.Many2one(
        'res.users', string='مدخل البيانات',  
        required=True, default=lambda self: self.env.uid)
    lines = fields.One2many('hotel.lines', 'header_id',ondelete="cascade", required=True, )
    service_lines = fields.One2many('hotel.service.lines', 'header_id',ondelete="cascade", required=True, )
    service_extend_lines = fields.One2many('hotel.service.extend', 'extend_header_id',ondelete="cascade", required=True, )
    lines_payment = fields.One2many('booking.register.payment', 'header_id', required=True,
                                     ondelete="cascade",copy=False, domain = [('state','!=','cancel')])
    create_invoice_manually_id = fields.Many2one('account.move',readonly=True, copy=False,)
   
   
    def _get_sequence(self):
        # print(self.env.context.get('report_name', False))
        branch_id = self.env.user.branch_id.id
        if branch_id:
       
            sql_query = "select max(COALESCE(seq,0)) as seq from hotel_master where branch_id=%s" % (branch_id)


            self.env.cr.execute(sql_query)
            seq = self.env.cr.fetchone()
            x = seq[0]
            if x:
                x = x + 1
                return (x)
            else:
                x = 1
                return (x)
   
    @api.depends('seq')
    def get_sequence_number(self):
        for rec in self:
            rec.seq_number = rec.seq

    
    # @api.onchange('order_higri_date')
    # def get_gregorian_date(self):
    #     for rec in self:
    #         try:
    #             if rec.order_higri_date:
    #                 check_date = datetime.strptime( rec.order_higri_date, '%Y-%m-%d').date()
                    
    #                 to_gregorian_date = convert.Hijri(check_date.year, check_date.month,check_date.day).to_gregorian()
    #                 print("to_gregorian_date",to_gregorian_date)
    #                 rec.update({'booking_start_date': to_gregorian_date})
                   
    #         except ValueError as ve2:
    #             raise ValidationError(ve2)   
              
                 
                 
    @api.onchange('booking_start_date')
    def get_hijri_start_date(self):
        for rec in self:
            print("--------*************-----")
            if rec.booking_start_date:
                hijri_date = convert.Gregorian(rec.booking_start_date.year, rec.booking_start_date.month, rec.booking_start_date.day).to_hijri()
                print("-------------",hijri_date)
                
                rec.update({'order_from_higri_date':  rec.return_format_hijri_month_name(hijri_date)})
            else:
                rec.order_from_higri_date=False
                
    @api.onchange('booking_end_date')
    def get_hijri_end_date(self):
        for rec in self:
            print("--------*************-----")
            if rec.booking_end_date:
                hijri_date = convert.Gregorian(rec.booking_end_date.year, rec.booking_end_date.month, rec.booking_end_date.day).to_hijri()
                print("-------------",hijri_date)
                
                rec.update({'order_to_higri_date': rec.return_format_hijri_month_name(hijri_date)})
            else:
                  
                rec.order_to_higri_date=False
    def return_format_hijri_month_name(self,hijri_date):
        day_name=""
        print("month_name",hijri_date.month_name().upper())
        if hijri_date.month_name().upper() == 'MUHARRAM':
            day_name =str(hijri_date.day)  + '-محرم-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'SAFAR':
             day_name =str(hijri_date.day)  + '-صفر-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'RABI’ AL-AWWAL':
             day_name =str(hijri_date.day)  + '-ربيع الأول-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'RABI’ AL-THANI':
             day_name =str(hijri_date.day)  + '-ربيع الثاني-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'JUMADA AL-ULA':
             day_name =str(hijri_date.day)  + '-جمادى الاول-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'JUMADA AL-AKHIRAH':
             day_name =str(hijri_date.day)  + '-جمادى الثاني-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'RAJAB':
             day_name =str(hijri_date.day)  + '-رجب-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'SHA’BAN':
             day_name =str(hijri_date.day)  + '-شعبان-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'RAMADHAN':
             day_name =str(hijri_date.day)  + '-رمضان-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'SHAWWAL':
             day_name =str(hijri_date.day)  + '-شوال-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'DHU AL-QI’DAH':
             day_name =str(hijri_date.day)  + '-ذي القعدة-' + str(hijri_date.year)
        elif hijri_date.month_name().upper() == 'DHU AL-HIJJAH':
             day_name =str(hijri_date.day) + '-ذي الحجة-' + str(hijri_date.year) 
        else:
            day_name =  hijri_date 
        
        return day_name
             
             
             
             
             
             
    # @api.onchange('booking_end_date','booking_start_date')
    # def get_hijri_end_date(self):
    #     for rec in self:
    #         if rec.booking_end_date != rec.booking_start_date:
    #             hijri_date1 = ""
    #             hijri_date2 = ""
    #             if  rec.booking_start_date:
    #                 hijri_date1 = convert.Gregorian(rec.booking_start_date.year, rec.booking_start_date.month, rec.booking_start_date.day).to_hijri()
                 
    #             if  rec.booking_end_date:
    #                 hijri_date2 = convert.Gregorian(rec.booking_end_date.year, rec.booking_end_date.month, rec.booking_end_date.day).to_hijri()
    #             if hijri_date1 and hijri_date2:
    #                 rec.update({'order_from_higri_date':hijri_date1})
    #                 rec.update({'order_to_higri_date':hijri_date1})
    #             elif hijri_date1 and not hijri_date2:
    #                 rec.update({'order_from_higri_date': hijri_date1 })
    #             elif not hijri_date1 and  hijri_date2:
    #                 rec.update({'order_to_higri_date': hijri_date2 })
    #         if rec.booking_end_date == rec.booking_start_date:
    #             if  rec.booking_start_date:
    #                 hijri_date1 = convert.Gregorian(rec.booking_start_date.year, rec.booking_start_date.month, rec.booking_start_date.day).to_hijri()
    #                 rec.update({'order_from_higri_date': hijri_date1 })
                    
    @api.depends('lines_payment','advance_amount')
    def _calc_remain_amount(self):
        for rec in self:
            extend_Service_amt = sum(l.price_after_discount_with_tax for l in rec.service_extend_lines.service_add_lines)

            payment_amount = sum(l.payment_amount for l in rec.lines_payment.filtered(lambda x:x.state == 'posted'))
            rec.remaining_amount = (rec.service_after_discount_with_tax + extend_Service_amt) - payment_amount
            
            
    @api.depends('booking_start_date')
    def _get_day_name(self):
        for rec in self:
            if self.booking_start_date:
                day_name = self.booking_start_date.strftime("%A")
                if day_name.upper() == 'SATURDAY':
                    rec.booking_day  = 'السبت'
                elif day_name.upper() == 'SUNDAY':
                    rec.booking_day  = 'الاحد'
                elif day_name.upper() == 'MONDAY':
                    rec.booking_day  = 'الاثنين'
                elif day_name.upper() == 'TUESDAY':
                    rec.booking_day  = 'الثلاثاء'
                elif day_name.upper() == 'WEDNESDAY':
                    rec.booking_day  = 'الاربعاء'
                elif day_name.upper() == 'THURSDAY':
                    rec.booking_day  = 'الخميس'
                elif day_name.upper() == 'FRIDAY':
                    rec.booking_day  = 'الجمعة'
                else:
                    rec.booking_day = day_name
                    
            else:
                 rec.booking_day = False
    
    @api.depends('booking_start_date')
    def _get_night_name(self):
        for rec in self:
            if self.booking_start_date:
                next_date = self.booking_start_date + timedelta(days = 1) 
                day_name  =  next_date.strftime("%A")
                
                if day_name.upper() == 'SATURDAY':
                    rec.booking_night  = 'السبت'
                elif day_name.upper() == 'SUNDAY':
                    rec.booking_night  = 'الاحد'
                elif day_name.upper() == 'MONDAY':
                    rec.booking_night  = 'الاثنين'
                elif day_name.upper() == 'TUESDAY':
                    rec.booking_night  = 'الثلاثاء'
                elif day_name.upper() == 'WEDNESDAY':
                    rec.booking_night  = 'الاربعاء'
                elif day_name.upper() == 'THURSDAY':
                    rec.booking_night  = 'الخميس'
                elif day_name.upper() == 'FRIDAY':
                    rec.booking_night  = 'الجمعة'
                else:
                    rec.booking_night = day_name
            else:
                rec.booking_night =False
                
    def unlink(self):
        for rec in self:
            if self.user_has_groups('qimamhd_booking_13.group_allow_cancel_wo'):
                if rec.create_invoice_manually_id:
                    raise ValidationError("لا يمكن الحذف لوجود فاتورة")  
                if  rec.lines_payment:
                    raise ValidationError("لا يمكن الحذف لوجود مدفوعات") 
             
            else:
                raise ValidationError("لا توجد لديك صلاحية حذف الحجز")
        return super(xx_hotel_master, self).unlink()
    def cancel_booking(self):
        for rec in self:
            if self.user_has_groups('qimamhd_booking_13.group_allow_cancel_wo'):
              rec.write({'state':'cancel_booking'})   
            else:
                raise ValidationError("لا توجد لديك صلاحية الغاء الحجز")
    def un_confirm_btn(self):
         for rec in self:
            if rec.create_invoice_manually_id:
                   raise ValidationError(" لايمكن الغاء الاعتماد لوجود فاتورة")    
            
            rec.write({'state':'initial_booking'})   
            
                
    def confirm_btn(self):
        for rec in self:
            if rec.department_id or rec.service_lines  :
                rec.write({'state':'booking_done'})    
            else:
                raise ValidationError("بيانات الحجز غير مكتملة")
    def complete_btn(self):
        for rec in self:
            if  rec.create_invoice_manually_id :
                rec.write({'state':'finish_booking'})    
            else:
                raise ValidationError("لم يتم انشاء فاتورة مبيعات للعميل")      
 
    def action_extend_services(self):
        service_extend = self.env['hotel.service.extend'].search([('extend_header_id','=',self.id)])
        
        if not service_extend:
             service_extend = self.env['hotel.service.extend'].create( 
                                                                      
                        {'partner_id': self.partner_id.id,
                         'order_date':datetime.today(),
                        'extend_header_id': self.id,
                        'service_id': self.service_id.id,
                        'department_id': self.department_id.id,
                        'booking_start_date': self.booking_start_date,
                        'booking_end_date': self.booking_end_date,
                                    })
        if service_extend:
            action = self.env.ref('qimamhd_booking_13.action_hotel_extend_view')
            result = action.read()[0]
            result.pop('id', None)
            result['context'] = {}
            result['domain'] = [('id', '=', service_extend.id)]
            if service_extend:
                res = self.env.ref('qimamhd_booking_13.hotel_extend_view', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = service_extend.id or False

            return result
    
    def register_payment(self):
         advanced_amount = 0
         remaining_amount = 0
         for rec in self:
             payment = self.env['booking.register.payment'].search([('header_id', '=', rec.id),('state', '!=', 'cancel')])
             print(payment)

             for line in payment:
                 advanced_amount = advanced_amount + line.payment_amount
             extend_Service_amt = sum(l.price_after_discount_with_tax for l in rec.service_extend_lines.service_add_lines)

            
             if advanced_amount >= (rec.service_after_discount_with_tax + extend_Service_amt):
                 raise ValidationError(
                     "اكتمل الدفع للحجز .. لا يمكن انشاء مفوعات جديدة ")

             payment = self.env['booking.register.payment'].search([('header_id', '=', rec.id),('state', '!=', 'cancel')])
             advanced_amount = sum(l.payment_amount for l in payment)
             remaining_amount = (rec.service_after_discount_with_tax+extend_Service_amt) - advanced_amount

             return {
                 'name': _('Register Payment'),
                 'view_mode': 'form',
                 'res_model': 'booking.register.payment',
                 'view_id': self.env.ref('qimamhd_booking_13.booking_payment_view').id,
                 'type': 'ir.actions.act_window',
                 'context': {'default_invoice_amount': (self.service_after_discount_with_tax +extend_Service_amt), 'default_advanced_amount': advanced_amount,
                                      'default_remaining_amount': remaining_amount,'default_branch_id': rec.branch_id.id,

                                        'default_header_id': rec.id,'default_payment_amount': remaining_amount,
                                     },
                 'target': 'current'
             }
  
    def create_invoice(self):
        for rec in self:

            inv = self.env['account.move'].search([('booking_id','=', rec.id)])
            if inv:
                raise ValidationError(
                    "لا يمكن انشاء فاتورة مبيعات لوجود فاتورة مسبقة[%s] لنفس الحجز" % inv.name)
                
            extend_Service_amt = sum(l.price_after_discount_with_tax for l in rec.service_extend_lines.service_add_lines)
            payment_all = sum(l.payment_amount for l in rec.lines_payment.filtered(lambda x: x.state== 'posted'))
            print("payment_all",payment_all)
            print("extend_Service_amt",extend_Service_amt)
            print("service_after_discount_with_tax",rec.service_after_discount_with_tax)
            
            if payment_all != (extend_Service_amt + rec.service_after_discount_with_tax):
                  raise ValidationError(
                       "تنبيه .. لا يمكن انشاء الفاتورة قيمة الحجز مع قيمة الخدمات الملحقة لا يساوي الدفعات " )
            
            if not rec.department_id.product_id:
                rec.department_id.create_product_service()
                
            if not rec.department_id.product_id:
                raise ValidationError(
                            "يجب تحديد الصنف الخدمي في تهيئة الباقات - (%s) " % rec.department_id.name)
                    
            inv_line_ids =[]
            sale_line_ids = {}
            select = []
            car_film_name =""
            for line in rec.lines:
                car_film_name = str(car_film_name) + " * "
                if len(select) == 0:
                    car_film_name = str(car_film_name) + str(line.product_id.name) 
                    
                    select.append(line.product_id.name)
                elif line.product_id.name not in select:
                    car_film_name = str(car_film_name) + str(line.product_id.name)  
                    
                    select.append(line.product_id.name)
                    

                car_film_name = " ( " + car_film_name + " )"
               
            line_ids = {
                'product_id': rec.department_id.product_id.id,
                'name': rec.department_id.product_id.name + " - " + car_film_name,
                'quantity': 1,
                'product_uom_id': rec.department_id.product_id.uom_id.id,
                    
                'discount': rec.dept_discount_perc ,
                'price_unit': rec.department_price,
                'tax_ids': [(6, 0, rec.dept_tax_ids.ids)] if rec.dept_tax_ids else False,

                # 'tax_id': product_mislead_id.taxes_id.id,
                    'company_id': rec.company_id.id,
                    'company_currency_id': rec.env.company.currency_id.id,

            }
            inv_line_ids.append((0,0,line_ids))

            
            for line_sale in rec.service_lines:
                  
                sale_line_ids ={
                    'product_id': line_sale.product_id.id,
                    'name': line_sale.name,
                    'quantity': line_sale.qty,
                    'product_uom_id': line_sale.product_id.uom_id.id,
                    'discount': line_sale.discount_perc,
                    'price_unit': line_sale.price,
                    'company_id': rec.company_id.id,
                        'tax_ids': [(6, 0, line_sale.tax_ids.ids)] if line_sale.tax_ids.ids else False ,

                    'company_currency_id': rec.env.company.currency_id.id,

                        }
                inv_line_ids.append((0, 0, sale_line_ids))
            for line_extend in rec.service_extend_lines.service_add_lines:
                line_extend_ids ={
                    'product_id': line_extend.product_id.id,
                    'name': line_extend.name,
                    'quantity': line_extend.qty,
                    'product_uom_id': line_extend.product_id.uom_id.id,
                    'discount': line_extend.discount_perc,
                    'price_unit': line_extend.price,
                    'company_id': rec.company_id.id,
                    'tax_ids': [(6, 0, line_extend.tax_ids.ids)] if line_extend.tax_ids.ids else False ,
                    'company_currency_id': rec.env.company.currency_id.id,
                        }
                inv_line_ids.append((0, 0, line_extend_ids))

            journal_id = self.env['account.journal'].search(
                [('branch_id', '=',rec.branch_id.id), ('type', '=', 'sale')], limit=1)
            journal_sale = ""
            if journal_id:
                journal_sale = journal_id.id
            else:
                journal_id = self.env['account.journal'].search(
                    [('type', '=', 'sale')], limit=1)

                journal_sale = journal_id.id
            print("journal_sale",journal_sale)
          
            invoice = self.env['account.move'].create({
                'name': '/',
                'type': 'out_invoice',
                'journal_id': journal_sale,
                'partner_id': rec.partner_id.id,
                'partner_mobile': rec.partner_mobile1 + str(' - '+ rec.partner_mobile2) if rec.partner_mobile2 else  False,
                'commercial_partner_id': rec.partner_id.id,
                'invoice_date': rec.order_date,
                'date': rec.order_date,
                'currency_id': self.env.company.currency_id.id,
                'state': 'draft',
                'company_id': rec.company_id.id,
                'invoice_user_id': rec.user_id.id,
                'invoice_payment_state': 'not_paid',
                'invoice_date_due': rec.order_date,
                'invoice_partner_display_name': rec.partner_id.name,
                'branch_id': rec.branch_id.id,

                'booking_id': rec.id,
                'invoice_line_ids': inv_line_ids,  })
            
             
            print("invoice",invoice)
            rec.write({'create_invoice_manually_id': invoice.id})
            action = self.env.ref('account.action_move_out_invoice_type')
            result = action.read()[0]
            result.pop('id', None)
            result['context'] = {}
            result['domain'] = [('booking_id', '=', rec.id)]
           
            return result
            
          
          
    @api.onchange('department_id')
    def get_department_data(self):
        for rec in self:
          
            rec.department_price = rec.department_id.dept_price
            rec.dept_tax_ids =  rec.department_id.tax_ids.id
            rec.lines.unlink()
            for line in rec.department_id.lines:
                line = self.env['hotel.lines'].create({'product_id': line.product_id.id,
                                                        'person_count': line.person_count,
                                                        'header_id': rec.id})
    
    @api.depends('department_price','dept_discount','dept_discount_type','dept_tax_ids')
    def _calc_department_price(self):
        for rec in self:
            if rec.department_price:
                new_discount = 0
                base_amount_line = rec.calc_base_amount(rec.department_price ,rec.dept_tax_ids.price_include)
                rec.dept_base_amount = base_amount_line
                rec.dept_discount_total = base_amount_line * (new_discount / 100)
                rec.dept_price_after_discount = base_amount_line - rec.dept_discount_total
                rec.dept_discount_perc = 0
                if rec.dept_tax_ids:
                    rec.dept_after_discount_with_tax =rec.dept_price_after_discount + rec.dept_price_after_discount * (15/100)
                    
                else:
                    rec.dept_after_discount_with_tax =rec.dept_price_after_discount                
            
                if rec.dept_discount:
                    base_amount_total = rec.calc_base_amount(rec.dept_after_discount_with_tax,rec.dept_tax_ids.price_include)

                    if rec.dept_discount_type !='discount_from_total':
                        new_discount = rec.set_discount_in_lines(rec.dept_discount_type,rec.dept_discount,base_amount_line,base_amount_total)
                    else:
                        new_discount = rec.set_discount_in_lines(rec.dept_discount_type,rec.dept_discount,base_amount_line,rec.dept_after_discount_with_tax)

                    if new_discount:
                        if self.env.user.max_discount_percentage:
                            if new_discount >  self.env.user.max_discount_percentage and not self.user_has_groups('qimamhd_booking_13.group_over_discount_mgr_priv'):
                                raise ValidationError(
                                            " لا يمكن الاستمرار .. الخصم [%s]اكبر من نسبة الخصم المحددة للمستخدم [%s]" % ( self.env.user.max_discount_percentage, self.env.user.name))
             
                        elif new_discount > rec.department_id.max_discount_percentage and not self.user_has_groups('qimamhd_booking_13.group_over_discount_mgr_priv'):
                             raise ValidationError(
                                    " لا يمكن الاستمرار .. الخصم  [%s]اكبر من نسبة الخصم المحدده للباقة" % rec.department_id.max_discount_percentage)
                        
                        rec.dept_discount_perc = new_discount
                        rec.dept_discount_total = base_amount_line * (new_discount / 100)
                        rec.dept_price_after_discount = base_amount_line - rec.dept_discount_total
                        if rec.dept_tax_ids:
                            rec.dept_after_discount_with_tax =rec.dept_price_after_discount  + rec.dept_price_after_discount  * (15/100)
                        
                        else:
                            rec.dept_after_discount_with_tax =rec.dept_price_after_discount                 
                
                rec._cal_tot_price()
            else:
              
                base_amount_line = 0
                rec.dept_after_discount_with_tax=0
                rec.dept_discount_total=0
                rec.dept_base_amount=0
                rec.dept_price_after_discount=0
                rec.dept_discount_perc = 0

    
    @api.onchange('discount', 'discount_type')
    def set_discount_master(self):
        for rec in self:
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                new_discount_services=0
                new_discount_dept = 0
                for ls in rec.service_lines:
                    ls.update({'discount': False ,
                                'discount_type': False,
                                'discount_total': False})
       
                rec.update({'dept_discount': False ,
                            'dept_discount_type': False,})
                
                if rec.discount and rec.discount_type:
                    for ls in rec.service_lines:
                        base_amount_line = rec.calc_base_amount((ls.price*ls.qty),ls.tax_ids.price_include)
                        print("base_amount_line",base_amount_line)
                        base_amount_total = rec.calc_base_amount(rec.service_after_discount_with_tax,ls.tax_ids.price_include)
                        print("base_amount_total",base_amount_total)
                        
                        if rec.discount_type != 'discount_from_total':
                            new_discount_services = rec.set_discount_in_lines(rec.discount_type,rec.discount,base_amount_line,base_amount_total)
                        else:
                            new_discount_services = rec.set_discount_in_lines(rec.discount_type,rec.discount,base_amount_line,rec.service_after_discount_with_tax)
                    
                        if new_discount_services:
                        
                            ls.update({'discount': new_discount_services ,
                                    'discount_type': 'percentage'})
                        else:
                            
                            ls.update({'discount': False ,
                                    'discount_type': False}) 
              
                    
                    base_amount_line = rec.calc_base_amount(rec.department_price,rec.dept_tax_ids.price_include)
                    print("base_amount_line",base_amount_line)
                    base_amount_total = rec.calc_base_amount(rec.dept_after_discount_with_tax,rec.dept_tax_ids.price_include)
                    print("base_amount_total",base_amount_total)
                    if rec.discount_type != 'discount_from_total':
                        new_discount_dept = rec.set_discount_in_lines(rec.discount_type,rec.discount,base_amount_line,base_amount_total)
                    else:
                        new_discount_dept = rec.set_discount_in_lines(rec.discount_type,rec.discount,base_amount_line,rec.service_after_discount_with_tax)
    
                        
                    if new_discount_dept:
                        rec.update({'dept_discount': new_discount_dept ,
                                    'dept_discount_type': 'percentage' })
                    
                    else:
                        rec.update({'dept_discount': False })
                    
        
                    
                rec._cal_tot_price()  
    def calc_base_amount(self,price,tax_include_price):

        if price:
            if tax_include_price:
                return price /1.15
            if not tax_include_price:
                return price
        else:
            return 0
    
    
    def set_discount_in_lines(self,discount_type,discount_line,amount_line,amount_total):
           
            if discount_type and discount_line:
                if discount_type == 'percentage':
                    if discount_line > 100:
                        raise ValidationError(
                            "تنبيه... نسبة الخصم غير صحيحة")
                        
                    if amount_line and amount_total:
                        amt_per = (amount_line / amount_total)
                        amount_discount = (discount_line / 100) * amount_total

                        new_line_discount = amount_discount * amt_per
                        print("amt_per", amt_per)
                        new_per_discount = (new_line_discount / amount_line) * 100
                        return new_per_discount

                if discount_type == 'amount':
                    if discount_line > amount_total:
                        raise ValidationError(
                            "تنبيه... نسبة الخصم غير صحيحة")
                    if amount_line:
                        amt_per = (amount_line / amount_total)
                        new_line_discount = discount_line * amt_per
                        print("new_line_discount", new_line_discount)
                        new_per_discount = (new_line_discount / amount_line) * 100
                        return new_per_discount
                       

                if discount_type == 'discount_from_total':
                    if discount_line < amount_total:
                        diff = amount_total - discount_line
                        discount = (diff / amount_total) * 100
                        print("discount", discount)
                        if discount != 0:
                           return discount
                    else:
                        raise ValidationError(
                            "لا يمكن ان يكون الخصم اكبر من اجمالي ")
            else:
                    return False
    @api.depends('service_lines','dept_after_discount_with_tax')
    def _cal_tot_price(self):
        for rec in self:
            print("*******************" )
            services_price = 0.00
            discount_total = 0.00
            services_price_after_discount = 0.00
            services_price_with_tax = 0.00

            total_before_tax = 0.00
          
            for line in rec.service_lines:
                services_price += (line.qty * line.price)
                discount_total += line.discount_total
                services_price_after_discount += line.price_after_discount
                services_price_with_tax += line.price_after_discount_with_tax
                total_before_tax += line.base_amount
    

            rec.service_price = services_price + rec.department_price
            rec.service_discount_total = discount_total + rec.dept_discount_total
            rec.service_price_after_discount = services_price_after_discount + rec.dept_price_after_discount
            rec.service_after_discount_with_tax = services_price_with_tax + rec.dept_after_discount_with_tax
            rec.service_base_amount = total_before_tax + rec.dept_base_amount
            if rec.service_base_amount:
               rec.service_discount_perc = (rec.service_discount_total / rec.service_base_amount) * 100
            else:
                rec.service_discount_perc = 0.00
    def action_register_payment(self):
        for rec in self:
            payment = self.env['booking.register.payment'].search([('header_id', '=', rec.id)])
             

            action = self.env.ref('qimamhd_booking_13.action_booking_payment_view')
            result = action.read()[0]
            result.pop('id', None)
            result['context'] = {}
            result['domain'] = [('id', 'in', payment.ids)]
            return result

    def call_invoice(self):
        for rec in self:
            action = self.env.ref('account.action_move_out_invoice_type')
            result = action.read()[0]
            result.pop('id', None)
            result['context'] = {}
            result['domain'] = [('booking_id', '=', rec.id)]
            return result
    def call_extend_services(self):
        for rec in self:
            action = self.env.ref('qimamhd_booking_13.action_hotel_extend_view')
            result = action.read()[0]
            result.pop('id', None)
            result['context'] = {}
            result['domain'] = [('extend_header_id', '=', rec.id)]
            return result
    def changeamount2words(self, amount):
        pre = float(amount)
        if pre:
            text = ''
            entire_num = int((str(pre).split('.'))[0])
            decimal_num = int((str(pre).split('.'))[1])
            if decimal_num < 10:
                decimal_num = decimal_num * 10
            #     ar_001
            text += num2words(entire_num, lang='ar_001').title()
            text += ' ريال '
            if decimal_num:
                text += ' و '
                text += num2words(decimal_num, lang='ar_001').title()
                text += ' هلله '
                text = text.replace(',', ' و ')

            amount_text = 'فقط ' + text.replace('،', ' و ')
            return amount_text
class xx_hotel_lines(models.Model):
    _name = 'hotel.lines'
  
    
    product_id = fields.Many2one('product.product', string="ألخدمة", required=True,domain=[('booking_flag','=',True)])
    person_count = fields.Float(string="الكمية المطلوبة" )
    delivered_qty = fields.Float(string="الكمية المسلمة" )
    header_id = fields.Many2one('hotel.master',ondelete="cascade")
    
class xx_hotel_service_lines(models.Model):
    _name = 'hotel.service.lines'
  
    
    product_id = fields.Many2one('product.product', string="ألخدمة", required=True,domain=[('booking_flag','=',True)])
    name = fields.Char(string="الوصف" )

    tax_ids = fields.Many2one('account.tax', string='نوع الضريبة', domain=[('type_tax_use','=','sale')],help="Taxes that apply on the base amount")

    qty = fields.Float(string="العدد",required=True )
    price = fields.Float(string="السعر",required=True)
    total = fields.Float(store=True,compute="_calc_total",string="الاجمالي")
    discount_type = fields.Selection([('amount', 'مبلغ'), ('percentage', 'نسبة'),('discount_from_total','الخصم من الاجمالي')], 
                                             string="نوع الخصم",  default='percentage') 
    discount = fields.Float( string="نسبة الخصم")
    discount_perc = fields.Float( string="نسبة الخصم المحتسبة",compute="_calc_total")
    discount_total = fields.Float(store=True,compute="_calc_total",string="مبلغ الخصم")
    base_amount = fields.Float(store=True,compute="_calc_total",string="المبلغ الاساسي")
    price_after_discount = fields.Float(store=True,compute="_calc_total",string="الاجمالي بعد الخصم")
    
    price_after_discount_with_tax = fields.Float( string="الاجمالي شامل الضريبة",store=True,compute="_calc_total")
  
    header_id = fields.Many2one('hotel.master',ondelete="cascade")
    extend_header_id = fields.Many2one('hotel.service.extend',ondelete="cascade")

    
    @api.onchange('product_id')
    def set_name(self):
        for rec in self:
            rec.name = rec.product_id.name
            rec.write({'qty': 1})
            rec.price = rec.product_id.list_price
            rec.tax_ids = rec.product_id.taxes_id.id

    @api.depends('qty','price','discount','discount_type','tax_ids')
    def _calc_total(self):
        for rec in self:
            rec.total = (rec.qty * rec.price)
            if rec.total:
                new_discount = 0
                base_amount_line = rec.header_id.calc_base_amount(rec.total ,rec.tax_ids.price_include)
                rec.base_amount = base_amount_line
                rec.discount_total = base_amount_line * (new_discount / 100)
                rec.price_after_discount = base_amount_line - rec.discount_total
                if rec.tax_ids:
                    rec.price_after_discount_with_tax =rec.price_after_discount + rec.price_after_discount * (15/100)
                    
                else:
                    rec.price_after_discount_with_tax =rec.price_after_discount                
            
                if rec.discount:
                    base_amount_total = rec.header_id.calc_base_amount(rec.price_after_discount_with_tax,rec.tax_ids.price_include)

                    if rec.discount_type !='discount_from_total':
                        new_discount = rec.header_id.set_discount_in_lines(rec.discount_type,rec.discount,base_amount_line,base_amount_total)
                    else:
                        new_discount = rec.header_id.set_discount_in_lines(rec.discount_type,rec.discount,base_amount_line,rec.price_after_discount_with_tax)

                    if new_discount:
                        if self.env.user.max_discount_percentage:
                            if new_discount >  self.env.user.max_discount_percentage and not self.user_has_groups('qimamhd_booking_13.group_over_discount_mgr_priv'):
                                raise ValidationError(
                                            " لا يمكن الاستمرار .. الخصم [%s]اكبر من نسبة الخصم المحددة للمستخدم [%s]" % ( self.env.user.max_discount_percentage, self.env.user.name))
             
                        elif new_discount > rec.header_id.department_id.max_discount_percentage and not self.user_has_groups('qimamhd_booking_13.group_over_discount_mgr_priv'):
                             raise ValidationError(
                                    " لا يمكن الاستمرار .. الخصم  [%s]اكبر من نسبة الخصم المحدده للباقة" % rec.header_id.department_id.max_discount_percentage)
                        
                       
                        rec.discount_total = base_amount_line * (new_discount / 100)
                        rec.price_after_discount = base_amount_line - rec.discount_total
                        if rec.tax_ids:
                            rec.price_after_discount_with_tax =rec.price_after_discount  + rec.price_after_discount  * (15/100)
                        
                        else:
                            rec.price_after_discount_with_tax =rec.price_after_discount                 
                    else:
                        rec.discount_perc = new_discount
                else:
                    rec.discount_perc = new_discount
            else:
              
                base_amount_line = 0
                rec.price_after_discount_with_tax=0
                rec.discount_total=0
                rec.base_amount=0
                rec.price_after_discount=0
                rec.discount_perc = 0

class xx_car_installation_order_register_payment(models.Model):
    _name = 'booking.register.payment'
    _description = 'Register Payment in installation order'

    _rec_name = 'journal_id'

    def get_journal_id(self):
        return [('type', '=', ['cash', 'bank']), ('branch_id','=', self.env.user.branch_id.id)]

    pay_date = fields.Date(string="تاريخ الدفع", default=fields.Date.today)
    user_id = fields.Many2one(
        'res.users', string='User name', readonly=True,
        required=True, default=lambda self: self.env.uid)
    state = fields.Selection([('draft','مسودة'),('posted','مرحل'),('cancel','ملغي')])
    invoice_amount = fields.Float(string="مبلغ الفاتورة",readonly=True)
    advanced_amount = fields.Float(string="المبلغ المقدم",readonly=True)
    remaining_amount = fields.Float(string="المبلغ المتبقي",readonly=True)
    payment_amount = fields.Float(string="المبلغ المدفوع", reqiured=True)
    branch_id= fields.Many2one('custom.branches')
    payment_note = fields.Char(string="البيان")
    header_id = fields.Many2one('hotel.master',ondelete="cascade")
   
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 domain=get_journal_id)
    payment_id = fields.Many2one('account.payment',    
                               )


    def create_payment(self):
        for rec in self:
            if rec.payment_amount <= 0:
                raise ValidationError(
                    "يجب تحديد المبلغ اولا")

            payment = self.env['booking.register.payment'].search([('header_id', '=', rec.header_id.id),('state', '=', 'posted')])
            print(payment)
            advanced_amount = 0
            for line in payment:
                advanced_amount = advanced_amount + line.payment_amount

            account_payment = self.env['account.payment'].search([('booking_id', '=', rec.header_id.id),('state', '=', 'posted')])
            extend_Service_amt = sum(l.price_after_discount_with_tax for l in rec.header_id.service_extend_lines.service_add_lines)

            ready_amount = 0
            for line in account_payment:
                ready_amount = ready_amount + line.amount
                
            if ready_amount >= (rec.header_id.service_after_discount_with_tax + extend_Service_amt):
                raise ValidationError(
                    "اكتمل الدفع للحجز في شاشة مدفوعات الفوترة للحجز المحدد .. لا يمكن انشاء مفوعات جديدة ")
          
            if advanced_amount >= (rec.header_id.service_after_discount_with_tax + extend_Service_amt):
                raise ValidationError(
                    "اكتمل الدفع للحجز .. لا يمكن انشاء مدفوعات جديدة ")

            
            self.inbound_payment_method = self.env['account.payment.method'].create({
                'name': 'inbound',
                'code': 'IN',
                'payment_type': 'inbound',
            })
            payment = self.env['account.payment'].create({
                'payment_date': self.pay_date,
                'payment_method_id': self.inbound_payment_method.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': self.header_id.partner_id.id,
                'amount': self.payment_amount,
                'journal_id': self.journal_id.id,
                'company_id': self.header_id.company_id.id,
                'branch_id': self.branch_id.id,
                'currency_id': self.env.company.currency_id.id,
                'payment_difference_handling': 'reconcile',
                'communication': self.payment_note,
                'booking_id': rec.header_id.id,

                  })
            payment.post()
            self.write({'state': 'posted'})
            self.write({'payment_id': payment.id})
            payment = self.env['booking.register.payment'].search([('header_id', '=', rec.header_id.id),('state', '!=', 'cancel')])
            print(payment)
            advanced_amount = 0
            for line in payment:
                advanced_amount = advanced_amount + line.payment_amount

            wo = self.env['hotel.master'].search([('id', '=', rec.header_id.id)])

            wo.write({'advance_amount': advanced_amount})

    def call_payments(self):
        for rec in self:
            action = self.env.ref('account.action_account_payments')
            result = action.read()[0]
            result.pop('id', None)
            result['context'] = {}
            result['domain'] = [('booking_id', '=', rec.header_id.id)
                                ]
            return result
    
    def cancel_payment_btn(self):
        for rec in self:
            rec.write({'state': 'cancel'})
            if rec.payment_id:
                rec.payment_id.action_draft()
                rec.payment_id.cancel()
            payment = self.env['booking.register.payment'].search([('header_id', '=', rec.header_id.id),('state', '!=', 'cancel')])
            print(payment)
            advanced_amount = 0
            for line in payment:
                advanced_amount = advanced_amount + line.payment_amount

            wo = self.env['hotel.master'].search([('id', '=', rec.header_id.id)])

            wo.write({'advance_amount': advanced_amount})

class xx_hotel_service_extend_lines(models.Model):
    _name = 'hotel.service.extend'
    _inherit = ['mail.thread']
    _rec_name = "partner_id"
    
    order_date = fields.Date(required=True, string="تاريخ الملحق")
    state = fields.Selection([('draft','مسودة'),('confirm','تم الاعتماد')
                              ,('cancel_order','ملحق ملغي')],
                             default='draft',string="حالة الحجز")
    partner_id = fields.Many2one('res.partner',required=True, string="العميل")
    service_id = fields.Many2one('booking.services',string="الخدمة",required=True)
    department_id = fields.Many2one('booking.departments',string="القسم",required=True)
    booking_start_date = fields.Date(string="الحجز من تاريخ")
    booking_end_date = fields.Date(string="الحجز الى تاريخ")
                               
    user_id = fields.Many2one(
        'res.users', string='مدخل البيانات',  
        required=True, default=lambda self: self.env.uid)
     
    extend_header_id = fields.Many2one('hotel.master',ondelete="cascade")
    
    service_add_lines = fields.One2many('hotel.service.lines', 'extend_header_id',ondelete="cascade", required=True, )
    
    def confirm_btn(self):
        for rec in self:
            rec.write({'state': 'confirm'})

    def un_confirm_btn(self):
        for rec in self:
            rec.write({'state': 'draft'})
    
    def cancel_order(self):
        for rec in self:
            rec.write({'state': 'cancel_order'})
    
    def unlink(self):
        for rec in self:
            if rec.state == 'confirm':
                 raise ValidationError("تنبيه ... الملحق معتمد لا يمكن الحذف")
        return super(xx_hotel_service_extend_lines, self).unlink()
