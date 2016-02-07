# -*- coding: utf-8 -*-

from segue.errors import SegueError

class NoSuchProduct(SegueError):
    code = 404
    def to_json(self):
        return { 'message': 'cannot find a product like that' }

class WrongBuyerForProduct(SegueError):
    code = 403
    def to_json(self):
        return { 'message': 'product cannot be bought by this buyer' }

class ProductExpired(SegueError):
    code = 403
    def to_json(self):
        return { 'message': 'product is no longer being sold' }


class MinimumAmount(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'Valor mínimo para doação é de R$ 10,00.' }


