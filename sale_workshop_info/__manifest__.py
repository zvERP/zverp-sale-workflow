# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Workshop Info",
    "version": "16.0.1.0.0",
    "summary": "Workshop data on quotations and invoices",
    "category": "Sales",
    "license": "AGPL-3",
    "depends": ["sale_management", "account"],
    "author": "zvERP.com",
    "website": "https://zverp.com",
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "report/sale_order_report.xml",
        "report/account_invoice_report.xml",
    ],
    "installable": True,
}
