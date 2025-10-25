//! moment-hijri.js
//! version : 2.1.2
//! author : @xsoh
//! license : MIT
//! github.com/xsoh/moment-hijri

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define(['moment'], factory);
    } else if (typeof exports === 'object') {
        module.exports = factory(require('moment'));
    } else {
        factory(root.moment);
    }
}(this, function (moment) {
    if (!moment) {
        throw new Error('Moment.js is required');
    }

    var ummalqura = {
        // تحويل السنة الميلادية إلى الهجرية
        gregorianToHijri: function (gYear, gMonth, gDay) {
            var jd = Math.floor((1461 * (gYear + 4800 + Math.floor((gMonth - 14) / 12))) / 4) +
                Math.floor((367 * (gMonth - 2 - 12 * (Math.floor((gMonth - 14) / 12)))) / 12) -
                Math.floor((3 * (Math.floor((gYear + 4900 + Math.floor((gMonth - 14) / 12)) / 100))) / 4) +
                gDay - 32075;
            return ummalqura.jdToHijri(jd);
        },
        // تحويل الجوليان إلى هجري
        jdToHijri: function (jd) {
            var l = jd - 1948440 + 10632;
            var n = Math.floor((l - 1) / 10631);
            l = l - 10631 * n + 354;
            var j = (Math.floor((10985 - l) / 5316)) * (Math.floor((50 * l) / 17719)) +
                (Math.floor(l / 5670)) * (Math.floor((43 * l) / 15238));
            l = l - (Math.floor((30 - j) / 15)) * (Math.floor((17719 * j) / 50)) -
                (Math.floor(j / 16)) * (Math.floor((15238 * j) / 43)) + 29;
            var m = Math.floor((24 * l) / 709);
            var d = l - Math.floor((709 * m) / 24);
            var y = 30 * n + j - 30;
            return [y, m, d];
        }
    };

    // إضافة دوال للهجري
    moment.fn.iYear = function () {
        return this._hYear || this.hijriData().year;
    };

    moment.fn.iMonth = function () {
        return this._hMonth || this.hijriData().month;
    };

    moment.fn.iDate = function () {
        return this._hDate || this.hijriData().date;
    };

    moment.fn.hijriData = function () {
        var gYear = this.year();
        var gMonth = this.month() + 1;
        var gDay = this.date();
        var h = ummalqura.gregorianToHijri(gYear, gMonth, gDay);
        return { year: h[0], month: h[1] - 1, date: h[2] };
    };

    // format hijri
    var oldFormat = moment.fn.format;
    moment.fn.format = function (inputString) {
        var str = inputString || '';
        if (str.indexOf('i') !== -1) {
            var h = this.hijriData();
            str = str.replace(/iYYYY/g, h.year);
            str = str.replace(/iMM/g, ('0' + (h.month + 1)).slice(-2));
            str = str.replace(/iDD/g, ('0' + h.date).slice(-2));
            str = str.replace(/iD/g, h.date);
            str = str.replace(/iM/g, h.month + 1);
        }
        return oldFormat.call(this, str);
    };
}));
