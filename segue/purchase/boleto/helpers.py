from segue.core import config

class BoletoConfig(object):

    def __init__(self, category=''):
        self.category = category

    def __getattr__(self, name):
        config_name = self.with_category(name)
        if config_name in config:
            return config[config_name]
        else:
            return config[self.without_category(name)]

    def with_category(self, name):
        return 'BOLETO_{}_{}'.format(self.category.upper(), name)

    def without_category(self, name):
        return 'BOLETO_{}'.format(name)
