# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerMatricula(models.Model):
    _name = "res.partner.matricula"
    _description = "License Plate"

    name = fields.Char(string="License Plate")
    brand_model = fields.Char(string="Brand/Model")
    partner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        ondelete="cascade",
    )

    def name_get(self):
        result = []
        for record in self:
            label = record.name or ""
            if record.brand_model:
                label = f"{label} - {record.brand_model}"
            result.append((record.id, label))
        return result


class ResPartner(models.Model):
    _inherit = "res.partner"

    matricula_ids = fields.One2many(
        "res.partner.matricula",
        "partner_id",
        string="License Plates",
    )
