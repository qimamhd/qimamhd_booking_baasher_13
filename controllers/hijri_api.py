from odoo import http
from odoo.http import request
from hijri_converter import convert

class HijriApi(http.Controller):

    @http.route('/qimamhd/hijri_converter', type='json', auth='user')
    def hijri_converter(self, date_str):
        """
        يستقبل تاريخ ميلادي بصيغة YYYY-MM-DD ويُرجع التاريخ الهجري الكامل نصًا
        """
        try:
            y, m, d = map(int, date_str.split('-'))
            h = convert.Gregorian(y, m, d).to_hijri()
            hijri_text = f"{h.day} {self._get_month_name(h.month)} {h.year}"
            return {'success': True, 'hijri_text': hijri_text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_month_name(self, m):
        months = [
            "محرم", "صفر", "ربيع الأول", "ربيع الآخر",
            "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
            "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
        ]
        return months[m - 1]
