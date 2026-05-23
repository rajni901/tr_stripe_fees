{
    'name': 'Stripe Fees — Charge Customers Processing Fees',
    'version': '19.0.1.2.0',
    'category': 'Accounting/Payment',
    'summary': 'Automatically add Stripe processing fees to customer payments on eCommerce checkout and invoice portal.',
    'description': """
Stripe Fees Extension — by Technical Rajni
==========================================
Pass Stripe processing fees to your customers automatically.

Features:
- Add fixed + percentage fees on Stripe payments
- Separate rates for Domestic and International transactions
- Works on eCommerce website checkout
- Works on invoice portal payments
- Fee shown to customer before payment
- Transaction log with fee breakdown
    """,
    'author': 'Technical Rajni',
    'website': 'https://www.technicalrajni.com',
    'license': 'OPL-1',
    'depends': ['payment_stripe', 'website_sale', 'account'],
    'data': [
        'data/product_data.xml',
        'views/payment_provider_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'assets': {
        'web.assets_frontend': [
            'tr_stripe_fees/static/src/js/checkout_fees.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 5.00,
    'currency': 'USD',
}
