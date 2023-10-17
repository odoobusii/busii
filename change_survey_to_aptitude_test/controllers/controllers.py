# -*- coding: utf-8 -*-
# from odoo import http


# class ChangeSurveyToAptitudeTest(http.Controller):
#     @http.route('/change_survey_to_aptitude_test/change_survey_to_aptitude_test', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/change_survey_to_aptitude_test/change_survey_to_aptitude_test/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('change_survey_to_aptitude_test.listing', {
#             'root': '/change_survey_to_aptitude_test/change_survey_to_aptitude_test',
#             'objects': http.request.env['change_survey_to_aptitude_test.change_survey_to_aptitude_test'].search([]),
#         })

#     @http.route('/change_survey_to_aptitude_test/change_survey_to_aptitude_test/objects/<model("change_survey_to_aptitude_test.change_survey_to_aptitude_test"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('change_survey_to_aptitude_test.object', {
#             'object': obj
#         })
