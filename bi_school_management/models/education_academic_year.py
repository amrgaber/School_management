# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EducationAcademicYear(models.Model):
    _name = "education.academic.year"
    _description = "Academic Year"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc"

    name = fields.Char(string="Academic Year", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    school_id = fields.Many2one(
        "education.school", string="School", required=True, tracking=True
    )

    # Date Information
    start_date = fields.Date(string="Start Date", required=True, tracking=True)
    end_date = fields.Date(string="End Date", required=True, tracking=True)

    # Status
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("closed", "Closed"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Relationships
    class_ids = fields.One2many("education.class", "academic_year_id", string="Classes")

    # Computed Fields
    total_classes = fields.Integer(
        string="Total Classes", compute="_compute_totals", store=True
    )
    total_students = fields.Integer(
        string="Total Students", compute="_compute_totals", store=True
    )

    # Multi-company support
    company_id = fields.Many2one(
        "res.company", string="Company", related="school_id.company_id", store=True
    )

    # Additional Information
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)

    # SQL Constraints
    _sql_constraints = [
        (
            "date_check",
            "check(end_date > start_date)",
            "End date must be after start date!",
        ),
        (
            "name_school_unique",
            "unique(name, school_id)",
            "Academic year name must be unique per school!",
        ),
    ]

    @api.depends("class_ids", "class_ids.student_ids")
    def _compute_totals(self):
        for year in self:
            year.total_classes = len(year.class_ids)
            year.total_students = len(year.class_ids.mapped("student_ids"))

    # Workflow Methods
    def action_activate(self):
        """Activate academic year"""
        for year in self:
            if year.state != "draft":
                raise ValidationError(_("Only draft academic years can be activated."))
            year.write({"state": "active"})
        return True

    def action_close(self):
        """Close academic year"""
        for year in self:
            if year.state != "active":
                raise ValidationError(_("Only active academic years can be closed."))
            year.write({"state": "closed"})
        return True

    # Python Constraints
    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for year in self:
            if year.start_date and year.end_date:
                if year.end_date <= year.start_date:
                    raise ValidationError(_("End date must be after start date."))
