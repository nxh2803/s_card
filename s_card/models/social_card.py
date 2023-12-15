from odoo import fields, models, api
from odoo.exceptions import ValidationError


class SocialCard(models.Model):
    _name = 'social.card'
    _rec_name = 'name'
    _description = 'Social Card'

    SOCIAL_MEDIA_SELECTION = [
        ('facebook', 'Facebook'),
        ('zalo', 'Zalo'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('pinterest', 'Pinterest'),
        ('snapchat', 'Snapchat'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('youtube', 'YouTube'),
        ('reddit', 'Reddit'),
        ('spotify', 'Spotify'),
        ('soundcloud', 'SoundCloud'),
        ('twitch', 'Twitch'),
        ('github', 'GitHub'),
        ('stackoverflow', 'Stack Overflow')
    ]

    name = fields.Char(string='Name', required=True, help='Social Media Name')
    social = fields.Char(string='Link', required=True)
    card_id = fields.Many2one(comodel_name='sne.card', string='Card', ondelete='cascade')

    @api.onchange('name')
    def _onchange_name(self):
        if self.name and self.name not in dict(self.SOCIAL_MEDIA_SELECTION).keys():
            raise ValidationError('Requires entering the correct social network name.')

    @api.model
    def create(self, values):
        encrypted_vals = self._encrypt_fields(values)
        res = super(SocialCard, self).create(encrypted_vals)
        return res

    def write(self, values):
        if 'name' in values or 'social' in values:
            encrypted_vals = self._encrypt_fields(values)
            super(SocialCard, self).write(encrypted_vals)
        else:
            super(SocialCard, self).write(values)
        return True

    def _encrypt_fields(self, values):
        encrypted_vals = values.copy()
        if 'name' in values:
            if values['name'] not in dict(self.SOCIAL_MEDIA_SELECTION).keys():
                raise ValidationError('Requires entering the correct social network name.')
            encrypted_vals['name'] = self.env['sne.card'].encrypt_data(values.get('name', ''))
        if 'social' in values:
            encrypted_vals['social'] = self.env['sne.card'].encrypt_data(values.get('social', ''))
        return encrypted_vals

    def read(self, fields=None, load='_classic_read'):
        records = super(SocialCard, self).read(fields=fields, load=load)

        for record in records:
            record['name'] = self.env['sne.card'].decrypt_data(record.get('name', ''))
            record['social'] = self.env['sne.card'].decrypt_data(record.get('social', ''))

        return records
