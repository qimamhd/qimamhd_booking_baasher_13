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
    'depends': ['base','custom_branch_13', 'calendar','qimamhd_booking_13'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
         
        'reports/booking_report.xml',
        'reports/booking_payment_report.xml',
        'reports/booking_extend_report.xml',
        'views/booking.xml',
       
         
 
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}

