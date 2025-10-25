// odoo.define('qimamhd_booking_13.CalendarHijri', function (require) {
//     "use strict";

//     var CalendarRenderer = require('web.CalendarRenderer');

//     CalendarRenderer.include({

//         _render: function () {
//             var self = this;
//             var res = this._super.apply(this, arguments);

//             // أسماء الأشهر الهجرية بالعربية
//             var hijriMonths = [
//                 "محرم", "صفر", "ربيع الأول", "ربيع الآخر",
//                 "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
//                 "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
//             ];

//             // نضيف التاريخ الهجري بالحروف العربية تحت كل يوم
//             setTimeout(function () {
//                 self.$el.find('.fc-day-top').each(function () {
//                     var $cell = $(this);
//                     var date = $cell.data('date'); // YYYY-MM-DD

//                     if (date) {
//                         // نحول التاريخ لمومنت وننقص يوم
//                         var mDate = moment(date).subtract(1, 'days');

//                         var hYear = mDate.iYear();
//                         var hMonth = mDate.iMonth(); // صفر-based
//                         var hDay = mDate.iDate();

//                         var hijriText = hDay + " " + hijriMonths[hMonth] + " " + hYear;

//                         // نمنع التكرار
//                         if ($cell.find('.hijri-date').length === 0) {
//                             $cell.append(
//                                 $('<div/>', {
//                                     text: hijriText,
//                                     class: 'hijri-date',
//                                     css: {
//                                         'font-size': '11px',
//                                         'color': '#007bff',
//                                         'margin-top': '2px'
//                                     }
//                                 })
//                             );
//                         }
//                     }
//                 });
//             }, 50);

//             return res;
//         },
//     });
// });
odoo.define('qimamhd_booking_13.CalendarHijri', function (require) {
    "use strict";

    const CalendarRenderer = require('web.CalendarRenderer');
    const rpc = require('web.rpc');

    CalendarRenderer.include({

        _render: function () {
            const self = this;
            const res = this._super.apply(this, arguments);

            // بعد عرض التقويم، أضف التواريخ الهجرية تحت كل يوم
            setTimeout(function () {
                self.$el.find('.fc-day-top').each(function () {
                    const $cell = $(this);
                    const date = $cell.data('date'); // YYYY-MM-DD

                    if (date && !$cell.find('.hijri-date').length) {
                        // استدعاء الـ API لجلب التاريخ الهجري من الباك إند
                        rpc.query({
                            route: '/qimamhd/hijri_converter',
                            params: { date_str: date },
                        }).then(function (result) {
                            if (result.success) {
                                $cell.append(
                                    $('<div/>', {
                                        text: result.hijri_text,
                                        class: 'hijri-date',
                                        css: {
                                            'font-size': '11px',
                                            'color': '#007bff',
                                            'margin-top': '2px'
                                        }
                                    })
                                );
                            }
                        });
                    }
                });
            }, 100);

            return res;
        },
    });
});
