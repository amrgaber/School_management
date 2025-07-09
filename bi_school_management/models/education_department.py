from odoo import _, api, fields, models


class EducationDepartment(models.Model):
    _name = "education.department"
    _description = "Education Department"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Department Name", required=True, tracking=True)
    code = fields.Char(string="Department Code", tracking=True)
    school_id = fields.Many2one(
        "education.school", string="School", required=True, tracking=True
    )
    head_teacher_id = fields.Many2one(
        "hr.employee", string="Head Teacher", tracking=True
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account"
    )

    # Relationships
    course_ids = fields.One2many("education.course", "department_id", string="Courses")
    class_ids = fields.One2many("education.class", "department_id", string="Classes")
    student_ids = fields.One2many(
        "education.student", "department_id", string="Students"
    )

    # Computed Fields
    total_courses = fields.Integer(
        string="Total Courses", compute="_compute_totals", store=True
    )
    total_classes = fields.Integer(
        string="Total Classes", compute="_compute_totals", store=True
    )
    total_students = fields.Integer(
        string="Total Students", compute="_compute_totals", store=True
    )

    # Multi-company support
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    # Additional Information
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)

    @api.depends("course_ids", "class_ids", "student_ids")
    def _compute_totals(self):
        for department in self:
            department.total_courses = len(department.course_ids)
            department.total_classes = len(department.class_ids)
            department.total_students = len(department.student_ids)
