# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class EducationSchool(models.Model):
    _name = 'education.school'
    _description = 'Education School'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='School Name', required=True, tracking=True)
    code = fields.Char(string='School Code', required=True, tracking=True)

    # Multi-company support
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, tracking=True)

    # Contact Information
    partner_id = fields.Many2one('res.partner', string='Contact', tracking=True)
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')

    # Relationships
    department_ids = fields.One2many('education.department', 'school_id', string='Departments')
    academic_year_ids = fields.One2many('education.academic.year', 'school_id', string='Academic Years')

    # Additional Information
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    established_date = fields.Date(string='Established Date')

    # Computed Fields
    total_departments = fields.Integer(string='Total Departments', compute='_compute_totals', store=True)
    total_students = fields.Integer(string='Total Students', compute='_compute_totals', store=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'School code must be unique.'),
    ]

    @api.depends('department_ids', 'department_ids.student_ids')
    def _compute_totals(self):
        for school in self:
            school.total_departments = len(school.department_ids)
            school.total_students = len(school.department_ids.mapped('student_ids'))
