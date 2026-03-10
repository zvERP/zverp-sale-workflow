# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_workshop_quote = fields.Boolean(string="Workshop quote")
    workshop_brand_model = fields.Char(string="Brand/Model")
    workshop_plate = fields.Char(string="Plate")
    workshop_km = fields.Integer(string="Kilometers")

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update(
            {
                "is_workshop_quote": self.is_workshop_quote,
                "workshop_brand_model": self.workshop_brand_model,
                "workshop_plate": self.workshop_plate,
                "workshop_km": self.workshop_km,
            }
        )
        return vals
