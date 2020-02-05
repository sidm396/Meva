# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from .houzzApi import *

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Sale Order"""
    _inherit = 'sale.order'


    houzz_config_id = fields.Many2one('houzz.config', string='Houzz')
    client_order_ref = fields.Char(required=True, copy=True)
    houzz_order_status = fields.Selection([
        ('Placed', 'Placed'),
        ('Processing', 'Processing'),
        ('Charged', 'Charged'),
        ('FailedToCharge', 'Failed to Charge'),
        ('Shipped', 'Shipped'),
        ('Canceled', 'Canceled'),
        ('InProduction', 'InProduction')
    ], string='Houzz Order Status')



    def houzz_process_order(self):
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz_config_id.houzz_token, 
                         user_name=self.houzz_config_id.houzz_user_name, 
                         app_name=self.houzz_config_id.name)
        process = houzz.process_order(self.client_order_ref)

        if not process:
            self.message_post(body=u"Confirmation order failed")

        else:
            self.update({'houzz_order_status': 'Processing'})
            self.message_post(body=u"Order Confirmed")

        return True



    def houzz_charge_order(self):
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz_config_id.houzz_token, 
                         user_name=self.houzz_config_id.houzz_user_name,
                         app_name=self.houzz_config_id.name)
        process = houzz.charge_order(self.client_order_ref)
        _logger.info(process)

        if not process:
            self.message_post(body=u"Collection failed")
        else:
            self.update({'houzz_order_status': 'Charged'})
            self.message_post(body=u"Collection successful")
        return True


    def preview_shipping_label(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            # https://www.houzz.com/printShippingLabel/orderId=1656-9927-9120-7805
            'url': 'https://www.houzz.com/printShippingLabel/orderId='+self.client_order_ref,
        }


    def preview_packing_slip(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            # 1656-9927-9120-7805
            'url': 'https:\/\/www.houzz.com\/printBuyerOrder\/orderId='+self.client_order_ref,
        }