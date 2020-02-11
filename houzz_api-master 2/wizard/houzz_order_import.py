# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ..models.houzzApi import *

from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import AccessDenied
import logging
import json

_logger = logging.getLogger(__name__)


class HouzzOrderImport(models.TransientModel):
    """Houzz Order Import """
    _name = 'houzz.order.import'
    _description = 'HOUZZ Import '

    houzz = fields.Many2one('houzz.config', 'Houzz', required=True)
    order_status = fields.Selection([
        ('All', 'All'),
        ('Active', 'Active'),
        ('New', 'New'),
        ('Charged', 'Charged'),
        ('InProduction', 'InProduction'),
        ('Shipped', 'Shipped'),
        ('FailedToCharge', 'FailedToCharge')
    ], default='All')
    order_form = fields.Date('From Date')
    order_to = fields.Date('From To')
    order_limit = fields.Integer('Limit', default=1000)
    order_start = fields.Integer('Start', default=0)


    def do_order_import(self):
        """Import HOUZZ order it returns data in the JSON Format"""

        self.ensure_one()
        houzz = HouzzApi(token=self.houzz.houzz_token, user_name=self.houzz.houzz_user_name, app_name=self.houzz.name)
        response = houzz.get_orders(status=self.order_status, start=self.order_start, limit=self.order_limit,
                                    from_date=self.order_form, to_date=self.order_to, format='json')
        
        response_decode = json.loads(response.decode('utf-8'))
        orders = response_decode['Orders']

        self.save_order(orders, self.houzz.id)
        return {'type': 'ir.actions.act_window_close'}


    @api.model
    def auto_import_order(self):
        """Auto import orders"""

        yesterday = datetime.now() + timedelta(-1)
        houzzs = self.env['houzz.config'].search([])
        for houzz_config in houzzs:
            houzz = HouzzApi(token=houzz_config.houzz_token, user_name=houzz_config.houzz_user_name,
                             app_name=houzz_config.name)
            response = houzz.get_orders(status='New', start=yesterday, from_date=yesterday, format='json')
            
            response_decode = json.loads(response.decode('utf-8'))
            orders = response_decode['Orders']
            self.save_order(orders, self.houzz.id)
        return True


    @api.model
    def process_order(self):
        """Process Order"""
        _logger.info(self)
        return True


    @api.model
    def charge_order(self, order):
        """Charge order"""
        pass


    def create_product(self, sku_id):
        houzz = HouzzApi(token=self.houzz.houzz_token, user_name=self.houzz.houzz_user_name, app_name=self.houzz.name)
        response = houzz.get_listing(sku=sku_id).get('Listing')
        product_obj = self.env['product.template']
        pro_obj = product_obj.create({
            'name': response.get('Title'),
            'default_code': response.get('SKU'),
            'barcode': response.get('ProductId'),
            'list_price': response.get('Cost'),
            'taxes_id': None,
            'description_sale': response.get('Description'),
            'description_pickingout': response.get('Description'),
            'description_pickingin': response.get('Description'),
            'sale_ok': True,
            'purchase_ok': True,
            'supplier_taxes_id': False,
            'sale_delay': response.get('ShippingDetails').get('LeadTimeMax'),
            'type': 'product',
            'qty_available': response.get('Quantity'),
            'description': response.get('Keywords'),
            'houzz_product_description': response
            })
        return pro_obj




    @api.model
    def save_order(self, orders, houzz_id):
        """Save Order"""
        for order in orders:
            OrderId = order.get('OrderId')
            
            houzz_order_status = order.get('Status')
            CustomerName = order.get('CustomerName')
            inner_Address = order.get('Address')
           
            if inner_Address is not None:
                Address = inner_Address.get('Address')
                Address1 = inner_Address.get('Address1')
                City = inner_Address.get('City')
                Zip = inner_Address.get('Zip')
                Phone = inner_Address.get('Phone')
                State = inner_Address.get('State')

                if inner_Address.get('Country') is not None:
                    Country = order.get('Country')
                else:
                    Country = 'US'

            country_id = self.env['res.country'].search([('code', '=', Country)])

            # _logger.info(country_ids[0]['id'])

            OrderTotal = float(order.get('OrderTotal'))
            FlatShipping = float(order.get('FlatShipping'))
            Created = order.get('Created')
            LatestShipDate = datetime.strptime(Created, '%Y-%m-%d %H:%M:%S') + timedelta(+20)

            # Query State ID
            states = self.env['res.country.state'].search([
                ('country_id', '=', country_id.id),
                ('code', '=', State)
            ])
            for state in states:
                state_id = state.id

            # Create Custmer or use Existing Customer
            customer_id = self.env['res.partner'].search([('name','=', CustomerName), 
                                                          ('phone', '=', Phone), 
                                                          ('zip', '=', Zip)])
            if not customer_id:
                customer = {
                    'type': 'delivery',
                    'name': CustomerName,
                    'email': False,
                    'phone': Phone,
                    'street': Address,
                    'street2': Address1,
                    'city': City,
                    'state_id': state_id,
                    'country_id': country_id.id,
                    'zip': Zip,
                    'property_product_pricelist': 2
                }
                customer_id = self.env['res.partner'].create(customer)

            # Check if the order exists
            check_order = self.env['sale.order'].search([('client_order_ref', '=', OrderId)])

            if not check_order:
                team = self.env['houzz.config'].browse([houzz_id])
                # New Order
                sale = self.env['sale.order'].create({
                    'partner_id': customer_id.id,
                    'client_order_ref': OrderId,
                    'team_id': team.team_id.id,
                    'date_order': Created,
                    'validity_date': LatestShipDate,
                    'houzz_config_id': houzz_id,
                    'houzz_order_status': houzz_order_status,
                    'pricelist_id': 1,
                })

                for i in order.get('OrderItems'):
                    if i.get('Type') == 'Product':
                        sku = i.get('SKU')
                        product_uom_qty = int(i.get('Quantity'))
                    else:
                        sku = 'COUPON'
                        product_uom_qty = 1

                    default_code = sku.upper()
                    price_unit = float(i.get('Cost'))
                    
                    # Search Product
                    product = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
                    if not product:
                        pro_obj = self.create_product(sku_id=default_code)
                        product = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
                        self.env['sale.order.line'].create({
                            'order_id': sale.id,
                            'product_id': product.id,
                            'name': product.name,
                            'product_uom_qty': product_uom_qty,
                            'price_unit': price_unit,
                            'product_uom':1,
                            'tax_id': False
                        })

                    else:
                    
                        # Add Order Content
                        self.env['sale.order.line'].create({
                            'order_id': sale.id,
                            'product_id': product.id,
                            'name': product.name,
                            'product_uom_qty': product_uom_qty,
                            'price_unit': price_unit,
                            'product_uom':1,
                            'tax_id': False
                        })

        return True

    # @api.model
    # def ship_order(self):
    #     """Upload logistics note number"""
    #     houzzs = self.env['houzz.config'].search([])
    #     for houzz in houzzs:
    #         houzz_model = HouzzApi(token=houzz.houzz_token, user_name=houzz.houzz_user_name, app_name=houzz.name)
    #         orders = self.env['sale.order'].search(
    #             [('houzz_config_id', '=', houzz.id), ('houzz_order_status', '=', 'Charged')])
    #         for order in orders:
    #             stock_pickings = self.env['stock.picking'].search([('origin', '=', order.name)])
    #             carriers = []
    #             for picking in stock_pickings:
    #                 for track in picking.carrier_tracking_ref:
    #                     carriers.append({
    #                         'ShippingMethod': track.carrier_id.houzz_carrier_code,
    #                         'TrackingNumber': track.tracking_ref,
    #                     })
    #             if carriers:
    #                 track_numbers = ','.join([i['TrackingNumber'] for i in carriers])
    #                 shiped = houzz_model.ship_order(order_id=order.client_order_ref,
    #                                                 shipping_method=carriers[0]['ShippingMethod'],
    #                                                 tracking_number=track_numbers)
    #                 if shiped:
    #                     # Update order status to Shipped
    #                     order.update({'houzz_order_status': 'Shipped'})

    #     return True


