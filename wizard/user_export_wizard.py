# Đường dẫn: addons/user_export/wizard/user_export_wizard.py
# -*- coding: utf-8 -*-
import base64
import xlsxwriter
import io
import csv
from odoo import models, fields, api
from odoo.exceptions import UserError

class UserExportWizard(models.TransientModel):
    _name = 'user.export.wizard'
    _description = 'User Export Wizard'
    
    name = fields.Char(string='Export Name', default='User Export')
    export_type = fields.Selection([
        ('all', 'All Users'),
        ('active', 'Active Users Only'),
        ('by_groups', 'By Groups'),
        ('by_teams', 'By Sales Teams')
    ], string='Export Type', default='active', required=True)
    
    group_ids = fields.Many2many('res.groups', string='User Groups')
    team_ids = fields.Many2many('crm.team', string='Sales Teams')
    
    file_type = fields.Selection([
        ('csv', 'CSV'),
        ('excel', 'Excel (.xlsx)')
    ], string='File Type', default='excel', required=True)
    
    include_login = fields.Boolean(string='Include Login', default=True)
    include_email = fields.Boolean(string='Include Email', default=True)
    include_phone = fields.Boolean(string='Include Phone', default=True)
    include_groups = fields.Boolean(string='Include Groups', default=True)
    include_company = fields.Boolean(string='Include Company', default=True)
    include_department = fields.Boolean(string='Include Department', default=False)
    include_last_login = fields.Boolean(string='Include Last Login', default=False)
    
    file_data = fields.Binary(string='Download File', readonly=True)
    file_name = fields.Char(string='File Name', readonly=True)
    
    @api.onchange('export_type')
    def _onchange_export_type(self):
        if self.export_type != 'by_groups':
            self.group_ids = False
        if self.export_type != 'by_teams':
            self.team_ids = False
    
    def action_export(self):
        """Export users data"""
        users = self._get_users_to_export()
        
        if not users:
            raise UserError('Không có users nào để export!')
        
        if self.file_type == 'excel':
            file_data, file_name = self._generate_excel(users)
        else:
            file_data, file_name = self._generate_csv(users)
        
        # Lưu log
        self._create_export_log(len(users), file_name)
        
        # Cập nhật wizard để download
        self.write({
            'file_data': file_data,
            'file_name': file_name
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'user.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'default_file_data': file_data, 'default_file_name': file_name}
        }
    
    
    def _get_users_to_export(self):
        """Get users based on export criteria"""
        domain = []
        
        if self.export_type == 'active':
            domain.append(('active', '=', True))
        elif self.export_type == 'by_groups':
            if not self.group_ids:
                raise UserError('Vui lòng chọn ít nhất một nhóm!')
            domain.append(('groups_id', 'in', self.group_ids.ids))
        elif self.export_type == 'by_teams':
            if not self.team_ids:
                raise UserError('Vui lòng chọn ít nhất một team!')
            domain.append(('sale_team_id', 'in', self.team_ids.ids))
        
        return self.env['res.users'].search(domain)
    
    def _generate_excel(self, users):
        """Generate Excel file"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Users Export')
        
        # Định dạng
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        
        # Headers
        headers = ['STT', 'Tên người dùng']
        col = 2
        
        if self.include_login:
            headers.append('Login')
            col += 1
        if self.include_email:
            headers.append('Email')
            col += 1
        if self.include_phone:
            headers.append('Số điện thoại')
            col += 1
        if self.include_company:
            headers.append('Công ty')
            col += 1
        if self.include_department:
            headers.append('Phòng ban')
            col += 1
        if self.include_groups:
            headers.append('Nhóm quyền')
            col += 1
        if self.include_last_login:
            headers.append('Lần đăng nhập cuối')
            col += 1
        
        # Write headers
        for i, header in enumerate(headers):
            worksheet.write(0, i, header, header_format)
        
        # Write data
        row = 1
        for idx, user in enumerate(users, 1):
            col = 0
            worksheet.write(row, col, idx, cell_format)
            col += 1
            worksheet.write(row, col, user.name or '', cell_format)
            col += 1
            
            if self.include_login:
                worksheet.write(row, col, user.login or '', cell_format)
                col += 1
            if self.include_email:
                worksheet.write(row, col, user.email or '', cell_format)
                col += 1
            if self.include_phone:
                worksheet.write(row, col, user.phone or user.mobile or '', cell_format)
                col += 1
            if self.include_company:
                worksheet.write(row, col, user.company_id.name or '', cell_format)
                col += 1
            if self.include_department:
                worksheet.write(row, col, user.department_id.name if hasattr(user, 'department_id') else '', cell_format)
                col += 1
            if self.include_groups:
                groups = ', '.join(user.groups_id.mapped('name'))
                worksheet.write(row, col, groups, cell_format)
                col += 1
            if self.include_last_login:
                last_login = user.login_date.strftime('%d/%m/%Y %H:%M') if user.login_date else ''
                worksheet.write(row, col, last_login, cell_format)
                col += 1
            
            row += 1
        
        # Adjust column widths
        for i in range(len(headers)):
            if i == 0:  # STT column
                worksheet.set_column(i, i, 5)
            elif headers[i] == 'Nhóm quyền':
                worksheet.set_column(i, i, 50)
            elif headers[i] in ['Email', 'Tên người dùng']:
                worksheet.set_column(i, i, 25)
            else:
                worksheet.set_column(i, i, 15)
        
        workbook.close()
        output.seek(0)
        
        file_data = base64.b64encode(output.read())
        file_name = f'YODY_Users_Export_{fields.Date.today()}.xlsx'
        
        return file_data, file_name
    
    def _generate_csv(self, users):
        """Generate CSV file"""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Headers
        headers = ['STT', 'Tên người dùng']
        
        if self.include_login:
            headers.append('Login')
        if self.include_email:
            headers.append('Email')
        if self.include_phone:
            headers.append('Số điện thoại')
        if self.include_company:
            headers.append('Công ty')
        if self.include_department:
            headers.append('Phòng ban')
        if self.include_groups:
            headers.append('Nhóm quyền')
        if self.include_last_login:
            headers.append('Lần đăng nhập cuối')
        
        writer.writerow(headers)
        
        # Data
        for idx, user in enumerate(users, 1):
            row = [idx, user.name or '']
            
            if self.include_login:
                row.append(user.login or '')
            if self.include_email:
                row.append(user.email or '')
            if self.include_phone:
                row.append(user.phone or user.mobile or '')
            if self.include_company:
                row.append(user.company_id.name or '')
            if self.include_department:
                row.append(user.department_id.name if hasattr(user, 'department_id') else '')
            if self.include_groups:
                groups = ', '.join(user.groups_id.mapped('name'))
                row.append(groups)
            if self.include_last_login:
                last_login = user.login_date.strftime('%d/%m/%Y %H:%M') if user.login_date else ''
                row.append(last_login)
            
            writer.writerow(row)
        
        output.seek(0)
        file_data = base64.b64encode(output.getvalue().encode('utf-8'))
        file_name = f'YODY_Users_Export_{fields.Date.today()}.csv'
        
        return file_data, file_name
    
    def _create_export_log(self, user_count, file_name):
        """Create export log"""
        self.env['user.export.log'].create({
            'name': self.name,
            'user_count': user_count,
            'file_name': file_name,
            'file_type': self.file_type,
            'notes': f'Export type: {self.export_type}'
        })

    def download_file(self):
        """Download the exported file"""
        if not self.file_data or not self.file_name:
            raise UserError('No file available for download.')
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=user.export.wizard&field=file_data&id={self.id}&filename_field=file_name&download=true&filename={self.file_name}',
            'target': 'self',
        }