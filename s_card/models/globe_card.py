from odoo import fields, models, api


class GlobeCard(models.Model):
    _name = 'globe.card'
    _rec_name = 'name'
    _description = 'Globe Card'

    name = fields.Char(string='Name', required=True)
    globe = fields.Char(string='Globe', required=True)
    card_id = fields.Many2one(comodel_name='sne.card', string='Card', ondelete='cascade')

    @api.model
    def create(self, values):
        encrypted_vals = self._encrypt_fields(values)
        res = super(GlobeCard, self).create(encrypted_vals)
        return res

    def write(self, values):
        if 'name' in values or 'globe' in values:
            encrypted_vals = self._encrypt_fields(values)
            super(GlobeCard, self).write(encrypted_vals)
        else:
            super(GlobeCard, self).write(values)
        return True

    def _encrypt_fields(self, values):
        encrypted_vals = values.copy()
        if 'name' in values:
            encrypted_vals['name'] = self.env['sne.card'].encrypt_data(values.get('name', ''))
        if 'globe' in values:
            encrypted_vals['globe'] = self.env['sne.card'].encrypt_data(values.get('globe', ''))

        return encrypted_vals

    def read(self, fields=None, load='_classic_read'):
        records = super(GlobeCard, self).read(fields=fields, load=load)

        for record in records:
            record['name'] = self.env['sne.card'].decrypt_data(record.get('name', ''))
            record['globe'] = self.env['sne.card'].decrypt_data(record.get('globe', ''))

        return records
