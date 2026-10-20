# Customer Retainer Hours Alert (`busii_retainer_alert`)

Odoo 18 · Author: busii · busii.com

Emails the team when a customer's logged timesheet hours reach a set percentage (80% by default) of their monthly retainer, so overage can be flagged and charged.

## How it works

1. On a customer (company contact), open the **Retainer** tab and set:
   - **Monthly Retainer Hours** – hours included each calendar month (0 = off)
   - **Alert at (%)** – defaults to 80
   - **Alert Recipients** – internal users who get the email
2. Whenever a timesheet is created or its hours, date, project, task or customer change, the module totals that customer's timesheet hours for the calendar month of the timesheet date.
3. When the total reaches the threshold, it creates a **Retainer Alert** record and queues one email to the recipients. The unique constraint (customer + month) means it only fires once per customer per month.
4. On the 1st of the next month the count starts at zero again.

The Retainer tab also shows hours used this month and a progress bar. All alerts are listed under **Project › Reporting › Retainer Alerts**.

## Which timesheets count

All timesheet lines (analytic lines with a project) whose customer resolves to that company — including lines on projects/tasks set to one of the company's individual contacts. The timesheet's customer comes from the task's customer, falling back to the project's customer (standard `hr_timesheet` behaviour).

## Notes

- Emails go via the outgoing mail queue (`force_send=False`), so on Odoo.sh they leave on the next mail queue cron run (usually within a minute or two).
- Hours are compared in hours (`unit_amount`). If the company encodes timesheets in days, check the stored values before relying on this.
- The email template is `noupdate`: edit it under Settings › Technical › Email Templates ("Retainer: Threshold Reached") without upgrades overwriting it.
- Lowering or raising the retainer mid-month does not resend an alert already sent for that month.
- Back-dated timesheets are checked against their own month, so logging into last month can raise last month's alert if it was missed.

## Tests

```
odoo-bin -d <db> -i busii_retainer_alert --test-tags /busii_retainer_alert --stop-after-init
```
