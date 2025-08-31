# Đường dẫn: addons/user_export/models/user_export_log.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api

class UserExportLog(models.Model):
    _name = 'user.export.log'
    _description = 'User Export Log'
    _order = 'create_date desc'
    
    name = fields.Char(string='Export Name', required=True)
    export_date = fields.Datetime(string='Export Date', default=fields.Datetime.now)
    exported_by = fields.Many2one('res.users', string='Exported By', default=lambda self: self.env.user)
    user_count = fields.Integer(string='Number of Users Exported')
    file_name = fields.Char(string='File Name')
    file_type = fields.Selection([
        ('csv', 'CSV'),
        ('excel', 'Excel')
    ], string='File Type', default='excel')
    notes = fields.Text(string='Notes')