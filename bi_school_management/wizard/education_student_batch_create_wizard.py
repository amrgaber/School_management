from odoo import fields, models


class EducationStudentBatchCreateWizard(models.TransientModel):
    _name = "education.student.batch.create.wizard"
    _description = "Batch Create Students Wizard"

    class_id = fields.Many2one("education.class", string="Class", required=True)
    student_line_ids = fields.One2many(
        "education.student.batch.create.line", "wizard_id", string="Students"
    )

    def action_create_students(self):
        vals_list = []
        for line in self.student_line_ids:
            vals_list.append(
                {
                    "name": line.name,
                    "class_id": self.class_id.id,
                }
            )
        students = self.env["education.student"].create(vals_list)
        return {
            "type": "ir.actions.act_window",
            "name": "Created Students",
            "res_model": "education.student",
            "view_mode": "list,form",
            "domain": [("id", "in", students.ids)],
            "target": "current",
        }


class EducationStudentBatchCreateLine(models.TransientModel):
    _name = "education.student.batch.create.line"
    _description = "Batch Create Student Line"

    wizard_id = fields.Many2one(
        "education.student.batch.create.wizard", required=True, ondelete="cascade"
    )
    name = fields.Char(string="Student Name", required=True)
