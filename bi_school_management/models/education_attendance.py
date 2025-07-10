from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EducationAttendance(models.Model):
    _name = "education.attendance"
    _description = "Education Attendance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    # Basic Information
    student_id = fields.Many2one(
        "education.student", string="Student", required=True, tracking=True
    )
    class_id = fields.Many2one(
        "education.class", string="Class", required=True, tracking=True
    )
    enrollment_id = fields.Many2one(
        "education.enrollment", string="Enrollment", tracking=True
    )
    date = fields.Date(
        string="Attendance Dates",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    # Attendance State
    state = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
            ("excused", "Excused Absence"),
        ],
        string="State",
        default="present",
        tracking=True,
    )

    # Additional Information
    teacher_id = fields.Many2one("hr.employee", string="Teacher", tracking=True)
    course_id = fields.Many2one(
        "education.course",
        string="Course",
        related="enrollment_id.course_id",
        store=True,
    )
    notes = fields.Text(string="Notes")

    # Time tracking
    check_in_time = fields.Datetime(string="Check In Time")
    check_out_time = fields.Datetime(string="Check Out Time")
    duration = fields.Float(
        string="Duration (Hours)", compute="_compute_duration", store=True
    )

    # Context-dependent fields
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        related="class_id.department_id",
        store=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        related="class_id.academic_year_id",
        store=True,
    )

    # Multi-company support
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    # SQL Constraints
    _sql_constraints = [
        (
            "unique_attendance",
            "unique(student_id, class_id, date)",
            "Student can only have one attendance record per class per day!",
        ),
    ]

    @api.depends("check_in_time", "check_out_time")
    def _compute_duration(self):
        for attendance in self:
            if attendance.check_in_time and attendance.check_out_time:
                delta = attendance.check_out_time - attendance.check_in_time
                attendance.duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                attendance.duration = 0.0

    # Python Constraints
    @api.constrains("check_in_time", "check_out_time")
    def _check_times(self):
        for attendance in self:
            if attendance.check_in_time and attendance.check_out_time:
                if attendance.check_out_time <= attendance.check_in_time:
                    raise ValidationError(
                        _("Check out time must be after check in time.")
                    )

    @api.constrains("date")
    def _check_date(self):
        for attendance in self:
            if attendance.date > fields.Date.context_today(attendance):
                raise ValidationError(_("Attendance date cannot be in the future."))
