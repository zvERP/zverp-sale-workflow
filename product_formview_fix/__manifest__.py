# -*- coding: utf-8 -*-
{
    "name": "Product Form View Fix",
    "summary": "Redirige la navegación de product.product a product.template cuando solo hay una variante",
    "description": """
        Corrige el comportamiento de navegación al hacer clic en el producto
        desde sale.order.line u otros modelos: redirige al formulario de
        product.template en lugar de product.product cuando el producto
        solo tiene una variante.
    """,
    "version": "16.0.1.0.0",
    "category": "Sales",
    "author": "zvERP",
    "website": "http://www.zverp.com",
    "license": "LGPL-3",
    "depends": ["product"],
    "installable": True,
    "auto_install": False,
}
