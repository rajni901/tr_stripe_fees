import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Auto-set stripe_fee_product_id on all existing Stripe providers."""
    tmpl = env.ref(
        'tr_stripe_fees.product_template_stripe_fee', raise_if_not_found=False
    )
    if not tmpl:
        return
    fee_product = tmpl.product_variant_id
    if not fee_product:
        return
    providers = env['payment.provider'].search([('code', '=', 'stripe')])
    for provider in providers:
        if not provider.stripe_fee_product_id:
            provider.stripe_fee_product_id = fee_product
            _logger.info(
                'Auto-set stripe_fee_product_id on provider %s', provider.name
            )
