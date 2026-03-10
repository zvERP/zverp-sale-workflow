# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_workshop_quote = fields.Boolean(string="Workshop quote")
    workshop_brand_model = fields.Char(string="Brand/Model")
    workshop_plate = fields.Char(string="Plate")
    workshop_km = fields.Integer(string="Kilometers")
