{
    "name": "Education Context Demo",
    "version": "18.0.1.0.0",
    "category": "Education",
    "summary": "Education Management with Advanced Context Usage Demonstrations",
    "author": "Amr Gaber",
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
