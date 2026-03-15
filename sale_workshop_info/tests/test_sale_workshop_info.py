# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import common


class TestSaleWorkshopInfo(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.matricula_model = cls.env["res.partner.matricula"]
        cls.partner = cls.env["res.partner"].create({"name": "Workshop Partner"})
        cls.partner_single_plate = cls.env["res.partner"].create(
            {"name": "Partner Single Plate"}
        )
        cls.partner_multi_plate = cls.env["res.partner"].create(
            {"name": "Partner Multi Plate"}
        )
        cls.partner_no_plate = cls.env["res.partner"].create({"name": "Partner No Plate"})
        cls.single_plate = cls.matricula_model.create(
            {
                "name": "1111AAA",
                "partner_id": cls.partner_single_plate.id,
                "brand_model": "Seat Ibiza",
            }
        )
        cls.multi_plate_a = cls.matricula_model.create(
            {
                "name": "2222BBB",
                "partner_id": cls.partner_multi_plate.id,
                "brand_model": "Renault Clio",
            }
        )
        cls.multi_plate_b = cls.matricula_model.create(
            {
                "name": "3333CCC",
                "partner_id": cls.partner_multi_plate.id,
                "brand_model": "Volkswagen Golf",
            }
        )
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
                "workshop_plate": "1234ABC",
                "workshop_km": 120000,
            }
        )

        quotation_html = self._render_sale_report_html(order)
        self.assertIn("Workshop data", quotation_html)
        self.assertIn("1234ABC", quotation_html)

        proforma_html = self._render_sale_report_html(order, proforma=True)
        self.assertIn("Workshop data", proforma_html)

    def test_03_invoice_created_from_quote_copies_fields_and_prints(self):
        plate = self.matricula_model.create(
            {
                "name": "MAT-INV-01",
                "partner_id": self.partner.id,
                "brand_model": "Renault Clio",
            }
        )
        order = self._create_sale_order(
            {
                "is_workshop_quote": True,
                "workshop_brand_model": "Renault Clio",
                "workshop_plate": "4321XYZ",
                "workshop_km": 98000,
                "matricula_id": plate.id,
            }
        )
        order.action_confirm()
        invoice = order._create_invoices()

        self.assertEqual(invoice.matricula_id, plate)
        self.assertTrue(invoice.is_workshop_quote)
        self.assertEqual(invoice.workshop_brand_model, "Renault Clio")
        self.assertEqual(invoice.workshop_plate, "4321XYZ")
        self.assertEqual(invoice.workshop_km, 98000)

        invoice_html = self._render_invoice_report_html(invoice)
        self.assertIn("Workshop data", invoice_html)
        self.assertIn("Renault Clio", invoice_html)
        self.assertIn("MAT-INV-01", invoice_html)

    def test_06_order_auto_assigns_single_partner_plate(self):
        order = self.env["sale.order"].create({"partner_id": self.partner_single_plate.id})
        self.assertFalse(order.matricula_id)

    def test_07_move_auto_assigns_single_partner_plate(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_single_plate.id,
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
        self.assertFalse(invoice.matricula_id)

    def test_08_manual_plate_kept_with_multiple_partner_plates(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_multi_plate.id,
                "matricula_id": self.multi_plate_b.id,
            }
        )
        self.assertEqual(order.matricula_id, self.multi_plate_b)

    def test_09_order_partner_change_does_not_force_matricula(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_single_plate.id,
                "matricula_id": self.single_plate.id,
            }
        )
        self.assertEqual(order.matricula_id, self.single_plate)

        order.write({"partner_id": self.partner_no_plate.id})
        self.assertEqual(order.matricula_id, self.single_plate)

    def test_10_move_without_partner_does_not_force_matricula(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "entry",
                "matricula_id": self.single_plate.id,
            }
        )
        invoice.write({"partner_id": False})
        self.assertEqual(invoice.matricula_id, self.single_plate)

    def test_11_sale_report_prints_plate_when_present(self):
        order = self._create_sale_order(
            {
                "is_workshop_quote": True,
                "matricula_id": self.single_plate.id,
                "partner_id": self.partner_single_plate.id,
            }
        )
        report_html = self._render_sale_report_html(order)
        self.assertIn("License Plate:", report_html)
        self.assertIn("1111AAA", report_html)

    def test_12_form_views_define_partner_domain_for_plate(self):
        sale_view = self.env.ref("sale_workshop_info.view_order_form_inherit_workshop_info")
        move_view = self.env.ref("sale_workshop_info.view_move_form_inherit_workshop_info")
        domain_snippet = "domain=\"[('partner_id', '=', partner_id)]\""
        no_create_edit_snippet = "options=\"{'no_create_edit': True}\""
        self.assertIn(domain_snippet, sale_view.arch_db)
        self.assertIn(domain_snippet, move_view.arch_db)
        self.assertIn(no_create_edit_snippet, sale_view.arch_db)
        self.assertIn(no_create_edit_snippet, move_view.arch_db)

    def test_17_partner_view_uses_tags_widget_for_matriculas(self):
        partner_view = self.env.ref("sale_workshop_info.view_partner_form_inherit_matricula")
        self.assertIn("name=\"matricula_ids\"", partner_view.arch_db)
        self.assertIn("<tree editable=\"bottom\">", partner_view.arch_db)

    def test_13_order_write_matricula_syncs_legacy_plate(self):
        order = self.env["sale.order"].create({"partner_id": self.partner_multi_plate.id})
        order.write({"matricula_id": self.multi_plate_a.id})
        self.assertEqual(order.workshop_plate, "2222BBB")

    def test_14_order_multi_plate_no_auto_match_from_legacy_plate(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_multi_plate.id,
                "workshop_plate": "3333CCC",
            }
        )
        self.assertFalse(order.matricula_id)

    def test_15_order_confirm_syncs_brand_model_to_matricula(self):
        order = self.env["sale.order"].create({"partner_id": self.partner_multi_plate.id})
        order.write(
            {
                "matricula_id": self.multi_plate_b.id,
                "workshop_brand_model": "Toyota Corolla",
            }
        )
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
        order.action_confirm()
        self.assertEqual(self.multi_plate_b.brand_model, "Toyota Corolla")

    def test_16_move_post_syncs_brand_model_to_matricula(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_multi_plate.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Direct line",
                            "quantity": 1.0,
                            "price_unit": 50.0,
                        }
                    )
                ],
                "matricula_id": self.multi_plate_a.id,
                "workshop_brand_model": "Ford Focus",
            }
        )
        invoice.action_post()
        self.assertEqual(self.multi_plate_a.brand_model, "Ford Focus")

    def test_04_uncheck_keeps_existing_values(self):
        order = self._create_sale_order(
            {
                "is_workshop_quote": True,
                "matricula_id": self.single_plate.id,
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
