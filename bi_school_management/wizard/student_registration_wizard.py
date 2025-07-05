# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EducationStudentRegistrationWizard(models.TransientModel):
    _name = 'education.student.registration.wizard'
    _description = 'Education Student Registration Wizard'

    student_id = fields.Many2one('education.student', string='Student')
    class_id = fields.Many2one('education.class', string='Class')

    def action_register_student(self):
        self.student_id.write({'class_id': self.class_id.id})
        return {'type': 'ir.actions.act_window_close'}
