# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    matricula_id = fields.Many2one("res.partner.matricula", string="License Plate")
    is_workshop_quote = fields.Boolean(string="Workshop quote")
    workshop_brand_model = fields.Char(string="Brand/Model")
    workshop_plate = fields.Char(string="Plate")
    workshop_km = fields.Integer(string="Kilometers")

    @api.onchange("matricula_id")
    def _onchange_matricula_id_set_workshop_plate(self):
        for move in self:
            if move.matricula_id:
                move.workshop_plate = move.matricula_id.name
                if not move.workshop_brand_model:
                    move.workshop_brand_model = move.matricula_id.brand_model or False
            else:
                move.workshop_plate = False

    def action_post(self):
        result = super().action_post()
        for move in self:
            if (
                move.matricula_id
                and move.workshop_brand_model
                and move.matricula_id.brand_model != move.workshop_brand_model
            ):
                move.matricula_id.brand_model = move.workshop_brand_model
        return result
