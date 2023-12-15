from odoo import fields, models, api


class LinkCard(models.Model):
    _name = 'link.card'
    _rec_name = 'name'
    _description = 'Link Card'

    name = fields.Char(string='Name', required=True)
    link = fields.Char(string='Link', required=True)
    card_id = fields.Many2one(comodel_name='sne.card', string='Card', ondelete='cascade')

    @api.model
    def create(self, values):
        encrypted_vals = self._encrypt_fields(values)
        res = super(LinkCard, self).create(encrypted_vals)
        return res

    def write(self, values):
        if 'name' in values or 'link' in values:
            encrypted_vals = self._encrypt_fields(values)
            super(LinkCard, self).write(encrypted_vals)
        else:
            super(LinkCard, self).write(values)
        return True

    def _encrypt_fields(self, values):
        encrypted_vals = values.copy()
        if 'name' in values:
            encrypted_vals['name'] = self.env['sne.card'].encrypt_data(values.get('name', ''))
        if 'link' in values:
            encrypted_vals['link'] = self.env['sne.card'].encrypt_data(values.get('link', ''))
        return encrypted_vals

    def read(self, fields=None, load='_classic_read'):
        records = super(LinkCard, self).read(fields=fields, load=load)

        for record in records:
            record['name'] = self.env['sne.card'].decrypt_data(record.get('name', ''))
            record['link'] = self.env['sne.card'].decrypt_data(record.get('link', ''))

        return records
