# Woob

Pythonic WooCommerce API wrapper.

## Usage

```
from woob import Woo
from datetime import datetime, timedelta

# either pass in your woocommerce credentials
woo = Woo(
    url=url,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
)
# or pass an existing api connection directly
# woo = Woo(api=existing_woo_api)

# collections support iteration
for order in woo.orders:
    print(order)
    for refund in order.refunds:
        print(refund)

for customer in woo.customers:
    print(customer)

for product in woo.products:
    print(product)

# iterate taxes
for tax_rate in woo.taxes:
    print(tax_rate)



# filter objects using woo api filters
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

last_7_days = woo.orders.filter_by(
    modified_after=start_date.isoformat(),
    modified_before=end_date.isoformat()
)


# collections support access by id
# in this case, an order
order_id = '123'
order = woo.orders[order_id]

# all objects support serialisation
data = order.serialise()

# all collections support serialisation
orders = woo.orders.serialise()



# convenience functions / wrappers around filter_by

# get orders by customer
customer_id = '123'
for order in woo.orders.for_customer(customer_id):
    print(order)

# orders after a certain date
for order in woo.orders.modified_after(start_date):
    print(order)
```

