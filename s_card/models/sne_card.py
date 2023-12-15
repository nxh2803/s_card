# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.s_card.unit import get_qr_code
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from odoo.exceptions import ValidationError
import logging
import base64
from unidecode import unidecode
import re
import uuid
from PIL import Image
from io import BytesIO

_logger = logging.getLogger(__name__)

try:
    import vobject
except ImportError:
    _logger.warning(
        "`vobject` Python module not found, vcard file generation disabled. Consider installing this module if you want to generate vcard files")
    vobject = None


class SmartCard(models.Model):
    _name = 'sne.card'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Smart Card'
    _rec_name = 'code'

    CHAR_FIELDS = ['name', 'title', 'company', 'phone', 'work_phone', 'email']

    code = fields.Char(string='Code', required=True,
                       readonly=True, default=lambda self: _('New'))
    qr_code_img = fields.Binary(string='Image QR', copy=False)
    logo_company = fields.Binary(string='Logo Company', copy=False)
    avatar = fields.Binary(string='Avatar')
    image = fields.Many2many('ir.attachment', string="Image")
    name = fields.Char(string='Name', tracking=True)
    title = fields.Char(string='Title', tracking=True)
    company = fields.Char(string='Company', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    work_phone = fields.Char(string='Work Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    content = fields.Text(string='Content')
    globe = fields.One2many('globe.card', 'card_id', string='Globe')
    social = fields.One2many('social.card', 'card_id', string='Social')
    link = fields.One2many('link.card', 'card_id', string='Link')
    video = fields.Char(string='Video URL', help='YouTube video URL')
    url = fields.Char(string='URL Website')
    url_company = fields.Char(string='Company URL', tracking=True)

    user_id = fields.Many2one('res.users', string='Related User', ondelete='cascade',
                              default=lambda self: self.env.user)
    follower_ids = fields.Many2many('res.users', string='Followers', help='Users who are following this card')

    @api.model
    def create(self, vals):
        user_id = self.env.user.id
        existing_card = self.env['sne.card'].search([('user_id', '=', user_id)])
        if existing_card:
            raise ValidationError('A user can create only one card.')

        encrypted_vals = self._encrypt_fields(vals)
        if vals.get('reference_no', _('New')) == _('New'):
            encrypted_vals['code'] = self.env['ir.sequence'].next_by_code('sne.card') or _('New')
        res = super(SmartCard, self).create(encrypted_vals)
        res.gen_qr_code()
        res._compute_thumbnail_images()
        return res

    @api.model
    def _auto_init(self):
        super(SmartCard, self)._auto_init()
        if not self.env['ir.config_parameter'].sudo().get_param('private_key'):
            self.generate_rsa_key_pair()

    def read(self, fields=None, load='_classic_read'):
        records = super(SmartCard, self).read(fields=fields, load=load)

        for record in records:
            for field in self.CHAR_FIELDS:
                if field in record and record[field]:
                    record[field] = self.decrypt_data(record[field])

        return records

    def write(self, vals):
        encrypted_vals = self._encrypt_fields(vals)
        res = super(SmartCard, self).write(encrypted_vals)

        if 'image' in vals:
            self._compute_thumbnail_images()

        return res

    def _encrypt_fields(self, vals):
        encrypted_vals = vals.copy()
        for field in self.CHAR_FIELDS:
            field_value = vals.get(field, '')
            if field_value:
                encrypted_vals[field] = self.encrypt_data(field_value)
        return encrypted_vals

    @api.onchange('phone')
    def _onchange_normalize_phone(self):
        for card in self:
            card.phone = self._normalize_phone(card.phone)

    @api.onchange('work_phone')
    def _onchange_normalize_work_phone(self):
        for card in self:
            card.work_phone = self._normalize_phone(card.work_phone)

    def _compute_thumbnail_images(self):
        for attachment in self.image:
            random_uuid = str(uuid.uuid4())
            attachment.name = f"{random_uuid}.png"
            if attachment.datas and len(attachment.datas) > 1048576:
                image_data = base64.b64decode(attachment.datas)
                img = Image.open(BytesIO(image_data))
                img.thumbnail((800, 800))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue())
                attachment.datas = img_str

    def _normalize_phone(self, phone):
        if phone and isinstance(phone, str):
            phone = re.sub(r'\D', '', phone)
            if phone.startswith('0'):
                phone = '+84' + phone[1:]
        return phone

    def gen_qr_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        name = self.decrypt_name(self.name)
        self.qr_code_img = get_qr_code(f'{base_url}/{name}.{self.id}')

    def action_web_card(self):
        name = self.decrypt_name(self.name)
        url = f'/{name}.{self.id}'
        return {
            'type': 'ir.actions.act_url',
            'target': 'fullscreen',
            'url': url,
        }

    def decrypt_name(self, name):
        name_encrypt = self.decrypt_data(name)
        name = unidecode(name_encrypt).replace(' ', '').lower()
        return name

    def generate_rsa_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        if not self.env['ir.config_parameter'].sudo().get_param('private_key'):
            self.env['ir.config_parameter'].set_param('private_key', private_pem)
            self.env['ir.config_parameter'].set_param('public_key', public_pem)

    def encrypt_data(self, data_to_encrypt):
        public_key_pem = self.env['ir.config_parameter'].sudo().get_param('public_key')
        public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))

        data_bytes = data_to_encrypt.encode('utf-8')

        try:
            encrypted_data = public_key.encrypt(data_bytes,
                                                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                             algorithm=hashes.SHA256(), label=None))
            encrypted_data_base64 = base64.b64encode(encrypted_data)
            encrypted_data_str = encrypted_data_base64.decode('utf-8')

            return encrypted_data_str

        except Exception as e:
            _logger.error('Error while encrypting data: %s' % e)
            raise

    def decrypt_data(self, data_to_decrypt):
        if data_to_decrypt is None or data_to_decrypt is False:
            return None

        private_key_pem = self.env['ir.config_parameter'].sudo().get_param('private_key')
        private_key = serialization.load_pem_private_key(private_key_pem.encode('utf-8'), password=None,
                                                         backend=default_backend())
        try:
            data_base64 = base64.b64decode(data_to_decrypt)

            decrypted_data = private_key.decrypt(data_base64,
                                                 padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                              algorithm=hashes.SHA256(), label=None)
                                                 )
            decrypted_data_str = decrypted_data.decode('utf-8', errors='replace')
            return decrypted_data_str

        except Exception as e:
            _logger.error('Error while decrypting data: %s' % e)
            raise

    def process_attachment(self, attachment):
        return {
            'name': attachment.name,
            'datas': attachment.datas,
            'type': attachment.mimetype,
            'res_id': attachment.res_id,
            'id': attachment.id,
        }

    def process_generic_record(self, record, fields):
        return {field: self.decrypt_data(getattr(record, field)) for field in fields}
