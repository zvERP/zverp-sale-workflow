# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = "sale.order"

    advance_payment_amount = fields.Monetary(
        string="Advance payment amount",
        currency_field="currency_id",
        compute="_compute_advance_payment_amount",
        store=True,
        readonly=True,
    )
    amount_total_after_advance = fields.Monetary(
        string="Total after advance",
        currency_field="currency_id",
        compute="_compute_amount_total_after_advance",
        store=True,
        readonly=True,
    )
    amount_total_after_advance_display = fields.Char(
        string="Formatted total after advance",
        compute="_compute_amount_total_after_advance",
        store=False,
        readonly=True,
    )

    @api.depends(
        "payment_line_ids",
        "payment_line_ids.amount_residual",
        "payment_line_ids.amount_residual_currency",
        "payment_line_ids.currency_id",
        "payment_line_ids.company_id",
        "payment_line_ids.date",
        "currency_id",
        "company_id",
    )
    def _compute_advance_payment_amount(self):
        for order in self:
            advance_amount = 0.0
            for line in order.payment_line_ids:
                line_currency = line.currency_id or line.company_currency_id
                line_amount = (
                    line.amount_residual_currency if line.currency_id else line.amount_residual
                )
                line_amount *= -1
                if line_currency != order.currency_id:
                    advance_amount += line_currency._convert(
                        line_amount,
                        order.currency_id,
                        order.company_id,
                        line.date or fields.Date.today(),
                    )
                else:
                    advance_amount += line_amount
            order.advance_payment_amount = advance_amount

    @api.depends("amount_total", "advance_payment_amount")
    def _compute_amount_total_after_advance(self):
        for order in self:
            order.amount_total_after_advance = (
                order.amount_total - order.advance_payment_amount
            )
            order.amount_total_after_advance_display = formatLang(
                order.env,
                order.amount_total_after_advance,
                currency_obj=order.currency_id,
            )
