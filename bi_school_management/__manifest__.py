# -*- coding: utf-8 -*-
{
    "name": "Education Context Demo",
    "version": "18.0.1.0.0",
    "category": "Education",
    "summary": "Education Management with Advanced Context Usage Demonstrations",
    "description": """
Education Context Demo Module
=============================

This module demonstrates advanced context usage patterns in Odoo 18 through a comprehensive education management system.

Key Context Usage Patterns Demonstrated:
* Default Values via Context in forms and wizards
* Dynamic Domains via Context for filtering records
* Multi-Step Wizards with Context flow between steps
* Context in Smart Buttons and action methods
* Context for Security and role-based access control

Features:
* School and Department Management
* Student Registration and Management
* Course and Class Management
* Enrollment Workflow with Financial Integration
* Attendance Tracking with Bulk Operations
* Academic Year Management
* Integration with HR, Accounting, and Inventory modules

This module serves as a practical tutorial and reference for developers learning advanced context usage in Odoo 18.
    """,
    "author": "AmrGaber",
    "website": "https://www.linkedin.com/in/amrgabr/",
    "depends": [
        "base",
        "mail",
        "hr",
        "account",
        "product",
        "stock",
        "analytic",
    ],
    "data": [
        # Security
        "security/education_security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/education_sequence.xml",
        # Views
        "views/education_school_views.xml",
        "views/education_academic_year_views.xml",
        "views/education_department_views.xml",
        "views/education_course_views.xml",
        "views/education_class_views.xml",
        "views/education_student_views.xml",
        "views/education_enrollment_views.xml",
        "views/education_attendance_views.xml",
        "views/res_partner_views.xml",
        "views/education_student_batch_create_wizard.xml",
        # Wizards
        "wizard/attendance_bulk_wizard.xml",
        "wizard/course_enrollment_wizard.xml",
        "wizard/student_registration_wizard.xml",
        # Reports
        "report/education_reports.xml",
        # Menus
        "views/education_menus.xml",
    ],
    "demo": [
        "demo/education_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "bi_school_management/static/src/js/**/*",
            "bi_school_management/static/src/css/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 10,
    "license": "LGPL-3",
}
