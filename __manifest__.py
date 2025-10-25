# -*- coding: utf-8 -*-
{
    'name': 'qimamhd_booking_baasher_13',
    'version': '13.0.1.0.0',
    'summary': 'qimamhd_booking_baasher_13',
    'category': 'Tools',
    'author': 'Developers team',
    'maintainer': 'qimamhd-tech Techno Solutions',
    'company': 'qimamhd-tech Techno Solutions',
    'website': 'https://www.qimamhd-tech.com',
    'depends': ['base','custom_branch_13', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/product_template.xml',
        'views/hotel.xml',
        'views/hotel_extend.xml',
        'views/register_payment.xml',
        'views/users.xml',
        'views/account_move.xml',
        'reports/booking_report.xml',
        'reports/booking_payment_report.xml',
        'reports/booking_extend_report.xml',
        'views/delivery_report_view.xml',
        'views/delivery_booking.xml',
        'reports/delivery_report.xml',
        

        # هنا نضيف ملف الأصول
        'views/assets.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}

