# Enhanced Striped Invoice Layout

Customises the standard Odoo customer **invoice report** (`account.report_invoice_document`)
on the striped layout:

- **Partner address / VAT block** — renders the partner address and name, and a
  VAT line that uses the fiscal country's VAT label when available (falling back
  to *"Vat no."*). Applied consistently across all three address layouts
  (different shipping address, same shipping address, and no shipping address).
- **Payment term spacing** — removes the top margin on the payment-term block and
  replaces the payment-term note with vertical spacing.
- **Payment reference** — reworded and reformatted payment instruction line,
  including the bank account when set.

## Compatibility

- **Odoo 19.0**

> Upgraded from the 18.0 release. The address overrides were rewritten to match
> Odoo 19's restructured invoice template, where all three address blocks expose
> a `<t t-set="address">` node (v18 used differing markup that the old XPaths
> targeted via `//div[1]`).

## Behaviour notes

- This module is set to **auto-install** — it installs automatically on any
  database that has *Accounting* (`account`) installed.
- The payment-term **note** from the payment terms record is intentionally
  **not** shown; it is replaced with spacing.

## Installation

After installing, go to **Accounting → Customers → Invoices**, open any customer
invoice and print/preview the PDF. The modified striped layout applies
automatically — no further configuration required.

## Technical

| | |
|---|---|
| **Author** | busii |
| **Website** | busii.com |
| **Licence** | LGPL-3 |
| **Depends** | `base`, `account` |
