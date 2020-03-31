from .houzzApi import *

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPickingHouzz(models.Model):
    """Stock Picking for Shipping Labels and Packing Slips"""
    _inherit = 'stock.picking'


    def preview_shipping_label(self):
        # stock_obj = self.browse(self._context.get('active_id'))
        if self.sale_id:
            print("entered...")
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': 'https://www.houzz.com/printShippingLabel/orderId='+self.sale_id.client_order_ref
            }
        else:
            raise UserError(_("Report Can't be viewed becoz Sales Order not linked with this record"))



    def preview_packing_slip(self):
        if self.sale_id:
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                # 1656-9927-9120-7805
                'url': 'https:\/\/www.houzz.com\/printBuyerOrder\/orderId='+self.sale_id.client_order_ref
            }
        else:
            raise UserError(_("Report Can't be viewed becoz Sales Order not linked with this record"))