import datetime
from typing import Type, Optional
from woocommerce import API

# optional, add a memoiser here that supports unhashables
def get_json(api, path, params=None):
    return api.get(path, params=params).json()


class DotDict(dict):
    '''Dict accessable via attributes rather than indices'''
    def __getattr__(self, name):
        result = self.get(name)
        if isinstance(result, dict):
            return DotDict(**result)
        return result


class WooObject:
    '''Base for Woo Commerce object'''
    str_type: str
    endpoint: Optional[str]

    def __init__(self, api, id, data=None):
        self.api = api
        self.id = id
        self._data = DotDict(**data) if data else None

    def _get_data(self):
        return DotDict(get_json(self.api, f'{self.endpoint}/{self.id}'))

    @property
    def data(self):
        if not self._data:
            self._data = self._get_data()
        return self._data

    def __getattr__(self, name):
        return getattr(self.data, name)

    def __str__(self):
        return f'{self.str_type}(id={self.data["id"]})'

    def serialise(self):
        return self.data


class Order(WooObject):
    str_type = 'Order'
    endpoint = 'orders'

    @property
    def refunds(self):
        return Refunds(self.api, self.id)

class Customer(WooObject):
    str_type = 'Customer'
    endpoint = 'customers'

class Refund(WooObject):
    '''Refunds are directly tied to an order'''
    str_type = 'Refund'
    endpoint = None

    def __init__(self, api: API, order_id, id, data=None):
        super().__init__(api, id, data)
        self.order_id = order_id
        self.endpoint = f'orders/{order_id}/refunds'

class Product(WooObject):
    str_type = 'Product'
    endpoint = 'products'

class TaxRate(WooObject):
    str_type = 'TaxRate'
    endpoint = 'taxes'

class Collection:
    '''Collections of Woo Commerce objects'''
    cls_type: Type[WooObject]
    endpoint: str

    def __init__(self, api: API, filters=None):
        self.api = api
        self.filters = filters or {}
        self._data = []

    def filter_by(self, **filters):
        return self.__class__(self.api, {**self.filters, **filters})

    def __getitem__(self, id: str):
        return self._create_object(id)

    def _create_object(self, id, data=None) -> WooObject:
        return self.cls_type(self.api, id, data)

    def __iter__(self):
        # loop through our internal data first
        for obj in self._data:
            yield self._create_object(obj['id'], obj)

        per_page = 20
        params = {
            'offset': len(self._data),
            'per_page': per_page,
            **self.filters
        }
        while True:
            objects = get_json(self.api, self.endpoint, params=params)
            for obj in objects:
                self._data.append(obj)
                yield self._create_object(obj['id'], obj)
            
            if len(objects) < per_page:
                break

            params['offset'] += per_page

    def serialise(self):
        return [obj.serialise() for obj in self]

class Orders(Collection):
    cls_type = Order
    endpoint = 'orders'

    def for_customer(self, customer_id: str):
        return self.filter_by(customer=customer_id)

    def modified_after(self, date: datetime.datetime):
        date_str = date.isoformat()
        return self.filter_by(modified_after=date_str)

class Customers(Collection):
    cls_type = Customer
    endpoint = 'customers'

class Refunds(Collection):
    '''Refunds are associated with an Order, and are not globally discoverable'''
    cls_type: Type[Refund] = Refund

    def __init__(self, api: API, order_id, filters=None):
        super().__init__(api, filters)
        self.order_id = order_id
        self.endpoint = f'orders/{order_id}/refunds'

    def _create_object(self, id, data=None):
        return self.cls_type(self.api, self.order_id, id, data)

class Products(Collection):
    cls_type = Product
    endpoint = 'products'

class TaxRates(Collection):
    cls_type = TaxRate
    endpoint = 'taxes'


class Woo:
    '''Woo Commerce API wrapper'''
    def __init__(self, *args, api: Optional[API]=None, **kwargs):
        self.api = api or API(*args, **kwargs)
        self.orders = Orders(self.api)
        self.customers = Customers(self.api)
        self.products = Products(self.api)
        self.taxes = TaxRates(self.api)
