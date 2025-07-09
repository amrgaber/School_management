from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BulkAttendanceWizard(models.TransientModel):
    _name = "education.bulk.attendance.wizard"
    _description = "Bulk Attendance Management Wizard"

    # Step 1: Selection Criteria
    step = fields.Selection(
        [
            ("selection", "Selection Criteria"),
            ("students", "Select Students"),
            ("attendance", "Mark Attendance"),
            ("summary", "Summary"),
        ],
        string="Step",
        default="selection",
    )

    # Selection Criteria Fields
    class_id = fields.Many2one("education.class", string="Class", required=True)
    date = fields.Date(
        string="Attendance Date", default=fields.Date.context_today, required=True
    )
    course_id = fields.Many2one("education.course", string="Course")
    teacher_id = fields.Many2one("hr.employee", string="Teacher")

    # Context-dependent filtering
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        related="class_id.department_id",
        readonly=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        related="class_id.academic_year_id",
        readonly=True,
    )

    # Student Selection (Step 2)
    student_ids = fields.Many2many("education.student", string="Students")
    all_students = fields.Boolean(string="Select All Students", default=True)

    # Attendance Data (Step 3)
    attendance_line_ids = fields.One2many(
        "education.bulk.attendance.line", "wizard_id", string="Attendance Lines"
    )

    # Bulk Actions
    bulk_state = fields.Selection(
        [
            ("present", "Mark All Present"),
            ("absent", "Mark All Absent"),
            ("custom", "Custom Selection"),
        ],
        string="Bulk Action",
        default="custom",
    )

    # Summary Information (Step 4)
    total_students = fields.Integer(
        string="Total Students", compute="_compute_summary", store=False
    )
    present_count = fields.Integer(
        string="Present Count", compute="_compute_summary", store=False
    )
    absent_count = fields.Integer(
        string="Absent Count", compute="_compute_summary", store=False
    )
    late_count = fields.Integer(
        string="Late Count", compute="_compute_summary", store=False
    )

    # Additional Options
    send_notifications = fields.Boolean(
        string="Send Notifications to Parents", default=False
    )
    create_activities = fields.Boolean(
        string="Create Activities for Absences", default=False
    )
    notes = fields.Text(string="General Notes")

    @api.depends("attendance_line_ids", "attendance_line_ids.state")
    def _compute_summary(self):
        for wizard in self:
            wizard.total_students = len(wizard.attendance_line_ids)
            wizard.present_count = len(
                wizard.attendance_line_ids.filtered(lambda l: l.state == "present")
            )
            wizard.absent_count = len(
                wizard.attendance_line_ids.filtered(lambda l: l.state == "absent")
            )
            wizard.late_count = len(
                wizard.attendance_line_ids.filtered(lambda l: l.state == "late")
            )

    # Context-dependent domain filtering
    @api.onchange("class_id")
    def _onchange_class_id(self):
        """Context: Demonstrates dynamic domain filtering based on class selection"""
        if self.class_id:
            # Update student domain based on class
            domain = [("class_id", "=", self.class_id.id), ("state", "=", "enrolled")]

            # Context-based filtering for active enrollments
            if self.env.context.get("only_active_enrollments"):
                active_students = (
                    self.env["education.enrollment"]
                    .search(
                        [
                            ("student_id.class_id", "=", self.class_id.id),
                            ("state", "=", "enrolled"),
                        ]
                    )
                    .mapped("student_id")
                )
                domain = [("id", "in", active_students.ids)]

            return {"domain": {"student_ids": domain}}

        return {"domain": {"student_ids": []}}

    @api.onchange("course_id")
    def _onchange_course_id(self):
        """Context: Filter students based on course enrollment"""
        if self.course_id:
            enrolled_students = (
                self.env["education.enrollment"]
                .search(
                    [("course_id", "=", self.course_id.id), ("state", "=", "enrolled")]
                )
                .mapped("student_id")
            )

            domain = [("id", "in", enrolled_students.ids)]
            if self.class_id:
                domain.append(("class_id", "=", self.class_id.id))

            return {"domain": {"student_ids": domain}}

    @api.onchange("all_students", "class_id")
    def _onchange_all_students(self):
        """Context: Auto-select students based on context flags"""
        if self.all_students and self.class_id:
            # Get students based on context
            if self.env.context.get("enrolled_only"):
                students = self.class_id.student_ids.filtered(
                    lambda s: s.state == "enrolled"
                )
            else:
                students = self.class_id.student_ids

            self.student_ids = [(6, 0, students.ids)]

    @api.onchange("bulk_state")
    def _onchange_bulk_state(self):
        """Context: Apply bulk state to all attendance lines"""
        if self.bulk_state != "custom" and self.attendance_line_ids:
            for line in self.attendance_line_ids:
                line.state = self.bulk_state

    # Step Navigation Methods
    def action_next_step(self):
        """Navigate to next step - Context: Multi-step wizard flow"""
        self.ensure_one()

        if self.step == "selection":
            # Validate selection criteria
            if not self.class_id or not self.date:
                raise UserError(_("Please select class and date."))

            # Check for existing attendance (context-dependent)
            if not self.env.context.get("allow_duplicate_attendance"):
                existing = self.env["education.attendance"].search(
                    [("class_id", "=", self.class_id.id), ("date", "=", self.date)]
                )
                if existing:
                    raise UserError(
                        _("Attendance already exists for this class and date.")
                    )

            self.step = "students"

        elif self.step == "students":
            # Validate student selection
            if not self.student_ids:
                raise UserError(_("Please select at least one student."))

            # Generate attendance lines
            self._generate_attendance_lines()
            self.step = "attendance"

        elif self.step == "attendance":
            # Validate attendance data
            if not self.attendance_line_ids:
                raise UserError(_("No attendance data to process."))

            self.step = "summary"

        return self._return_wizard()

    def action_previous_step(self):
        """Navigate to previous step"""
        self.ensure_one()

        if self.step == "students":
            self.step = "selection"
        elif self.step == "attendance":
            self.step = "students"
        elif self.step == "summary":
            self.step = "attendance"

        return self._return_wizard()

    def _generate_attendance_lines(self):
        """Generate attendance lines for selected students"""
        self.attendance_line_ids = [(5, 0, 0)]  # Clear existing lines

        lines = []
        for student in self.student_ids:
            # Context-based default state
            default_state = self.env.context.get("default_attendance_state", "present")

            lines.append(
                (
                    0,
                    0,
                    {
                        "student_id": student.id,
                        "state": default_state,
                        "notes": "",
                    },
                )
            )

        self.attendance_line_ids = lines

    def action_confirm(self):
        """Confirm and create attendance records - Context: Final processing with context flags"""
        self.ensure_one()

        if not self.attendance_line_ids:
            raise UserError(_("No attendance data to process."))

        # Create attendance records
        attendance_records = []
        for line in self.attendance_line_ids:
            # Prepare attendance values with context
            vals = self._prepare_attendance_vals(line)
            attendance_records.append(vals)

        # Batch create attendance records
        created_attendances = self.env["education.attendance"].create(
            attendance_records
        )

        # Post-processing based on context
        if self.send_notifications:
            self._send_parent_notifications(created_attendances)

        if self.create_activities:
            self._create_absence_activities(created_attendances)

        # Update enrollment attendance statistics (context-dependent)
        if self.env.context.get("update_enrollment_stats"):
            self._update_enrollment_statistics(created_attendances)

        return self._return_success_action(created_attendances)

    def _prepare_attendance_vals(self, line):
        """Prepare attendance record values - Context: Context-based configuration"""
        vals = {
            "student_id": line.student_id.id,
            "class_id": self.class_id.id,
            "date": self.date,
            "state": line.state,
            "notes": line.notes or self.notes,
            "teacher_id": self.teacher_id.id if self.teacher_id else False,
        }

        # Add enrollment context if course is specified
        if self.course_id:
            enrollment = self.env["education.enrollment"].search(
                [
                    ("student_id", "=", line.student_id.id),
                    ("course_id", "=", self.course_id.id),
                    ("state", "=", "enrolled"),
                ],
                limit=1,
            )
            if enrollment:
                vals["enrollment_id"] = enrollment.id

        # Add time tracking if context specifies
        if self.env.context.get("track_time"):
            vals.update(
                {
                    "check_in_time": datetime.combine(
                        self.date, datetime.min.time().replace(hour=8)
                    ),
                    "check_out_time": datetime.combine(
                        self.date, datetime.min.time().replace(hour=17)
                    ),
                }
            )

        return vals

    def _send_parent_notifications(self, attendances):
        """Send notifications to parents about attendance"""
        absent_attendances = attendances.filtered(
            lambda a: a.state in ["absent", "late"]
        )

        for attendance in absent_attendances:
            if attendance.student_id.parent_ids:
                # Create mail activity or send email notification
                for parent in attendance.student_id.parent_ids:
                    if parent.email:
                        # This would send email notification
                        pass

    def _create_absence_activities(self, attendances):
        """Create activities for absent students"""
        absent_attendances = attendances.filtered(lambda a: a.state == "absent")

        for attendance in absent_attendances:
            if self.teacher_id:
                attendance.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=self.teacher_id.user_id.id,
                    note=_("Student %s was absent on %s. Follow up required.")
                    % (attendance.student_id.name, attendance.date),
                )

    def _update_enrollment_statistics(self, attendances):
        """Update enrollment attendance statistics"""
        # This would update computed fields on enrollment records
        enrollments = attendances.mapped("enrollment_id").filtered(lambda e: e)
        for enrollment in enrollments:
            enrollment._compute_attendance_stats()

    def _return_wizard(self):
        """Return wizard action to continue in same window"""
        return {
            "type": "ir.actions.act_window",
            "res_model": "education.bulk.attendance.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def _return_success_action(self, attendances):
        """Return success action - Context: Context-dependent return action"""
        # Context determines what action to return after success
        if self.env.context.get("return_to_attendance_list"):
            return {
                "name": _("Attendance Records"),
                "type": "ir.actions.act_window",
                "res_model": "education.attendance",
                "view_mode": "list,form",
                "domain": [("id", "in", attendances.ids)],
                "context": {
                    "search_default_date": self.date,
                    "search_default_class_id": self.class_id.id,
                },
            }
        elif self.env.context.get("return_to_class"):
            return {
                "name": _("Class"),
                "type": "ir.actions.act_window",
                "res_model": "education.class",
                "res_id": self.class_id.id,
                "view_mode": "form",
            }
        else:
            # Default: Show success message and close wizard
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _(
                        "Attendance records created successfully for %d students."
                    )
                    % len(attendances),
                    "type": "success",
                },
            }

    # Advanced Context Methods
    @api.model
    def default_get(self, fields_list):
        """Override default_get to demonstrate context usage in wizard initialization"""
        res = super().default_get(fields_list)

        # Set defaults based on context
        if self.env.context.get("default_class_id"):
            res["class_id"] = self.env.context["default_class_id"]

        if self.env.context.get("default_course_id"):
            res["course_id"] = self.env.context["default_course_id"]

        if self.env.context.get("default_teacher_id"):
            res["teacher_id"] = self.env.context["default_teacher_id"]

        # Set date based on context
        if self.env.context.get("attendance_date"):
            res["date"] = self.env.context["attendance_date"]

        # Set bulk action based on context
        if self.env.context.get("default_bulk_state"):
            res["bulk_state"] = self.env.context["default_bulk_state"]

        # Set notification flags based on context
        if self.env.context.get("auto_notify_parents"):
            res["send_notifications"] = True

        if self.env.context.get("create_absence_activities"):
            res["create_activities"] = True

        return res


