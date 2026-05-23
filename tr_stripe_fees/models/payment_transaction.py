import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    stripe_fee_amount = fields.Monetary(
        string='Stripe Fee', currency_field='currency_id', readonly=True)
    stripe_base_amount = fields.Monetary(
        string='Base Amount', currency_field='currency_id', readonly=True)

    def _get_specific_processing_values(self, processing_values):
        # Fee must be applied BEFORE super() because Stripe's override creates the
        # PaymentIntent (using self.amount) inside that super() call. Applying it after
        # would create a PI for the base amount while storing the inflated amount on the
        # transaction, causing a "amounts don't match" validation error on the webhook.
        if self.provider_code == 'stripe' and not self.stripe_fee_amount:
            provider = self.provider_id
            if provider.stripe_fees_active:
                is_international = False
                if self.partner_id and self.partner_id.country_id:
                    company_country = self.env.company.country_id
                    is_international = self.partner_id.country_id != company_country
                fee = provider._compute_stripe_fee(self.amount, is_international)
                if fee > 0:
                    base = self.amount
                    new_amount = base + fee
                    self.write({
                        'amount': new_amount,
                        'stripe_fee_amount': fee,
                        'stripe_base_amount': base,
                    })
                    _logger.info(
                        'Stripe fee applied: base=%s fee=%s total=%s', base, fee, new_amount
                    )
                    # Add fee line to linked sale orders so order.amount_total == tx.amount.
                    # Without this, website_sale shows "amount does not match your cart".
                    self._stripe_add_fee_line_to_orders(fee, provider)
        return super()._get_specific_processing_values(processing_values)

    def _create_payment(self, **extra_create_values):
        """Inject a write-off line for the Stripe fee so the journal entry reads:
            Dr Bank:          base + fee
              Cr Receivable:  base   (reconciles with the invoice)
              Cr Fee Income:  fee    (posted to the configured income account)
        """
        if (
            self.provider_code == 'stripe'
            and self.stripe_fee_amount > 0
            and self.provider_id.stripe_fee_income_account_id
        ):
            fee = self.stripe_fee_amount
            fee_account = self.provider_id.stripe_fee_income_account_id
            company_currency = self.company_id.currency_id
            if self.currency_id == company_currency:
                balance = -fee
            else:
                balance = -self.currency_id._convert(
                    fee, company_currency, self.company_id, fields.Date.today()
                )
            write_off = extra_create_values.setdefault('write_off_line_vals', [])
            write_off.append({
                'account_id': fee_account.id,
                'amount_currency': -fee,
                'balance': balance,
                'name': 'Stripe Processing Fee',
            })
            _logger.info(
                'Stripe fee write-off added: fee=%s account=%s',
                fee, fee_account.display_name,
            )
        return super()._create_payment(**extra_create_values)

    def _stripe_add_fee_line_to_orders(self, fee, provider):
        """Add a Stripe fee order line to linked sale orders so that
        order.amount_total == tx.amount and website_sale's confirmation
        page does not show the 'amount does not match cart' warning.
        """
        fee_product = provider.stripe_fee_product_id
        if not fee_product:
            return
        sale_orders = getattr(self, 'sale_order_ids', self.env['sale.order'])
        if not sale_orders:
            return
        SaleLine = self.env['sale.order.line'].sudo()
        for order in sale_orders.sudo():
            # Remove any previously added fee line to avoid duplicates on retry
            order.order_line.filtered(
                lambda l: l.product_id == fee_product
            ).unlink()
            SaleLine.create({
                'order_id': order.id,
                'product_id': fee_product.id,
                'name': 'Stripe Processing Fee',
                'product_uom_qty': 1,
                'price_unit': fee,
                'tax_id': [],
            })
            _logger.info(
                'Stripe fee line added to order %s: %s', order.name, fee
            )
