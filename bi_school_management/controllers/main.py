from odoo import http

# class EducationContextDemo(http.Controller):
#     @http.route('/bi_school_management/bi_school_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bi_school_management/bi_school_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bi_school_management.listing', {
#             'root': '/bi_school_management/bi_school_management',
#             'objects': http.request.env['bi_school_management.bi_school_management'].search([]),
#         })

#     @http.route('/bi_school_management/bi_school_management/objects/<model("bi_school_management.bi_school_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bi_school_management.object', {
#             'object': obj
#         })