class HouzzPaymentsImport(models.TransientModel):
    """HOUZZ settlement import"""
    _name = 'houzz.payments.import'
    _description = 'HOUZZ API Payments Import'

    houzz = fields.Many2one('houzz.config', 'Houzz', required=True)
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')


    def do_import(self):
        """Do Import Payments"""
        self.ensure_one()
        houzz = HouzzApi(token=self.houzz.houzz_token, 
                         user_name=self.houzz.houzz_user_name,
                         app_name=self.houzz.name)
        payment_ids = houzz.get_payments(from_date=self.from_date, to_date=self.to_date)
        for payment_id in payment_ids:
            payment = houzz.get_transactions(payment_id)
            payment_data = self.env['houzz.payments'].search_count([('payment_id', '=', payment_id)])
            if payment_data == 0:
                self.env['houzz.payments'].create({
                    'houzz_config_id': self.houzz.id,
                    'name': payment_id + 'Payment',
                    'payment_id': payment_id,
                    'from_date': payment['FromDate'],
                    'to_date': payment['ToDate'],
                    'sales': float(payment['Amount']),
                    # 'shipping': float(payment['Shipping']),
                    # 'tax': float(payment['Tax']),
                    'commission': float(payment['Allowance']),
                    'deposit_amount': float(payment['DepositAmount']),
                    'currency_id': self.env.ref('base.main_company').currency_id.id,
                })