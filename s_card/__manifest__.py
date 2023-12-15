# -*- coding: utf-8 -*-
{
    'name': "Smart Card",
    'author': "Snine",
    'company': 'SNine',
    'maintainer': 'SNine',
    'website': "https://www.snine.vn",
    'category': 'Services/Card',
    'version': '1.0.0',
    'depends': ['base', 'mail', 'website', 'web', 'auth_signup'],
    'data': [
        'security/ir.model.access.csv',
        'views/sne_card_view.xml',
        # 'views/card_template.xml',
        'views/card_template_update.xml',
        'views/globe_card_view.xml',
        'views/link_card_view.xml',
        'views/social_card_view.xml',
        'views/menuitem.xml',
        'views/card_form.xml',
        'views/card_update.xml',
        'views/thank_you_page.xml',
        'views/error_page.xml',
        'views/validation_error_page.xml',
        # 'views/card_document.xml',
        'data/sequence_card.xml',
        'data/card_form.xml',
    ],
    'license': 'OEEL-1',
    'installable': True,
    'application': True,

    # 'assets': {
    #     'web.assets_backend': [
    #         's_card/static/src/js/add_contact.js'
    #     ],
    # },
}
