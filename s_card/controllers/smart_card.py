from odoo.http import request, Response
from unidecode import unidecode
from odoo import http
from odoo.exceptions import ValidationError
import logging
import base64
import uuid
import re
import json
import os

from odoo.addons.s_card.unit import generate_cards_data

_logger = logging.getLogger(__name__)


class SmartCardForm(http.Controller):
    @http.route(['/card'], type='http', auth="public", website=True)
    def card(self, **post):
        user_id = request.env.user.id
        user_exists = request.env['res.users'].sudo().browse(user_id)
        if not user_exists:
            return {'error': 'User not found'}

        card_record = request.env['sne.card'].sudo().search([('user_id', '=', user_id)])
        if not card_record:
            return {'error': 'Card not found for the user'}

        card = generate_cards_data(card_record, user_id)
        name_without_diacritics = unidecode(card.get('name')).lower()
        card_name = re.sub(r'[^a-z0-9]+', '', name_without_diacritics)
        card_id = card.get('id')

        return request.redirect(f'/{card_name}.{card_id}')

    @http.route(['/card/form'], type='http', auth="public", website=True)
    def partner_form(self, **post):
        user_id = request.env.user.id
        card = request.env['sne.card'].sudo().search([('user_id', '=', user_id)])

        cards_data = generate_cards_data(card, user_id)

        return request.render("s_card.smart_card_form", {'cards': cards_data})

    @http.route('/card/submit', type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def customer_form_submit(self, **post):
        try:
            user_id = request.env.user.id
            smart_card = request.env['sne.card'].sudo().search([('user_id', '=', user_id)])

            if not smart_card:
                return Response('{"status": "Error", "message": "Smart card not found"}',
                                content_type='application/json', status=404)

            avatar_data, logo_data = self.get_avatar_logo(post)
            smart_card_data = self.get_card_data(post, avatar_data, logo_data)
            smart_card.write(smart_card_data)

            globe_list = self.get_list_globe(post, smart_card)
            social_list = self.get_list_social(post, smart_card)
            link_list = self.get_list_link(post, smart_card)

            request.env['globe.card'].sudo().create(globe_list)
            request.env['social.card'].sudo().create(social_list)
            request.env['link.card'].sudo().create(link_list)

            image_datas = self.get_image_data(post, smart_card)
            smart_card.write({'image': [(0, 0, image_data) for image_data in image_datas]})

            return request.redirect('/thank_you')

        except ValidationError as ve:
            _logger.error(f"Validation error submitting form: {ve}")
            return request.redirect('/validation_error')

        except Exception as e:
            _logger.error(f"Error submitting form: {e}")
            return request.redirect('/error_page')

    @http.route('/card/infor/<int:id>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def customer_update_infor(self, id, **post):
        try:
            smart_card = request.env['sne.card'].sudo().browse(id)
            if not smart_card:
                return Response('{"status": "Error", "message": "Smart card not found"}',
                                content_type='application/json', status=404)

            avatar_data, logo_data = self.get_avatar_logo(post)

            update_data = {
                'name': post.get('name'),
                'title': post.get('title'),
                'phone': post.get('phone'),
                'email': post.get('email'),
            }

            if avatar_data:
                update_data['avatar'] = avatar_data
            if logo_data:
                update_data['logo_company'] = logo_data

            smart_card.write(update_data)

            social_list = self.get_list_social(post, smart_card)
            smart_card.social.unlink()
            smart_card.write({'social': [(0, 0, social) for social in social_list]})

            return Response('{"status": "Success", "message": "Update successful"}', content_type='application/json',
                            status=200)

        except Exception as e:
            _logger.error(f"Error submitting form: {e}")
            return Response('{"status": "Error", "message": "Internal Server Error"}', content_type='application/json',
                            status=500)

    @http.route('/card/intro/<int:id>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def customer_update_intro(self, id, **post):
        try:
            smart_card = request.env['sne.card'].sudo().browse(id)

            if not smart_card:
                return Response('{"status": "Error", "message": "Smart card not found"}',
                                content_type='application/json', status=404)

            globe_list = self.get_list_globe(post, smart_card)
            link_list = self.get_list_link(post, smart_card)

            smart_card.write({
                'company': post.get('company'),
                'work_phone': post.get('work_phone'),
                'email': post.get('email'),
                'content': post.get('content'),
                'url_company': post.get('url_company'),
                'video': post.get('video'),
            })

            smart_card.globe.unlink()
            smart_card.link.unlink()
            smart_card.write({'globe': [(0, 0, globe) for globe in globe_list]})
            smart_card.write({'link': [(0, 0, link) for link in link_list]})

            return Response('{"status": "Success", "message": "Update successful"}', content_type='application/json',
                            status=200)

        except Exception as e:
            _logger.error(f"Error submitting form: {e}")
            return Response('{"status": "Error", "message": "Internal Server Error"}', content_type='application/json',
                            status=500)

    @http.route(['/card/delete'], type='http', auth="public", website=True)
    def card_delete(self, **post):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

        user_id = request.env.user.id
        card_record = request.env['sne.card'].sudo().search([('user_id', '=', user_id)])
        if not card_record:
            raise ValidationError('Card not found for the user')

        try:
            card_record.unlink()
            return request.redirect(base_url)
        except Exception as e:
            raise ValidationError(f'Failed to delete card: {str(e)}')

    @http.route('/card/image/<int:id>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def customer_add_image(self, id, **post):
        try:
            smart_card = request.env['sne.card'].sudo().browse(id)

            if not smart_card:
                return Response('{"status": "Error", "message": "Smart card not found"}',
                                content_type='application/json', status=404)

            image_datas = self.get_image_data(post, smart_card)
            smart_card.write({'image': [(0, 0, image_data) for image_data in image_datas]})

            return Response('{"status": "Success", "message": "Update successful"}', content_type='application/json',
                            status=200)

        except Exception as e:
            _logger.error(f"Error submitting form: {e}")
            return Response('{"status": "Error", "message": "Internal Server Error"}', content_type='application/json',
                            status=500)

    @http.route('/card/image/delete', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def delete_images(self, **kwargs):
        try:
            user_id = request.env.user.id
            smart_card = request.env['sne.card'].sudo().search([('user_id', '=', user_id)])

            if not smart_card:
                return {'status': 'Error', 'message': 'No images found'}

            data = json.loads(request.httprequest.data.decode('utf-8'))
            image_ids = data.get('imageIds', [])
            image_ids = [int(img_id) for img_id in image_ids]

            if not image_ids:
                return {'status': 'Error', 'message': 'No image IDs provided'}

            remaining_images = smart_card.image.filtered(lambda img: img.id not in image_ids)
            smart_card.write({'image': [(6, 0, remaining_images.ids)]})

            return {'status': 'Success', 'message': 'Images deleted successfully'}

        except Exception as e:
            _logger.error(f"Error deleting images: {e}")
            return {'status': 'Error', 'message': 'Internal Server Error'}

    @http.route('/thank_you', type='http', auth="public", website=True)
    def thank_you_page(self, **kw):
        return request.render('s_card.thank_you_page')

    @http.route('/validation_error', type='http', auth="public", website=True)
    def validation_error_page(self, **kw):
        return request.render('s_card.validation_error_page')

    @http.route('/error', type='http', auth="public", website=True)
    def error_page(self, **kw):
        return request.render('s_card.error_page')

    def get_card_data(self, post, avatar_data, logo_data):
        smart_card_data = {
            'name': post.get('name'),
            'title': post.get('title'),
            'company': post.get('company'),
            'phone': post.get('phone'),
            'work_phone': post.get('work_phone'),
            'email': post.get('email'),
            'content': post.get('content'),
            'video': post.get('video'),
            'url_company': post.get('url_company'),
            'avatar': avatar_data,
            'logo_company': logo_data,
        }
        return smart_card_data

    def create_records(post, smart_card, model_name, name_prefix, key_prefix):
        record_list = []
        for key, value in post.items():
            if key.startswith(name_prefix):
                index = key.split('_')[-1]
                data_key = f"{key_prefix}_{index}"
                record_list.append({
                    'name': value,
                    model_name: post.get(data_key),
                    'card_id': smart_card.id,
                })
        return record_list

    def get_list_social(self, post, smart_card):
        social_list = []
        for key, value in post.items():
            if key.startswith('social_name_'):
                index = key.split('_')[-1]
                social_key = 'social_' + index
                social_list.append({
                    'name': value,
                    'social': post.get(social_key),
                    'card_id': smart_card.id,
                })
        return social_list

    def get_list_globe(self, post, smart_card):
        globe_list = []
        for key, value in post.items():
            if key.startswith('globe_name'):
                index = key.split('_')[-1]
                globe_key = 'globe_' + index
                globe_list.append({
                    'name': value,
                    'globe': post.get(globe_key),
                    'card_id': smart_card.id,
                })
        return globe_list

    def get_list_link(self, post, smart_card):
        link_list = []
        for key, value in post.items():
            if key.startswith('link_name'):
                index = key.split('_')[-1]
                link_key = 'link_' + index
                link_list.append({
                    'name': value,
                    'link': post.get(link_key),
                    'card_id': smart_card.id,
                })
        return link_list

    def get_image_data(self, post, smart_card):
        image_datas = []
        for key, value in post.items():
            if key.startswith('image_'):
                link_key = 'image_' + key.split('_')[-1]
                image_file = request.httprequest.files.get(link_key)
                if image_file:
                    image_data = base64.b64encode(image_file.read())
                    image_datas.append({
                        'name': f"{str(uuid.uuid4())}.png",
                        'type': 'binary',
                        'datas': image_data,
                        'res_model': 'sne.card',
                        'res_id': smart_card.id,
                    })
        return image_datas

    def get_avatar_logo(self, post):
        avatar = request.httprequest.files.get('avatar')
        logo_company = request.httprequest.files.get('logo_company')

        try:
            if avatar:
                avatar_data = base64.b64encode(avatar.read())
            else:
                default_avatar_path = os.path.abspath('odoo-custom/scard/s_card/static/description/avatar.png')
                with open(default_avatar_path, 'rb') as default_avatar_file:
                    avatar_data = base64.b64encode(default_avatar_file.read())
        except Exception as e:
            _logger.error('Error while reading default avatar image: %s' % e)
            avatar_data = None

        try:
            if logo_company:
                logo_data = base64.b64encode(logo_company.read())
            else:
                default_logo_path = os.path.abspath('odoo-custom/scard/s_card/static/description/logo_company.png')
                with open(default_logo_path, 'rb') as default_logo_file:
                    logo_data = base64.b64encode(default_logo_file.read())
        except Exception as e:
            _logger.error('Error while reading default logo image: %s' % e)
            logo_data = None

        return avatar_data, logo_data
