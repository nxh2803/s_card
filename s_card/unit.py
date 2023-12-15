# -*- coding: utf-8 -*-

import qrcode
import base64
import io
import os
import logging

_logger = logging.getLogger(__name__)


def get_qr_code(data):
    if data != "":
        img = qrcode.make(data)
        result = io.BytesIO()
        img.save(result, format='PNG')
        result.seek(0)
        img_bytes = result.read()
        base64_encoded_result_bytes = base64.b64encode(img_bytes)
        base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
        return base64_encoded_result_str


def generate_cards_data(cards, user_id):
    card = cards
    return {
        'id': cards.id,
        'code': cards.code,
        'qr_code_img': cards.qr_code_img,
        'logo_company': cards.logo_company,
        'avatar': cards.avatar,
        'content': cards.content,
        'video': cards.video,
        'url': cards.url,
        'user_id': cards.user_id,
        'user_id_current': user_id,
        'url_company': cards.url_company,
        'image': [cards.process_attachment(attachment) for attachment in cards.image],
        'globe': [cards.process_generic_record(globe_record, ['name', 'globe']) for globe_record in cards.globe],
        'social': [cards.process_generic_record(social_record, ['name', 'social']) for social_record in
                   cards.social],
        'link': [cards.process_generic_record(link_record, ['name', 'link']) for link_record in cards.link],
        'name': cards.decrypt_data(cards.name),
        'title': cards.decrypt_data(cards.title),
        'company': cards.decrypt_data(cards.company),
        'phone': cards.decrypt_data(cards.phone),
        'work_phone': cards.decrypt_data(cards.work_phone),
        'email': cards.decrypt_data(cards.email),
    }

def get_image_avatar_logo():
    try:
        default_avatar_path = os.path.abspath('odoo-custom/scard/s_card/static/description/avatar.png')
        with open(default_avatar_path, 'rb') as default_avatar_file:
            avatar_data = base64.b64encode(default_avatar_file.read())
    except Exception as e:
        _logger.error('Error while reading default avatar image: %s' % e)
        avatar_data = None

    try:
        default_logo_path = os.path.abspath('odoo-custom/scard/s_card/static/description/logo_company.png')
        with open(default_logo_path, 'rb') as default_logo_file:
            logo_data = base64.b64encode(default_logo_file.read())
    except Exception as e:
        _logger.error('Error while reading default logo image: %s' % e)
        logo_data = None

    return avatar_data, logo_data
