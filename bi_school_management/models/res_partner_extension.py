from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_birth = fields.Date(string='Date of Birth', help='Date of birth of the partner') 