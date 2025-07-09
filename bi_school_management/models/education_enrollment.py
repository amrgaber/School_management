# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class EducationEnrollment(models.Model):
    _name = "education.enrollment"
    _description = "Education Enrollment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "enrollment_date desc, id desc"

    # Basic Information
    student_id = fields.Many2one(
        "education.student", string="Student", required=True, tracking=True
    )
    course_id = fields.Many2one(
        "education.course", string="Course", required=True, tracking=True
    )
    enrollment_date = fields.Date(
        string="Enrollment Date", default=fields.Date.context_today, tracking=True
    )

    # State Management with Workflow
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("enrolled", "Enrolled"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("failed", "Failed"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Financial Integration
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    payment_state = fields.Selection(
        related="invoice_id.payment_state", string="Payment Status", readonly=True
    )
    amount_total = fields.Monetary(
        string="Total Amount", related="invoice_id.amount_total", readonly=True
    )
    amount_due = fields.Monetary(
        string="Amount Due", related="invoice_id.amount_residual", readonly=True
    )

    # Academic Information
    grade = fields.Selection(
        [
            ("a+", "A+"),
            ("a", "A"),
            ("b+", "B+"),
            ("b", "B"),
            ("c+", "C+"),
            ("c", "C"),
            ("d", "D"),
            ("f", "F"),
        ],
        string="Grade",
    )

    score = fields.Float(string="Score (%)", help="Score percentage (0-100)")
    completion_date = fields.Date(string="Completion Date")

    # Relationships
    attendance_ids = fields.One2many(
        "education.attendance", "enrollment_id", string="Attendance Records"
    )

    # Computed Fields
    attendance_percentage = fields.Float(
        string="Attendance %", compute="_compute_attendance_stats", store=True
    )
    total_classes = fields.Integer(
        string="Total Classes", compute="_compute_attendance_stats", store=True
    )
    attended_classes = fields.Integer(
        string="Attended Classes", compute="_compute_attendance_stats", store=True
    )

    # Multi-company and Currency Support
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )

    # Context-dependent fields
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        related="course_id.department_id",
        store=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        related="student_id.academic_year_id",
        store=True,
    )

    # Additional Information
    notes = fields.Text(string="Notes")
    cancellation_reason = fields.Text(string="Cancellation Reason")

    # SQL Constraints
    _sql_constraints = [
        (
            "unique_enrollment",
            "unique(student_id, course_id)",
            "Student can only be enrolled in a course once!",
        ),
        (
            "valid_score",
            "check(score >= 0 AND score <= 100)",
            "Score must be between 0 and 100!",
        ),
    ]

    # Computed Methods
    @api.depends("attendance_ids", "attendance_ids.state")
    def _compute_attendance_stats(self):
        for enrollment in self:
            if enrollment.attendance_ids:
                enrollment.total_classes = len(enrollment.attendance_ids)
                enrollment.attended_classes = len(
                    enrollment.attendance_ids.filtered(lambda a: a.state == "present")
                )
                enrollment.attendance_percentage = (
                    (enrollment.attended_classes / enrollment.total_classes) * 100
                    if enrollment.total_classes > 0
                    else 0.0
                )
            else:
                enrollment.total_classes = 0
                enrollment.attended_classes = 0
                enrollment.attendance_percentage = 0.0

    # Workflow Methods with Context Usage
    def action_confirm(self):
        """Confirm enrollment - Context: Demonstrates validation with context flags"""
        for enrollment in self:
            if enrollment.state != "draft":
                raise UserError(_("Only draft enrollments can be confirmed."))

            # Context-based validation
            if not self.env.context.get("skip_prerequisites"):
                enrollment._check_prerequisites()

            if not self.env.context.get("skip_capacity"):
                enrollment._check_course_capacity()

            enrollment.write({"state": "confirmed"})

            # Send notification to teacher (context-dependent)
            if (
                self.env.context.get("notify_teacher")
                and enrollment.course_id.teacher_id
            ):
                enrollment._notify_teacher_enrollment()

        return True

    def action_enroll(self):
        """Enroll student - Context: Demonstrates financial integration with context"""
        for enrollment in self:
            if enrollment.state != "confirmed":
                raise UserError(_("Only confirmed enrollments can be enrolled."))

            # Generate invoice (context-dependent)
            if self.env.context.get("generate_invoice", True):
                enrollment._generate_invoice()

            enrollment.write(
                {
                    "state": "enrolled",
                    "enrollment_date": fields.Date.context_today(enrollment),
                }
            )

            # Create initial attendance records (context-dependent)
            if self.env.context.get("create_attendance"):
                enrollment._create_attendance_records()

        return True

    def action_complete(self):
        """Complete enrollment - Context: Demonstrates grade validation"""
        for enrollment in self:
            if enrollment.state != "enrolled":
                raise UserError(_("Only enrolled students can complete the course."))

            # Validate completion requirements
            min_attendance = self.env.context.get("min_attendance_percentage", 75)
            if enrollment.attendance_percentage < min_attendance:
                raise UserError(
                    _("Student does not meet minimum attendance requirement (%d%%).")
                    % min_attendance
                )

            # Auto-assign grade based on score (context-dependent)
            if enrollment.score and self.env.context.get("auto_grade"):
                enrollment._auto_assign_grade()

            enrollment.write(
                {
                    "state": "completed",
                    "completion_date": fields.Date.context_today(enrollment),
                }
            )

            # Issue certificate (context-dependent)
            if self.env.context.get("issue_certificate"):
                enrollment._issue_certificate()

        return True

    def action_cancel(self):
        """Cancel enrollment - Context: Demonstrates refund processing"""
        for enrollment in self:
            if enrollment.state in ["completed", "cancelled"]:
                raise UserError(
                    _("Cannot cancel completed or already cancelled enrollments.")
                )

            # Get cancellation reason from context
            reason = self.env.context.get("cancellation_reason", "Student request")

            enrollment.write({"state": "cancelled", "cancellation_reason": reason})

            # Process refund (context-dependent)
            if enrollment.invoice_id and self.env.context.get("process_refund"):
                enrollment._process_refund()

        return True

    def action_fail(self):
        """Mark enrollment as failed"""
        for enrollment in self:
            if enrollment.state != "enrolled":
                raise UserError(_("Only enrolled students can be marked as failed."))

            enrollment.write({"state": "failed"})

        return True

    # Validation Methods
    def _check_prerequisites(self):
        """Check if student has completed prerequisite courses"""
        for enrollment in self:
            if enrollment.course_id.prerequisite_ids:
                completed_courses = enrollment.student_id.enrollment_ids.filtered(
                    lambda e: e.state == "completed"
                ).mapped("course_id")

                missing_prerequisites = (
                    enrollment.course_id.prerequisite_ids - completed_courses
                )
                if missing_prerequisites:
                    raise ValidationError(
                        _("Student has not completed prerequisite courses: %s")
                        % ", ".join(missing_prerequisites.mapped("name"))
                    )

    def _check_course_capacity(self):
        """Check if course has available capacity"""
        for enrollment in self:
            if (
                hasattr(enrollment.course_id, "capacity")
                and enrollment.course_id.capacity
            ):
                current_enrollments = len(
                    enrollment.course_id.enrollment_ids.filtered(
                        lambda e: e.state in ["confirmed", "enrolled"]
                    )
                )
                if current_enrollments >= enrollment.course_id.capacity:
                    raise ValidationError(
                        _("Course capacity exceeded. Cannot enroll more students.")
                    )

    # Financial Integration Methods
    def _generate_invoice(self):
        """Generate invoice for enrollment - Context: Demonstrates accounting integration"""
        self.ensure_one()

        if self.invoice_id:
            raise UserError(_("Invoice already exists for this enrollment."))

        if not self.course_id.fee_amount:
            return  # No fee, no invoice needed

        # Get invoice values with context
        invoice_vals = self._prepare_invoice_vals()

        # Create invoice
        invoice = self.env["account.move"].create(invoice_vals)
        self.invoice_id = invoice.id

        # Auto-confirm invoice (context-dependent)
        if self.env.context.get("auto_confirm_invoice"):
            invoice.action_post()

        return invoice

    def _prepare_invoice_vals(self):
        """Prepare invoice values - Context: Demonstrates context-based configuration"""
        self.ensure_one()

        # Get journal from context or default
        journal_id = self.env.context.get("invoice_journal_id")
        if not journal_id:
            journal = self.env["account.journal"].search(
                [("type", "=", "sale"), ("company_id", "=", self.company_id.id)],
                limit=1,
            )
            journal_id = journal.id if journal else False

        # Get payment terms from context
        payment_term_id = self.env.context.get("payment_term_id")

        return {
            "move_type": "out_invoice",
            "partner_id": self.student_id.partner_id.id,
            "journal_id": journal_id,
            "payment_term_id": payment_term_id,
            "invoice_date": fields.Date.context_today(self),
            "ref": f"Enrollment: {self.course_id.name}",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": (
                            self.course_id.product_id.id
                            if self.course_id.product_id
                            else False
                        ),
                        "name": f"Course Enrollment: {self.course_id.name}",
                        "quantity": 1,
                        "price_unit": self.course_id.fee_amount,
                        "account_id": self._get_income_account(),
                    },
                )
            ],
        }

    def _get_income_account(self):
        """Get income account for enrollment"""
        if self.course_id.product_id:
            return self.course_id.product_id.property_account_income_id.id

        # Default income account
        account = self.env["account.account"].search(
            [("account_type", "=", "income"), ("company_id", "=", self.company_id.id)],
            limit=1,
        )
        return account.id if account else False

    def _process_refund(self):
        """Process refund for cancelled enrollment"""
        self.ensure_one()

        if not self.invoice_id or self.invoice_id.payment_state == "not_paid":
            return  # No payment to refund

        # Create credit note
        refund_vals = {
            "move_type": "out_refund",
            "partner_id": self.invoice_id.partner_id.id,
            "ref": f"Refund for: {self.invoice_id.name}",
            "reversed_entry_id": self.invoice_id.id,
        }

        refund = self.env["account.move"].create(refund_vals)

        # Auto-confirm refund (context-dependent)
        if self.env.context.get("auto_confirm_refund"):
            refund.action_post()

    # Helper Methods
    def _notify_teacher_enrollment(self):
        """Notify teacher about new enrollment"""
        self.ensure_one()

        self.activity_schedule(
            "mail.mail_activity_data_todo",
            user_id=self.course_id.teacher_id.user_id.id,
            note=_("New student %s enrolled in course %s.")
            % (self.student_id.name, self.course_id.name),
        )

    def _auto_assign_grade(self):
        """Auto-assign grade based on score"""
        self.ensure_one()

        if self.score >= 95:
            self.grade = "a+"
        elif self.score >= 90:
            self.grade = "a"
        elif self.score >= 85:
            self.grade = "b+"
        elif self.score >= 80:
            self.grade = "b"
        elif self.score >= 75:
            self.grade = "c+"
        elif self.score >= 70:
            self.grade = "c"
        elif self.score >= 60:
            self.grade = "d"
        else:
            self.grade = "f"

    def _issue_certificate(self):
        """Issue completion certificate"""
        # This would integrate with documents module if available
        pass

    def _create_attendance_records(self):
        """Create initial attendance records for the course"""
        # This would create attendance records based on course schedule
        pass

    # Smart Button Actions with Context
    def action_view_invoice(self):
        """View enrollment invoice - Context: Financial view"""
        self.ensure_one()

        if not self.invoice_id:
            raise UserError(_("No invoice found for this enrollment."))

        return {
            "name": _("Invoice"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
            "context": {
                "enrollment_context": True,
                "default_move_type": "out_invoice",
            },
        }

    def action_view_attendance(self):
        """View enrollment attendance - Context: Attendance filtering"""
        self.ensure_one()

        action = self.env.ref(
            "bi_school_management.action_education_attendance"
        ).read()[0]
        action.update(
            {
                "domain": [("enrollment_id", "=", self.id)],
                "context": {
                    "default_enrollment_id": self.id,
                    "default_student_id": self.student_id.id,
                    "default_course_id": self.course_id.id,
                    "enrollment_attendance_context": True,
                },
            }
        )
        return action

    # Override Methods
    @api.model
    def create(self, vals):
        """Override create to demonstrate context usage"""
        # Set default course based on context
        if not vals.get("course_id") and self.env.context.get("default_course_id"):
            vals["course_id"] = self.env.context.get("default_course_id")

        enrollment = super(EducationEnrollment, self).create(vals)

        # Auto-confirm if context flag is set
        if self.env.context.get("auto_confirm"):
            enrollment.action_confirm()

        return enrollment

    # Python Constraints
    @api.constrains("enrollment_date", "completion_date")
    def _check_dates(self):
        for enrollment in self:
            if enrollment.completion_date and enrollment.enrollment_date:
                if enrollment.completion_date < enrollment.enrollment_date:
                    raise ValidationError(
                        _("Completion date cannot be before enrollment date.")
                    )
