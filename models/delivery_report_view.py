from datetime import date, time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class product_label_report(models.TransientModel):
    _inherit = 'booking.delivery.report.view'

    def get_report(self):
        """Call when button 'Get Report' clicked.

        """
        active_ids = self._context.get('active_ids', [])
        self.booking_id = self.env['hotel.master'].search([('id', '=', active_ids)])
      
        self.customer_id = self.booking_id.partner_id.id
        # self.write({'date_order': self.booking_id.date_order})

        line_ids = []
        for l in self.lines:
            print("line_ids", l)

            if l.qty:
               line_ids.append(l.id)
               l.booking_line_id.write({'delivered_qty': l.qty + l.booking_line_id.delivered_qty})
               
      

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_order': self.date_order,
                'customer_id': self.customer_id.name,
                'lines': line_ids,
                'booking_id': self.booking_id.id,
                'id': self.id,
                'print_date': date.today(),
                },
            }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('qimamhd_booking_13.booking_delivery_report').report_action(self, data=data)


class ReportAttendanceRecap(models.AbstractModel):
    _name = 'report.qimamhd_booking_13.booking_delivery_report_temp'

    @api.model
    def _get_report_values(self, docids, data=None):
        l_customer = data['form']['customer_id']
        l_date_order = data['form']['date_order']
        l_booking_id = data['form']['booking_id']
        l_id = data['form']['id']
        l_print_date = data['form']['print_date']

        l_lines = data['form']['lines']
        sql_query = """
                        select id , 
                                   product as product_name,

                                qty from booking_delivery_view_line l where  qty > 0
        """
        if l_lines:
            if len(l_lines) > 1:
                sql_query += " and id in %s " % (tuple(l_lines),)
            else:
                if len(l_lines) == 1:
                    l_line = l_lines[0]
                    sql_query += " and id = %s " % (l_line)
        else:
            raise ValidationError(
                "تنبيه.. حدد الكمية بشكل صحيح على الاقل يتم اختيار كمية صنف واحدة")

        print(sql_query)
        self.env.cr.execute(sql_query)
        result = self.env.cr.dictfetchall()
        booking_ids = self.env['hotel.master'].search([('id', '=', l_booking_id)])

        res= []
        record = {
            'customer': l_customer,
            'date_order': l_date_order,
            'lines': result,
            'booking': booking_ids.seq,
            'id': l_id,
            'print_date': l_print_date,


         }
        res.append(record)
        print(res)
        # for lable in res:
        #     for line in lable['lines']:
        #         print("line",line.product_id.id)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': res,
            'branch_id': booking_ids.branch_id,


        }


class product_label_report_line(models.TransientModel):
    _name = 'booking.delivery.view.line'

    product = fields.Char()
    booking_line_id =  fields.Many2one('hotel.lines')
    
    qty = fields.Float()
    header_id = fields.Many2one('booking.delivery.report.view')
