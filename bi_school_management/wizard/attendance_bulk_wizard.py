from odoo import api, fields, models


class EducationAttendanceBulkWizard(models.TransientModel):
    _name = "education.attendance.bulk.wizard"
    _description = "Education Attendance Bulk Wizard"

    class_id = fields.Many2one("education.class", string="Class", required=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    attendance_line_ids = fields.One2many(
        "education.attendance.bulk.wizard.line", "wizard_id", string="Attendance Lines"
    )

    @api.onchange("class_id")
    def _onchange_class_id(self):
        self.attendance_line_ids = [(5, 0, 0)]
        if self.class_id:
            lines = []
            for student in self.class_id.student_ids:
                lines.append((0, 0, {"student_id": student.id}))
            self.attendance_line_ids = lines

    def action_mark_attendance(self):
        for line in self.attendance_line_ids:
            self.env["education.attendance"].create(
                {
                    "student_id": line.student_id.id,  # pylint: disable=no-member
                    "class_id": self.class_id.id,
                    "date": self.date,
                    "state": line.state,  # pylint: disable=no-member
                    "teacher_id": self.class_id.teacher_id.id,
                }
            )
        return {"type": "ir.actions.act_window_close"}


class EducationAttendanceBulkWizardLine(models.TransientModel):
    _name = "education.attendance.bulk.wizard.line"
    _description = "Education Attendance Bulk Wizard Line"

    wizard_id = fields.Many2one("education.attendance.bulk.wizard", string="Wizard")
    student_id = fields.Many2one("education.student", string="Student", required=True)
    state = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
        ],
        string="State",
        default="present",
    )
