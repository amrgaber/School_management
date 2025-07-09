from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    date_of_birth = fields.Date(
        string="Date of Birth", help="Date of birth of the partner"
    )
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")], string="Gender"
    )
