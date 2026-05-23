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
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'stripe':
            return res

        provider = self.provider_id
        if not provider.stripe_fees_active:
            return res

        # Detect international: check partner country vs company country
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
            _logger.info('Stripe fee applied: base=%s fee=%s total=%s', base, fee, new_amount)

        return res
