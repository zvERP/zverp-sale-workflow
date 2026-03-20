# -*- coding: utf-8 -*-
from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_formview_id(self, access_uid=None):
        if self.product_tmpl_id.product_variant_count == 1:
            return self.env.ref("product.product_template_only_form_view").id
        return super().get_formview_id(access_uid=access_uid)

    def get_formview_action(self, access_uid=None):
        res = super().get_formview_action(access_uid=access_uid)
        if self.product_tmpl_id.product_variant_count == 1:
            res["res_model"] = "product.template"
            res["res_id"] = self.product_tmpl_id.id
            view_id = self.env.ref("product.product_template_only_form_view").id
            res["views"] = [(view_id, "form")]
            res["view_id"] = view_id
        return res
