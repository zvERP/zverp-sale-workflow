# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import common


class TestSaleWorkshopInfo(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Workshop Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Workshop Service", "type": "service", "invoice_policy": "order"}
        )

    def _create_sale_order(self, workshop_vals=None):
        values = {"partner_id": self.partner.id}
        if workshop_vals:
            values.update(workshop_vals)
        order = self.env["sale.order"].create(values)
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "name": self.product.name,
                "product_uom_qty": 1.0,
                "product_uom": self.product.uom_id.id,
                "price_unit": 100.0,
            }
        )
        return order

    def _render_sale_report_html(self, order, proforma=False):
        report = self.env.ref("sale.action_report_saleorder")
        context = dict(self.env.context)
        if proforma:
            proforma_report = self.env.ref("sale.action_report_pro_forma", False)
            if proforma_report:
                report = proforma_report
            else:
                context["proforma"] = True
        html, _ = report.with_context(context)._render_qweb_html([order.id])
        return html.decode() if isinstance(html, bytes) else html

    def _render_invoice_report_html(self, invoice):
        report = self.env.ref("account.account_invoices")
        html, _ = report._render_qweb_html([invoice.id])
        return html.decode() if isinstance(html, bytes) else html

    def test_01_quote_without_check_does_not_show_block(self):
        order = self._create_sale_order()
        report_html = self._render_sale_report_html(order)
        self.assertNotIn("Workshop data", report_html)

    def test_02_quote_with_check_shows_block_in_quote_and_proforma(self):
        order = self._create_sale_order(
            {
                "is_workshop_quote": True,
                "workshop_brand_model": "Seat Ibiza",
                "workshop_plate": "1234ABC",
                "workshop_km": 120000,
            }
        )

        quotation_html = self._render_sale_report_html(order)
        self.assertIn("Workshop data", quotation_html)
        self.assertIn("Seat Ibiza", quotation_html)
        self.assertIn("1234ABC", quotation_html)

        proforma_html = self._render_sale_report_html(order, proforma=True)
        self.assertIn("Workshop data", proforma_html)

    def test_03_invoice_created_from_quote_copies_fields_and_prints(self):
        order = self._create_sale_order(
            {
                "is_workshop_quote": True,
                "workshop_brand_model": "Renault Clio",
                "workshop_plate": "4321XYZ",
                "workshop_km": 98000,
            }
        )
        order.action_confirm()
        invoice = order._create_invoices()

        self.assertTrue(invoice.is_workshop_quote)
        self.assertEqual(invoice.workshop_brand_model, "Renault Clio")
        self.assertEqual(invoice.workshop_plate, "4321XYZ")
        self.assertEqual(invoice.workshop_km, 98000)

        invoice_html = self._render_invoice_report_html(invoice)
        self.assertIn("Workshop data", invoice_html)
        self.assertIn("Renault Clio", invoice_html)

    def test_04_uncheck_keeps_existing_values(self):
        order = self._create_sale_order(
            {
                "is_workshop_quote": True,
                "workshop_brand_model": "Peugeot 308",
                "workshop_plate": "0000AAA",
                "workshop_km": 101000,
            }
        )
        order.write({"is_workshop_quote": False})

        self.assertEqual(order.workshop_brand_model, "Peugeot 308")
        self.assertEqual(order.workshop_plate, "0000AAA")
        self.assertEqual(order.workshop_km, 101000)

    def test_05_direct_invoice_allows_edit_and_print(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Direct line",
                            "quantity": 1.0,
                            "price_unit": 50.0,
                        }
                    )
                ],
            }
        )
        invoice.write(
            {
                "is_workshop_quote": True,
                "workshop_brand_model": "VW Golf",
                "workshop_plate": "5678DEF",
                "workshop_km": 150000,
            }
        )

        self.assertTrue(invoice.is_workshop_quote)
        self.assertEqual(invoice.workshop_brand_model, "VW Golf")
        self.assertEqual(invoice.workshop_plate, "5678DEF")
        self.assertEqual(invoice.workshop_km, 150000)

        invoice_html = self._render_invoice_report_html(invoice)
        self.assertIn("Workshop data", invoice_html)
