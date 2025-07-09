# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class EducationCourse(models.Model):
    _name = "education.course"
    _description = "Education Course"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Course Name", required=True, tracking=True)
    code = fields.Char(string="Course Code", tracking=True)
    department_id = fields.Many2one(
        "education.department", string="Department", required=True, tracking=True
    )
    teacher_id = fields.Many2one("hr.employee", string="Course Teacher", tracking=True)
    product_id = fields.Many2one("product.product", string="Product")
    fee_amount = fields.Monetary(
        string="Course Fee", currency_field="company_currency_id", tracking=True
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="department_id.school_id.company_id.currency_id",
        readonly=True,
    )

    # Course Information
    description = fields.Text(string="Description")
    duration_hours = fields.Float(string="Duration (Hours)")
    credits = fields.Integer(string="Credits")
    capacity = fields.Integer(
        string="Maximum Students",
        help="Maximum number of students that can enroll in this course",
    )
    required = fields.Boolean(
        string="Required Course",
        default=False,
        help="Check if this course is required for graduation",
    )

    # Prerequisites and Requirements
    prerequisite_ids = fields.Many2many(
        "education.course",
        "course_prerequisite_rel",
        "course_id",
        "prerequisite_id",
        string="Prerequisites",
    )

    # Relationships
    enrollment_ids = fields.One2many(
        "education.enrollment", "course_id", string="Enrollments"
    )

    # Computed Fields
    total_enrollments = fields.Integer(
        string="Total Enrollments", compute="_compute_totals", store=True
    )
    active_enrollments = fields.Integer(
        string="Active Enrollments", compute="_compute_totals", store=True
    )
    available_capacity = fields.Integer(
        string="Available Capacity", compute="_compute_totals", store=True
    )

    # Multi-company support
    company_id = fields.Many2one(
        "res.company", string="Company", related="department_id.company_id", store=True
    )

    # Additional Information
    active = fields.Boolean(string="Active", default=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.depends("enrollment_ids", "enrollment_ids.state", "capacity")
    def _compute_totals(self):
        for course in self:
            course.total_enrollments = len(course.enrollment_ids)
            course.active_enrollments = len(
                course.enrollment_ids.filtered(lambda e: e.state == "enrolled")
            )
            if course.capacity:
                course.available_capacity = course.capacity - course.active_enrollments
            else:
                course.available_capacity = 0
