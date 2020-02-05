# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from .houzzApi import HouzzApi

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

import json
import logging

_logger = logging.getLogger(__name__)




class HouzzConfig(models.Model):
    """HOUZZ API Configuration module"""
    _name = 'houzz.config'
    _description = 'HOUZZ API Profile'
    _rec_name = 'store_name'

    store_name = fields.Char(string='Store Name')
    name = fields.Char(string='App Name', required=True)
    houzz_token = fields.Char(string='Token', required=True)
    houzz_user_name = fields.Char(string='User Name', required=True)
    team_id = fields.Many2one('crm.team', string='Team', required=True)


class HouzzPayments(models.Model):
    """HOUZZ settlement management"""
    _name = 'houzz.payments'
    _description = 'Houzz Payments'


    name = fields.Char('Name')
    houzz_config_id = fields.Many2one('houzz.config', string='Houzz')
    payment_id = fields.Char('Payment Id', index=True)
    from_date = fields.Datetime('From Date')
    to_date = fields.Datetime('To Date')
    sales = fields.Float(string='Sales')
    shipping = fields.Float(string='Shipping')
    tax = fields.Float(string='Tax')
    commission = fields.Float(string='Commission')
    deposit_amount = fields.Monetary(string='Deposit Amount', 
                                     currency_field='currency_id', 
                                     track_visibility='always')
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)


