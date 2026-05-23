from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    stripe_fees_active = fields.Boolean(
        string='Charge Stripe Fees to Customer', default=False)

    # Domestic fees
    stripe_fee_fixed = fields.Float(
        string='Domestic Fixed Fee', default=0.30,
        help='Fixed fee per transaction (e.g. 0.30 for $0.30)')
    stripe_fee_percent = fields.Float(
        string='Domestic Percentage Fee', default=2.9,
        help='Percentage fee (e.g. 2.9 for 2.9%)')

    # International fees
    stripe_intl_fee_fixed = fields.Float(
        string='International Fixed Fee', default=0.30)
    stripe_intl_fee_percent = fields.Float(
        string='International Percentage Fee', default=3.9,
        help='Usually higher for international cards (e.g. 3.9%)')

    def _compute_stripe_fee(self, amount, is_international=False):
        """Calculate the Stripe fee for a given amount."""
        if not self.stripe_fees_active:
            return 0.0
        fixed = self.stripe_intl_fee_fixed if is_international else self.stripe_fee_fixed
        percent = self.stripe_intl_fee_percent if is_international else self.stripe_fee_percent
        return round(fixed + (amount * percent / 100.0), 2)
