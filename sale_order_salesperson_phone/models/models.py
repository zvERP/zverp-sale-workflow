# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrder(models.Model):
	_inherit = "sale.order"

	show_salesperson_phone = fields.Boolean(string="Show telephone")
