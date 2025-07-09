from odoo import api, fields, models


class EducationCourseEnrollmentWizard(models.TransientModel):
    _name = "education.course.enrollment.wizard"
    _description = "Education Course Enrollment Wizard"

    student_id = fields.Many2one("education.student", string="Student", required=True)
    course_id = fields.Many2one("education.course", string="Course", required=True)

    def action_enroll_student(self):
        self.env["education.enrollment"].create(
            {
                "student_id": self.student_id.id,
                "course_id": self.course_id.id,
            }
        )
        return {"type": "ir.actions.act_window_close"}
