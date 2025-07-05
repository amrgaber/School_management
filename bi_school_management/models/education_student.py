# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class EducationStudent(models.Model):
    _name = 'education.student'
    _description = 'Education Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'student_id, name'

    # Basic Information
    partner_id = fields.Many2one('res.partner', string='Student', required=True, tracking=True)
    name = fields.Char(string='Student Name', related='partner_id.name', store=True, readonly=True)
    student_id = fields.Char(string='Student ID', required=True, copy=False, tracking=True)
    class_id = fields.Many2one('education.class', string='Class', tracking=True)
    enrollment_date = fields.Date(string='Enrollment Date', default=fields.Date.context_today, tracking=True)

    # State Management with Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('transferred', 'Transferred'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
        ('dropped', 'Dropped Out'),
    ], string='State', default='draft', tracking=True)

    # Relationships
    parent_ids = fields.Many2many('res.partner', string='Parents/Guardians')
    enrollment_ids = fields.One2many('education.enrollment', 'student_id', string='Course Enrollments')
    attendance_ids = fields.One2many('education.attendance', 'student_id', string='Attendance Records')

    # Computed Fields for Statistics
    total_enrollments = fields.Integer(string='Total Enrollments', compute='_compute_enrollments', store=True)
    active_enrollments = fields.Integer(string='Active Enrollments', compute='_compute_enrollments', store=True)
    attendance_percentage = fields.Float(string='Attendance %', compute='_compute_attendance_percentage', store=True)
    total_fees = fields.Monetary(string='Total Fees', compute='_compute_total_fees', store=True)
    outstanding_fees = fields.Monetary(string='Outstanding Fees', compute='_compute_total_fees', store=True)

    # Multi-company and Currency Support
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                 related='company_id.currency_id', readonly=True)

    # Additional Information
    date_of_birth = fields.Date(string='Date of Birth', related='partner_id.date_of_birth', store=True)
    age = fields.Integer(string='Age', compute='_compute_age')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender')

    # Academic Information
    academic_year_id = fields.Many2one('education.academic.year', string='Academic Year',
                                      related='class_id.academic_year_id', store=True)
    department_id = fields.Many2one('education.department', string='Department',
                                   related='class_id.department_id', store=True)
    school_id = fields.Many2one('education.school', string='School',
                               related='department_id.school_id', store=True)

    # Transfer Information
    transfer_reason = fields.Text(string='Transfer Reason')
    transfer_date = fields.Date(string='Transfer Date')
    transfer_to_school = fields.Char(string='Transfer To School')

    # Graduation Information
    graduation_date = fields.Date(string='Graduation Date')
    graduation_grade = fields.Selection([
        ('distinction', 'Distinction'),
        ('first_class', 'First Class'),
        ('second_class', 'Second Class'),
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], string='Graduation Grade')

    # SQL Constraints
    _sql_constraints = [
        ('student_id_unique', 'unique(student_id, company_id)', 'Student ID must be unique per company!'),
        ('positive_attendance', 'check(attendance_percentage >= 0 AND attendance_percentage <= 100)',
         'Attendance percentage must be between 0 and 100!'),
    ]

    # Computed Methods
    @api.depends('enrollment_ids', 'enrollment_ids.state')
    def _compute_enrollments(self):
        for student in self:
            student.total_enrollments = len(student.enrollment_ids)
            student.active_enrollments = len(student.enrollment_ids.filtered(lambda e: e.state == 'enrolled'))

    @api.depends('attendance_ids', 'attendance_ids.state')
    def _compute_attendance_percentage(self):
        for student in self:
            if student.attendance_ids:
                total_days = len(student.attendance_ids)
                present_days = len(student.attendance_ids.filtered(lambda a: a.state == 'present'))
                student.attendance_percentage = (present_days / total_days) * 100 if total_days > 0 else 0.0
            else:
                student.attendance_percentage = 0.0

    @api.depends('enrollment_ids', 'enrollment_ids.invoice_id', 'enrollment_ids.invoice_id.payment_state')
    def _compute_total_fees(self):
        for student in self:
            invoices = student.enrollment_ids.mapped('invoice_id').filtered(lambda inv: inv.move_type == 'out_invoice')
            student.total_fees = sum(invoices.mapped('amount_total'))
            student.outstanding_fees = sum(invoices.filtered(lambda inv: inv.payment_state != 'paid').mapped('amount_total'))

    @api.depends('date_of_birth')
    def _compute_age(self):
        for student in self:
            if student.date_of_birth:
                today = fields.Date.context_today(student)
                student.age = today.year - student.date_of_birth.year - \
                             ((today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day))
            else:
                student.age = 0

    # Workflow Methods
    def action_enroll(self):
        """Enroll student - Context: Demonstrates state workflow with validation"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft students can be enrolled.'))

        # Validation using context
        if self.env.context.get('skip_validation'):
            # Context flag to skip validation for bulk operations
            pass
        else:
            self._validate_enrollment()

        self.write({
            'state': 'enrolled',
            'enrollment_date': fields.Date.context_today(self)
        })

        # Create activity for class teacher
        if self.class_id.teacher_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.class_id.teacher_id.user_id.id,
                note=_('New student %s enrolled in your class.') % self.name
            )

        return True

    def action_transfer(self):
        """Transfer student - Context: Demonstrates wizard with context passing"""
        self.ensure_one()
        if self.state not in ['enrolled', 'suspended']:
            raise UserError(_('Only enrolled or suspended students can be transferred.'))

        # Return wizard with context
        return {
            'name': _('Transfer Student'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.student.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
                'default_current_class_id': self.class_id.id,
                'default_current_school_id': self.school_id.id,
                'transfer_mode': True,
            }
        }

    def action_graduate(self):
        """Graduate student - Context: Demonstrates conditional workflow"""
        self.ensure_one()
        if self.state != 'enrolled':
            raise UserError(_('Only enrolled students can be graduated.'))

        # Check if student has completed all required courses
        if not self._check_graduation_requirements():
            raise UserError(_('Student has not completed all graduation requirements.'))

        self.write({
            'state': 'graduated',
            'graduation_date': fields.Date.context_today(self)
        })

        # Create graduation certificate (context-dependent)
        if self.env.context.get('create_certificate'):
            self._create_graduation_certificate()

        return True

    def action_suspend(self):
        """Suspend student - Context: Demonstrates reason tracking"""
        self.ensure_one()
        if self.state != 'enrolled':
            raise UserError(_('Only enrolled students can be suspended.'))

        # Get suspension reason from context
        reason = self.env.context.get('suspension_reason', 'Administrative decision')

        self.write({'state': 'suspended'})
        self.message_post(
            body=_('Student suspended. Reason: %s') % reason,
            message_type='notification'
        )

        return True

    def action_reactivate(self):
        """Reactivate suspended student"""
        self.ensure_one()
        if self.state != 'suspended':
            raise UserError(_('Only suspended students can be reactivated.'))

        self.write({'state': 'enrolled'})
        return True

    def action_dropout(self):
        """Mark student as dropped out"""
        self.ensure_one()
        if self.state not in ['enrolled', 'suspended']:
            raise UserError(_('Only enrolled or suspended students can be marked as dropped out.'))

        self.write({'state': 'dropped'})
        return True

    # Validation Methods
    def _validate_enrollment(self):
        """Validate enrollment requirements"""
        if not self.partner_id:
            raise ValidationError(_('Student partner is required.'))

        if not self.class_id:
            raise ValidationError(_('Class assignment is required for enrollment.'))

        # Check class capacity
        if self.class_id.capacity and len(self.class_id.student_ids) >= self.class_id.capacity:
            raise ValidationError(_('Class capacity exceeded. Cannot enroll more students.'))

        # Check age requirements (context-dependent)
        min_age = self.env.context.get('min_age', 5)
        if self.age and self.age < min_age:
            raise ValidationError(_('Student is too young for enrollment. Minimum age: %d') % min_age)

    def _check_graduation_requirements(self):
        """Check if student meets graduation requirements"""
        # Check minimum attendance
        if self.attendance_percentage < 75:
            return False

        # Check if all required courses are completed
        required_courses = self.class_id.department_id.course_ids.filtered('required')
        completed_courses = self.enrollment_ids.filtered(lambda e: e.state == 'completed').mapped('course_id')

        return all(course in completed_courses for course in required_courses)

    def _create_graduation_certificate(self):
        """Create graduation certificate document"""
        # This would integrate with documents module if available
        pass

    # Smart Button Actions with Context
    def action_view_enrollments(self):
        """View student enrollments - Context: Smart button with filtering"""
        self.ensure_one()
        action = self.env.ref('bi_school_management.action_education_enrollment').read()[0]
        action.update({
            'domain': [('student_id', '=', self.id)],
            'context': {
                'default_student_id': self.id,
                'search_default_student_id': self.id,
                'student_context': True,
            }
        })
        return action

    def action_view_invoice(self):
        """View all invoices related to the student's enrollments"""
        self.ensure_one()
        invoice_ids = self.enrollment_ids.mapped('invoice_id').filtered(lambda inv: inv.move_type == 'out_invoice').ids
        return {
            'name': _('Student Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoice_ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_move_type': 'out_invoice',
                'search_default_partner_id': self.partner_id.id,
            }
        }

    def action_view_attendance(self):
        """View student attendance - Context: Date-based filtering"""
        self.ensure_one()
        action = self.env.ref('bi_school_management.action_education_attendance').read()[0]

        # Context-based date filtering
        date_from = self.env.context.get('date_from', fields.Date.context_today(self) - timedelta(days=30))
        date_to = self.env.context.get('date_to', fields.Date.context_today(self))

        action.update({
            'domain': [
                ('student_id', '=', self.id),
                ('date', '>=', date_from),
                ('date', '<=', date_to)
            ],
            'context': {
                'default_student_id': self.id,
                'search_default_student_id': self.id,
                'attendance_context': True,
            }
        })
        return action

    def action_create_enrollment(self):
        """Create new enrollment - Context: Wizard with defaults"""
        self.ensure_one()
        return {
            'name': _('Create Enrollment'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.course.enrollment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
                'default_department_id': self.department_id.id,
                'enrollment_context': True,
            }
        }

    # Override Methods
    @api.model
    def create(self, vals):
        """Override create to demonstrate context usage in creation"""
        # Auto-generate student ID if not provided
        if not vals.get('student_id'):
            vals['student_id'] = self._generate_student_id(vals)

        # Set default class based on context
        if not vals.get('class_id') and self.env.context.get('default_class_id'):
            vals['class_id'] = self.env.context.get('default_class_id')

        student = super(EducationStudent, self).create(vals)

        # Auto-enroll if context flag is set
        if self.env.context.get('auto_enroll'):
            student.action_enroll()

        return student

    def _generate_student_id(self, vals):
        """Generate unique student ID"""
        sequence = self.env['ir.sequence'].next_by_code('education.student') or '0001'
        school_code = 'STU'

        # Use school code from context if available
        if self.env.context.get('school_id'):
            school = self.env['education.school'].browse(self.env.context['school_id'])
            school_code = school.code or 'STU'

        return f"{school_code}{sequence}"

    # Python Constraints
    @api.constrains('enrollment_date', 'graduation_date')
    def _check_dates(self):
        for student in self:
            if student.graduation_date and student.enrollment_date:
                if student.graduation_date < student.enrollment_date:
                    raise ValidationError(_('Graduation date cannot be before enrollment date.'))

    @api.constrains('age')
    def _check_age(self):
        for student in self:
            if student.age and student.age < 3:
                raise ValidationError(_('Student age cannot be less than 3 years.'))
            if student.age and student.age > 100:
                raise ValidationError(_('Student age cannot be more than 100 years.'))
