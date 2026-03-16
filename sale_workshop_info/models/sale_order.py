# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    matricula_id = fields.Many2one("res.partner.matricula", string="License Plate")
    is_workshop_quote = fields.Boolean(string="Workshop quote")
    workshop_brand_model = fields.Char(string="Brand/Model")
    workshop_plate = fields.Char(string="Plate")
    workshop_km = fields.Integer(string="Kilometers")

    @api.onchange("matricula_id")
    def _onchange_matricula_id_set_workshop_plate(self):
        for order in self:
            if order.matricula_id:
                order.workshop_plate = order.matricula_id.name
                if not order.workshop_brand_model:
                    order.workshop_brand_model = order.matricula_id.brand_model or False
            else:
                order.workshop_plate = False

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update(
            {
                "matricula_id": self.matricula_id.id,
                "is_workshop_quote": self.is_workshop_quote,
                "workshop_brand_model": self.workshop_brand_model,
                "workshop_plate": self.workshop_plate,
                "workshop_km": self.workshop_km,
            }
        )
        return vals

    def action_confirm(self):
        result = super().action_confirm()
        for order in self:
            if (
                order.matricula_id
                and order.workshop_brand_model
                and order.matricula_id.brand_model != order.workshop_brand_model
            ):
                order.matricula_id.brand_model = order.workshop_brand_model
        return result
