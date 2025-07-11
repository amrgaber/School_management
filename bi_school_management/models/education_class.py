from odoo import _, api, fields, models


class EducationClass(models.Model):
    _name = "education.class"
    _description = "Education Class"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Class Name", required=True, tracking=True)
    code = fields.Char(string="Class Code", tracking=True)
    department_id = fields.Many2one(
        "education.department", string="Department", required=True, tracking=True
    )
    academic_year_id = fields.Many2one(
        "education.academic.year", string="Academic Year", required=True, tracking=True
    )
    teacher_id = fields.Many2one("hr.employee", string="Class Teacher", tracking=True)
    capacity = fields.Integer(
        string="Maximum Students", help="Maximum number of students in this class"
    )

    # Relationships
    student_ids = fields.One2many("education.student", "class_id", string="Students")
    course_ids = fields.Many2many("education.course", string="Courses")

    # Computed Fields
    total_students = fields.Integer(compute="_compute_totals", store=True)
    available_capacity = fields.Integer(
        string="Available Capacity", compute="_compute_totals", store=True
    )

    # Multi-company support
    company_id = fields.Many2one(
        "res.company", string="Company", related="department_id.company_id", store=True
    )

    # Additional Information
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)

    gender = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
        ],
        string="Gender",
        help="Filter students by this gender. Not required.",
    )

    @api.depends("student_ids", "capacity")
    def _compute_totals(self):
        for class_rec in self:
            class_rec.total_students = len(class_rec.student_ids)
            if class_rec.capacity:
                class_rec.available_capacity = (
                    class_rec.capacity - class_rec.total_students
                )
            else:
                class_rec.available_capacity = 0

    def action_view_students(self):
        return {
            "name": "Students",
            "view_mode": "list,form",
            "res_model": "education.student",
            "type": "ir.actions.act_window",
            "domain": [("class_id", "=", self.id)],
            "context": {"default_class_id": self.id},
        }

    def action_mark_attendance(self):
        return {
            "name": "Mark Attendance",
            "view_mode": "form",
            "res_model": "education.attendance.bulk.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {
                "default_class_id": self.id,
                "default_date": fields.Date.context_today(self),
            },
        }

    def action_course_enrollments(self):
        return {
            "name": "Course Enrollments",
            "view_mode": "list,form",
            "res_model": "education.enrollment",
            "type": "ir.actions.act_window",
            "domain": [("student_id.class_id", "=", self.id)],
            "context": {"default_class_id": self.id, "search_default_active": 1},
        }

    def action_add_student(self):
        """Open the student selection window to add students to this class."""
        self.ensure_one()
        return {
            "name": "Select Students",
            "type": "ir.actions.act_window",
            "res_model": "education.student",
            "view_mode": "kanban,list,form",
            "target": "current",
            "context": {"add_to_class": True, "active_class_id": self.id},
        }

    def action_create_test_student(self):
        """Create a test student for this class using the @api.model method from the student model."""
        self.ensure_one()
        student_model = self.env["education.student"]
        # Example: create a student named 'Test Student' in this class
        new_student = student_model.create_student_with_defaults(
            "Test Student", class_id=self.id
        )
        # Optionally, return an action to open the new student record
        return {
            "type": "ir.actions.act_window",
            "name": "Test Student",
            "res_model": "education.student",
            "view_mode": "form",
            "res_id": new_student.id,
            "target": "current",
        }

    @api.returns("education.student")
    def get_students(self):
        return self.student_ids

    @api.readonly
    def get_student_statistics(self):
        """Return statistics about students in this class (readonly)."""
        stats = {
            "total": len(self.student_ids),
            "enrolled": len(self.student_ids.filtered(lambda s: s.state == "enrolled")),
            "graduated": len(
                self.student_ids.filtered(lambda s: s.state == "graduated")
            ),
        }
        return stats
