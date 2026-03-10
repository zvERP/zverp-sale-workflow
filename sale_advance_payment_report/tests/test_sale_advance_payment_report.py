# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import common


class TestSaleAdvancePaymentReport(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "Advance Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Service", "invoice_policy": "order", "type": "service"}
        )

        cls.currency_eur = (
            cls.env["res.currency"].with_context(active_test=False).search([
                ("name", "=", "EUR")
            ], limit=1)
        )
        if cls.currency_eur and not cls.currency_eur.active:
            cls.currency_eur.active = True

        cls.bank_journal = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("currency_id", "=", cls.currency_eur.id)], limit=1
        )
        if not cls.bank_journal:
            cls.bank_journal = cls.env["account.journal"].create(
                {
                    "name": "Advance Journal EUR",
                    "type": "bank",
                    "code": "APR16",
                    "currency_id": cls.currency_eur.id,
                }
            )

    def _create_sale_order(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1.0,
                "price_unit": 1000.0,
            }
        )
        return order

    def _create_advance_payment(self, order, amount):
        wizard = (
            self.env["account.voucher.wizard"]
            .with_context(active_ids=[order.id], active_id=order.id)
            .create(
                {
                    "journal_id": self.bank_journal.id,
                    "payment_type": "inbound",
                    "amount_advance": amount,
                    "order_id": order.id,
                }
            )
        )
        wizard.make_advance_payment()

    def _render_sale_report_html(self, order):
        report = self.env.ref("sale.action_report_saleorder")
        html, _ = report._render_qweb_html([order.id])
        return html.decode() if isinstance(html, bytes) else html

    def test_01_no_advance_payment(self):
        order = self._create_sale_order()
        order.invalidate_cache(["advance_payment_amount", "amount_total_after_advance"])
        self.assertTrue(order.currency_id.is_zero(order.advance_payment_amount))
        self.assertEqual(order.amount_total_after_advance, order.amount_total)

        report_html = self._render_sale_report_html(order)
        self.assertNotIn("Advance payment", report_html)

    def test_02_show_advance_payment_amount_in_report(self):
        order = self._create_sale_order()
        self._create_advance_payment(order, 125.0)

        order.invalidate_cache(
            ["advance_payment_amount", "amount_total_after_advance", "payment_line_ids"]
        )
        self.assertGreater(order.advance_payment_amount, 0.0)
        self.assertEqual(
            order.amount_total_after_advance,
            order.amount_total - order.advance_payment_amount,
        )

        report_html = self._render_sale_report_html(order)
        self.assertIn("Advance payment", report_html)

    def test_03_advance_payment_currency_conversion(self):
        order = self._create_sale_order()

        currency_usd = self.env["res.currency"].search([("name", "=", "USD")], limit=1)
        if not currency_usd:
            self.skipTest("USD currency not available")

        rate = self.env["res.currency.rate"].search(
            [("currency_id", "=", currency_usd.id), ("name", "=", fields.Date.today())],
            limit=1,
        )
        if rate:
            rate.rate = 1.20
        else:
            self.env["res.currency.rate"].create(
                {
                    "currency_id": currency_usd.id,
                    "name": fields.Date.today(),
                    "rate": 1.20,
                }
            )
        usd_journal = self.env["account.journal"].search(
            [("type", "=", "bank"), ("currency_id", "=", currency_usd.id)], limit=1
        )
        if not usd_journal:
            usd_journal = self.env["account.journal"].create(
                {
                    "name": "Advance Journal USD",
                    "type": "bank",
                    "code": "APU16",
                    "currency_id": currency_usd.id,
                }
            )

        wizard = (
            self.env["account.voucher.wizard"]
            .with_context(active_ids=[order.id], active_id=order.id)
            .create(
                {
                    "journal_id": usd_journal.id,
                    "payment_type": "inbound",
                    "amount_advance": 100.0,
                    "order_id": order.id,
                }
            )
        )
        wizard.make_advance_payment()

        order.invalidate_cache(
            ["advance_payment_amount", "amount_total_after_advance", "payment_line_ids"]
        )
        self.assertGreater(order.advance_payment_amount, 0.0)
        self.assertEqual(
            order.amount_total_after_advance,
            order.amount_total - order.advance_payment_amount,
        )
