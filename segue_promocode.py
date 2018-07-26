"""
passso para execução:
1. acessar a pasta /opt/segue no servidor.
2. ativar o virtualenv: source /opt/segue/env/bin/activate
3. rodar o shell: python manage shell
4. alterar os parâmetros
5. copiar o código e colar no shell
"""

import datetime

from segue.account.models import Account
from segue.purchase.promocode import PromoCodeService


qty = 300 #quantidade de códicos

data = {
    'description': 'Promo LOCAWEB',     #descrição sucinta
    'hash_code': 'PROMOLOCAWEB',         #código que a pessoa usa
    'discount': 0.5,                     #desconto 0.01 até 1.0 
    'product_id': 36,                     #id do produto dá uma olhada no 36 http://segue.fisl18.softwarelivre.org:8080/admin/mgmt/product/36/change/
    'start_at': '26/05/2018',   #dia mês ano 
    'end_at': '15/07/2018'      #até o final do evento
}


#pode deixar como o meu mesmo
creator = Account.query.filter(Account.email=='ricardo@solis.com.br').first()
service = PromoCodeService()

try:
    promocodes = service.create(data, quantity=qty, creator=creator)
    print('Códigos criados: {}'.format(len(promocodes)))
except Exception as ex:
    print('Pow', ex)