class BulkAttendanceLine(models.TransientModel):
    _name = "education.bulk.attendance.line"
    _description = "Bulk Attendance Line"

    wizard_id = fields.Many2one(
        "education.bulk.attendance.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    student_id = fields.Many2one("education.student", string="Student", required=True)
    state = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
            ("excused", "Excused"),
        ],
        string="Attendance",
        default="present",
        required=True,
    )
    notes = fields.Char(string="Notes")

    # Context-dependent display fields
    student_code = fields.Char(
        string="Student ID", related="student_id.student_id", readonly=True
    )
    last_attendance = fields.Char(
        string="Last Attendance", compute="_compute_last_attendance"
    )

    @api.depends("student_id")
    def _compute_last_attendance(self):
        """Compute last attendance for context display"""
        for line in self:
            if line.student_id:
                last_attendance = self.env["education.attendance"].search(
                    [
                        ("student_id", "=", line.student_id.id),
                        ("date", "<", line.wizard_id.date),
                    ],
                    order="date desc",
                    limit=1,
                )

                if last_attendance:
                    line.last_attendance = f"{last_attendance.date} - {dict(last_attendance._fields['state'].selection)[last_attendance.state]}"
                else:
                    line.last_attendance = _("No previous attendance")
            else:
                line.last_attendance = ""
