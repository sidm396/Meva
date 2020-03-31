# -*- encoding: utf-8 -*-
{
    'name': 'Houzz Market Place and Odoo Intigration ',
    'description': 'Houzz Market Place and Odoo Intigration ',
    'author': 'ShivaGuntuku',
    'depends': ['sale_management', 'stock'],
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'views/houzz_view.xml',
        'views/sale_view.xml',
        'views/sale_order_tree.xml',
        'wizard/houzz_order_import_view.xml',
        'wizard/houzz_stock_view.xml',
        'views/products_view.xml',
        # 'views/houzz_server_actions.xml',
        'views/stock_picking_view.xml',
        'views/houzz_menu.xml',
    ]
}
