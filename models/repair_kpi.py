from odoo import models, fields, api
from odoo.exceptions import UserError


class RepairComplaintKPI(models.TransientModel):
    _name = 'repair.complaint.kpi'
    _description = 'مؤشر قياس متوسط زمن الشكاوي'

    date_from = fields.Date(string="من تاريخ", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="إلى تاريخ", required=True, default=fields.Date.context_today)
    
    # نتائج الحساب
    total_complaints = fields.Integer(string="عدد الشكاوى المستلمة", readonly=True)
    total_days_difference = fields.Float(string="إجمالي فرق الأيام", readonly=True)
    average_complaint_time = fields.Float(string="متوسط زمن الشكاوي (بالأيام)", readonly=True, digits=(16, 2))
    
    # تفاصيل الشكاوى
    complaint_line_ids = fields.One2many('repair.complaint.kpi.line', 'kpi_id', string="تفاصيل الشكاوى")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise UserError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')

    def action_calculate_kpi(self):
        """حساب متوسط زمن الشكاوي"""
        self.ensure_one()
        
        # حذف الأسطر السابقة
        self.complaint_line_ids.unlink()
        
        # البحث عن طلبات الإصلاح في الفترة المحددة
        # نبحث عن الطلبات التي لها schedule_date و x_in_repair_date ضمن الفترة
        domain = [
            ('schedule_date', '>=', self.date_from),
            ('schedule_date', '<=', self.date_to),
            ('x_in_repair_date', '!=', False),
        ]
        
        repair_orders = self.env['repair.order'].search(domain)
        
        if not repair_orders:
            self.write({
                'total_complaints': 0,
                'total_days_difference': 0,
                'average_complaint_time': 0,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'تنبيه',
                    'message': 'لا توجد شكاوى في الفترة المحددة',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        total_days = 0.0
        lines_data = []
        
        for order in repair_orders:
            # حساب الفرق بين تاريخ قيد الإصلاح والتاريخ المجدول
            schedule_date = order.schedule_date
            in_repair_date = order.x_in_repair_date
            
            if schedule_date and in_repair_date:
                # تحويل schedule_date إلى date إذا كان datetime
                if hasattr(schedule_date, 'date'):
                    schedule_date = schedule_date.date()
                
                days_diff = (in_repair_date - schedule_date).days
                total_days += days_diff
                
                lines_data.append({
                    'kpi_id': self.id,
                    'repair_order_id': order.id,
                    'schedule_date': order.schedule_date,
                    'in_repair_date': in_repair_date,
                    'days_difference': days_diff,
                })
        
        # إنشاء أسطر التفاصيل
        self.env['repair.complaint.kpi.line'].create(lines_data)
        
        # حساب المتوسط
        total_complaints = len(repair_orders)
        average_time = total_days / total_complaints if total_complaints > 0 else 0
        
        self.write({
            'total_complaints': total_complaints,
            'total_days_difference': total_days,
            'average_complaint_time': average_time,
        })
        
        # إعادة فتح النموذج لعرض النتائج
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'repair.complaint.kpi',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }


class RepairComplaintKPILine(models.TransientModel):
    _name = 'repair.complaint.kpi.line'
    _description = 'تفاصيل شكاوى مؤشر الأداء'

    kpi_id = fields.Many2one('repair.complaint.kpi', string="مؤشر الأداء", ondelete='cascade')
    repair_order_id = fields.Many2one('repair.order', string="طلب الإصلاح", readonly=True)
    schedule_date = fields.Datetime(string="التاريخ المجدول", readonly=True)
    in_repair_date = fields.Date(string="تاريخ قيد الإصلاح", readonly=True)
    days_difference = fields.Integer(string="فرق الأيام", readonly=True)


class RepairClosedComplaintKPI(models.TransientModel):
    _name = 'repair.closed.complaint.kpi'
    _description = 'مؤشر قياس متوسط الشكاوى المغلقة'

    date_from = fields.Date(string="من تاريخ", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="إلى تاريخ", required=True, default=fields.Date.context_today)
    
    # نتائج الحساب
    total_closed_complaints = fields.Integer(string="عدد الشكاوى المغلقة", readonly=True)
    total_days_difference = fields.Float(string="إجمالي فرق الأيام", readonly=True)
    average_closed_complaint_time = fields.Float(string="متوسط زمن الشكاوى المغلقة (بالأيام)", readonly=True, digits=(16, 2))
    
    # تفاصيل الشكاوى المغلقة
    closed_complaint_line_ids = fields.One2many('repair.closed.complaint.kpi.line', 'kpi_id', string="تفاصيل الشكاوى المغلقة")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise UserError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية')

    def action_calculate_closed_kpi(self):
        """حساب متوسط زمن الشكاوى المغلقة"""
        self.ensure_one()
        
        # حذف الأسطر السابقة
        self.closed_complaint_line_ids.unlink()
        
        # البحث عن طلبات الإصلاح المغلقة (حالة done) في الفترة المحددة
        domain = [
            ('schedule_date', '>=', self.date_from),
            ('schedule_date', '<=', self.date_to),
            ('x_done_date', '!=', False),
            ('state', '=', 'done'),  # فقط الشكاوى التي تم إصلاحها
        ]
        
        repair_orders = self.env['repair.order'].search(domain)
        
        if not repair_orders:
            self.write({
                'total_closed_complaints': 0,
                'total_days_difference': 0,
                'average_closed_complaint_time': 0,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'تنبيه',
                    'message': 'لا توجد شكاوى مغلقة في الفترة المحددة',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        total_days = 0.0
        lines_data = []
        
        for order in repair_orders:
            # حساب الفرق بين تاريخ الانتهاء والتاريخ المجدول
            schedule_date = order.schedule_date
            done_date = order.x_done_date
            
            if schedule_date and done_date:
                # تحويل schedule_date إلى date إذا كان datetime
                if hasattr(schedule_date, 'date'):
                    schedule_date = schedule_date.date()
                
                days_diff = (done_date - schedule_date).days
                total_days += days_diff
                
                lines_data.append({
                    'kpi_id': self.id,
                    'repair_order_id': order.id,
                    'schedule_date': order.schedule_date,
                    'done_date': done_date,
                    'days_difference': days_diff,
                })
        
        # إنشاء أسطر التفاصيل
        self.env['repair.closed.complaint.kpi.line'].create(lines_data)
        
        # حساب المتوسط
        total_closed = len(repair_orders)
        average_time = total_days / total_closed if total_closed > 0 else 0
        
        self.write({
            'total_closed_complaints': total_closed,
            'total_days_difference': total_days,
            'average_closed_complaint_time': average_time,
        })
        
        # إعادة فتح النموذج لعرض النتائج
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'repair.closed.complaint.kpi',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }


class RepairClosedComplaintKPILine(models.TransientModel):
    _name = 'repair.closed.complaint.kpi.line'
    _description = 'تفاصيل الشكاوى المغلقة لمؤشر الأداء'

    kpi_id = fields.Many2one('repair.closed.complaint.kpi', string="مؤشر الأداء", ondelete='cascade')
    repair_order_id = fields.Many2one('repair.order', string="طلب الإصلاح", readonly=True)
    schedule_date = fields.Datetime(string="التاريخ المجدول", readonly=True)
    done_date = fields.Date(string="تاريخ الانتهاء", readonly=True)
    days_difference = fields.Integer(string="فرق الأيام", readonly=True)
