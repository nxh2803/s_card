# -*- coding: utf-8 -*-
import json
from base64 import b64decode
import werkzeug
from odoo import http, _
from odoo.http import request
import base64
import logging
import re
from werkzeug.urls import url_encode
from unidecode import unidecode
from odoo.exceptions import ValidationError, UserError
from odoo.addons.s_card.unit import generate_cards_data, get_image_avatar_logo
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.auth_signup.models.res_users import SignupError

_logger = logging.getLogger(__name__)

try:
    import vobject
except ImportError:
    _logger.warning(
        "`vobject` Python module not found, vcard file generation disabled. Consider installing this module if you want to generate vcard files")
    vobject = None


class SmartCard(Home):
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                user_id = request.env.user.id
                card = self.create_sne_card(qcontext)
                card = generate_cards_data(card, user_id)

                name_without_diacritics = unidecode(card.get('name')).lower()
                card_name = re.sub(r'[^a-z0-9]+', '', name_without_diacritics)
                card_id = card.get('id')

                # Send an account creation confirmation email
                User = request.env['res.users']
                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                )

                template = request.env.ref('auth_signup.mail_template_user_signup_account_created',
                                           raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)

                return request.redirect(f'/{card_name}.{card_id}')

            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')), ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode({'login': user.login, 'redirect': '/web'}))

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def create_sne_card(self, qcontext):
        avatar_data, logo_data = get_image_avatar_logo()
        card_data = {
            'title': 'Positions',
            'company': 'Company Name',
            'email': qcontext.get('login'),
            'name': qcontext.get('name'),
            'phone': '+55 5555 5555',
            'work_phone': '+55 5555 5555',
            'content': 'Introduce your company here.',
            'avatar': avatar_data,
            'logo_company': logo_data,
        }
        smart_card = request.env['sne.card'].sudo().create(card_data)
        globe_list = [{'name': 'Head Office', 'globe': 'Ha Noi, Viet Nam', 'card_id': smart_card.id, }]
        social_list = [{'name': 'facebook', 'social': 'https://www.facebook.com/', 'card_id': smart_card.id, }]
        link_list = [{'name': 'Fanpage', 'link': 'https://www.facebook.com/', 'card_id': smart_card.id, }]

        request.env['globe.card'].sudo().create(globe_list)
        request.env['social.card'].sudo().create(social_list)
        request.env['link.card'].sudo().create(link_list)

        return smart_card

    @http.route(['/<string:name>.<int:id>'], auth="public", json=True)
    def card_template(self, name, id):
        model_card = request.env['sne.card'].sudo()
        card = model_card.browse(id)
        current_url = request.httprequest.base_url

        if card:
            card.write({'url': current_url})

        user_id = request.env.user.id
        cards_data = generate_cards_data(card, user_id)

        return request.render('s_card.card_template_update', {
            'cards': cards_data
        })

    @http.route('/vcf/<int:id>', auth='public')
    def action_save_contacts(self, id):
        model_card = request.env['sne.card'].sudo()
        card = model_card.browse(id)
        if card:
            user_id = request.env.user.id
            cards_data = generate_cards_data(card, user_id)
            name_without_diacritics = unidecode(cards_data.get('name')).lower()
            card_name = re.sub(r'[^a-z0-9]+', '', name_without_diacritics)
            vcf_filename = f"{card_name}.vcf"

            vcf_content = self._get_card_file(card, user_id)

            response = http.request.make_response(vcf_content, headers=[('Content-Type', 'text/vcard')])
            response.headers.add('Content-Disposition', f'attachment; filename="{vcf_filename}"')

            return response
        else:
            return http.request.make_response('Card not found', status=404)

    @http.route('/follow/<int:user_id>', type='http', auth='public', methods=['POST'], csrf=False)
    def follow_card(self, user_id):
        try:
            if not user_id:
                return http.Response('Missing user_id parameter', status=400)

            if not request.session.uid:
                return http.Response('User not logged in', status=401)

            current_user_id = request.env.user.id
            card = request.env['sne.card'].sudo().search([('user_id', '=', current_user_id)], limit=1)

            if card:
                card.write({'follower_ids': [(4, int(user_id))]})
                return http.Response(
                    'User {} is now following card {}'.format(user_id, card.id), status=200)
            else:
                return http.Response('Card not found for the current user', status=404)

        except Exception as e:
            return http.Response(str(e), status=500)

    @http.route('/followers/<int:user_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_followers(self, user_id):
        try:
            user_exists = request.env['res.users'].sudo().browse(user_id)
            if not user_exists:
                return {'error': 'User not found'}

            card = request.env['sne.card'].sudo().search([('user_id', '=', user_id)])
            if not card:
                return {'error': 'Card not found for the user'}

            follower_ids = [follower.id for follower in card.follower_ids]

            follower_data = {}
            for follower_id in follower_ids:
                card = request.env['sne.card'].sudo().search([('user_id', '=', follower_id)])
                cards_data = generate_cards_data(card, follower_id)
                follower_dict = {
                    'id': cards_data['id'],
                    'name': cards_data['name'],
                    'title': cards_data['title'],
                    'company': cards_data['company'],
                    'url': cards_data['url'],
                }
                follower_data[card.id] = follower_dict

            return http.Response(
                json.dumps({'success': True, 'followers': follower_data}),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return http.Response(str(e), status=500)

    @http.route('/search/<string:search_string>', type='http', auth='public', methods=['GET'],
                csrf=False)
    def search_followers(self, search_string):
        try:
            user_id = request.env.user.id
            user_exists = request.env['res.users'].sudo().browse(user_id)
            if not user_exists:
                return {'error': 'User not found'}

            card_model = request.env['sne.card'].sudo()
            card = card_model.search([('user_id', '=', user_id)])
            if not card:
                return {'error': 'Card not found for the user'}

            follower_ids = card.follower_ids.ids if card.follower_ids else []
            card_list = [generate_cards_data(card_model.search([('user_id', '=', follower_id)]), user_id) for
                         follower_id in
                         follower_ids]

            user_ids = [
                {'user_id': card['user_id'].id}
                for card in card_list
                if search_string in (card['name'], card['phone'], card['work_phone'], card['title'])
            ]

            return http.Response(
                json.dumps({'success': True, 'user_ids': user_ids}),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return http.Response(str(e), status=500)

    def _get_card_file(self, card, user_id):
        vcard = self._build_vcard(card, user_id)
        if vcard:
            return vcard.serialize().encode('utf-8')
        return False

    def _build_vcard(self, card, user_id):
        cards_data = generate_cards_data(card, user_id)

        if not vobject:
            return False
        vcard = vobject.vCard()

        n = vcard.add('n')
        n.value = vobject.vcard.Name(family=cards_data.get('name'))

        fn = vcard.add('fn')
        fn.value = cards_data.get('name')

        count = 0

        if cards_data.get('title'):
            title = vcard.add('title')
            title.value = cards_data.get('title')

        if cards_data.get('company'):
            org = vcard.add('org')
            org.value = [cards_data.get('company')]

        if cards_data.get('email'):
            count += 1
            email = vcard.add(f'item{count}.email')
            email.value = cards_data.get('email')
            email.type_param = 'Internet'
            x_ablabel_email = vcard.add(f'item{count}.x-ablabel')
            x_ablabel_email.value = 'Email'

        if cards_data.get('work_phone'):
            count += 1
            tel = vcard.add(f'item{count}.tel')
            tel.type_param = ['pref']
            tel.value = cards_data.get('work_phone')
            x_ablabel_tel = vcard.add(f'item{count}.x-ablabel')
            x_ablabel_tel.value = 'Hotline'

        if cards_data.get('globe'):
            for globe_record in cards_data.get('globe'):
                count += 1
                adr = vcard.add(f'item{count}.adr')
                adr.type_param = 'pref'
                adr.value = globe_record.get('globe')
                x_ablabel_globe = vcard.add(f'item{count}.x-ablabel')
                x_ablabel_globe.value = 'Address'
                x_abadr_globe = vcard.add(f'item{count}.x_abadr')
                x_abadr_globe.value = 'vn'

        if cards_data.get('url'):
            count += 1
            x_url = vcard.add(f'item{count}.url')
            x_url.value = cards_data.get('url')
            x_ablabel_url = vcard.add(f'item{count}.x-ablabel')
            x_ablabel_url.value = 'Profile'

        if cards_data.get('avatar'):
            photo = vcard.add('photo')
            photo.value = b64decode(cards_data.get('avatar'))
            photo.encoding_param = 'B'
            photo.type_param = 'JPG'

        if cards_data.get('social'):
            for social_record in cards_data.get('social'):
                count += 1
                x_social = vcard.add(f'item{count}.url')
                x_social.type_param = social_record.get('name').lower()
                x_social.value = social_record.get('social')
                x_ablabel_social = vcard.add(f'item{count}.x-ablabel')
                x_ablabel_social.value = 'Link'

        if cards_data.get('link'):
            for link_record in cards_data.get('link'):
                count += 1
                x_social = vcard.add(f'item{count}.url')
                x_social.type_param = link_record.get('name').lower()
                x_social.value = link_record.get('link')
                x_ablabel_link = vcard.add(f'item{count}.x-ablabel')
                x_ablabel_link.value = 'Link'

        if cards_data.get('content'):
            note = vcard.add('note')
            note.value = cards_data.get('content')

        return vcard

    @http.route('/media/<int:res_id>/<string:image_name>', auth='public')
    def get_image(self, res_id, image_name):
        try:
            attachment = request.env['ir.attachment'].sudo().search(
                [('res_model', '=', 'sne.card'), ('res_id', '=', res_id), ('name', '=', image_name)])
            if not attachment:
                return http.request.make_response('Image not found', status=404)

            image_content = base64.b64decode(attachment.datas)
            response = http.request.make_response(image_content, headers=[('Content-Type', 'image/jpeg')])
            response.headers.add('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline';")
            response.headers.add('Content-Disposition', f'inline; filename="{attachment.name}"')

            return response
        except ValidationError as e:
            return http.request.make_response(f'Error: {e}', status=500)
