from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRetainerAlert(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env['res.users'].create({
            'name': 'Retainer Manager', 'login': 'retainer_mgr', 'email': 'mgr@example.com',
            'groups_id': [(6, 0, [cls.env.ref('project.group_project_manager').id])],
        })
        cls.dev = cls.env['res.users'].create({
            'name': 'Retainer Dev', 'login': 'retainer_dev', 'email': 'dev@example.com',
            'groups_id': [(6, 0, [cls.env.ref('hr_timesheet.group_hr_timesheet_user').id])],
        })
        cls.employee = cls.env['hr.employee'].create({'name': 'Retainer Dev', 'user_id': cls.dev.id})
        cls.customer = cls.env['res.partner'].create({
            'name': 'Retainer Customer', 'is_company': True,
            'retainer_hours': 10.0,
            'retainer_alert_user_ids': [(6, 0, [cls.manager.id, cls.dev.id])],
        })
        cls.contact = cls.env['res.partner'].create({'name': 'Contact Person', 'parent_id': cls.customer.id})
        cls.project = cls.env['project.project'].create({
            'name': 'Retainer Project', 'partner_id': cls.contact.id, 'allow_timesheets': True,
        })
        cls.task = cls.env['project.task'].create({'name': 'Support', 'project_id': cls.project.id})
        cls.Alert = cls.env['busii.retainer.alert']

    def _log(self, hours, day=date(2026, 10, 5), user=None):
        env = self.env(user=user or self.dev)
        return env['account.analytic.line'].create({
            'name': 'work', 'task_id': self.task.id, 'project_id': self.project.id,
            'employee_id': self.employee.id, 'unit_amount': hours, 'date': day,
        })

    def _alerts(self):
        return self.Alert.search([('partner_id', '=', self.customer.id)])

    def test_below_threshold_no_alert(self):
        self._log(7.9)
        self.assertFalse(self._alerts())

    def test_alert_at_80_percent_once(self):
        self._log(5)
        self._log(3)  # 8h of 10h = 80%
        alert = self._alerts()
        self.assertEqual(len(alert), 1)
        self.assertEqual(alert.period_start, date(2026, 10, 1))
        self.assertAlmostEqual(alert.hours_used, 8.0)
        mails = self.env['mail.mail'].sudo().search([('model', '=', 'busii.retainer.alert'), ('res_id', '=', alert.id)])
        self.assertEqual(len(mails), 1)
        self.assertEqual(set(mails.recipient_ids.ids), {self.manager.partner_id.id, self.dev.partner_id.id})
        self.assertIn('Retainer Customer', mails.subject)
        cron = self.env.ref('mail.ir_cron_mail_scheduler_action')
        self.assertTrue(self.env['ir.cron.trigger'].sudo().search_count([('cron_id', '=', cron.id)]),
                        'Mail queue should be triggered immediately')
        # More time in the same month does not send again
        self._log(2)
        self.assertEqual(len(self._alerts()), 1)

    def test_new_month_resets(self):
        self._log(8, day=date(2026, 10, 5))
        self._log(8, day=date(2026, 11, 3))
        self.assertEqual(self._alerts().mapped('period_start'), [date(2026, 11, 1), date(2026, 10, 1)])

    def test_editing_hours_triggers(self):
        line = self._log(1)
        self.assertFalse(self._alerts())
        line.with_user(self.dev).write({'unit_amount': 9})
        self.assertEqual(len(self._alerts()), 1)

    def test_no_recipients_or_no_retainer(self):
        self.customer.retainer_alert_user_ids = [(5, 0, 0)]
        self._log(9)
        self.assertFalse(self._alerts())
        self.customer.write({'retainer_alert_user_ids': [(6, 0, [self.manager.id])], 'retainer_hours': 0})
        self._log(9)
        self.assertFalse(self._alerts())

    def test_usage_compute(self):
        today = date.today()
        self._log(2.5, day=today)
        self.customer.invalidate_recordset()
        self.assertAlmostEqual(self.customer.retainer_hours_used, 2.5)
        self.assertAlmostEqual(self.customer.retainer_usage_percent, 25.0)
