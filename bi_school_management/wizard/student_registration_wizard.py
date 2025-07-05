# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EducationStudentRegistrationWizard(models.TransientModel):
    _name = 'education.student.registration.wizard'
    _description = 'Education Student Registration Wizard'

    registration_type = fields.Selection([
        ('existing', 'Register Existing Student'),
        ('new', 'Register New Student'),
    ], string='Registration Type', default='existing', required=True)

    student_id = fields.Many2one('education.student', string='Student')
    class_id = fields.Many2one('education.class', string='Class', required=True)

    # Fields for new student creation
    new_student_name = fields.Char(string='Student Name')
    new_student_date_of_birth = fields.Date(string='Date of Birth')
    new_student_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender')
    new_student_parent_ids = fields.Many2many('res.partner', string='Parents/Guardians')

    @api.onchange('registration_type')
    def _onchange_registration_type(self):
        if self.registration_type == 'new':
            self.student_id = False
        else:
            self.new_student_name = False
            self.new_student_date_of_birth = False
            self.new_student_gender = False
            self.new_student_parent_ids = False

    def action_register_student(self):
        if self.registration_type == 'existing':
            if not self.student_id:
                raise UserError(_('Please select an existing student.'))
            self.student_id.write({'class_id': self.class_id.id})
        elif self.registration_type == 'new':
            if not self.new_student_name:
                raise UserError(_('Please enter the new student\'s name.'))

            # Create res.partner for the new student
            partner_vals = {
                'name': self.new_student_name,
                'date_of_birth': self.new_student_date_of_birth,
                'gender': self.new_student_gender,
                'is_student': True, # Custom field on res.partner if exists
            }
            new_partner = self.env['res.partner'].create(partner_vals)

            # Create education.student record
            student_vals = {
                'partner_id': new_partner.id,
                'class_id': self.class_id.id,
                'enrollment_date': fields.Date.context_today(self),
                'parent_ids': [(6, 0, self.new_student_parent_ids.ids)],
                'state': 'enrolled', # Automatically enroll new students
            }
            # Pass context to student creation for auto-enrollment and ID generation
            new_student = self.env['education.student'].with_context(
                auto_enroll=True,
                school_id=self.class_id.department_id.school_id.id
            ).create(student_vals)

        return {'type': 'ir.actions.act_window_close'}
