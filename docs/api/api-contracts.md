# API Contracts

## Cart

### Add item to cart

`POST /cart/items`

Request body:

```json
{
  "user_id": "{{user_id}}",
  "product_id": "{{product_id}}",
  "quantity": 2
}
```

The Cart Service does not accept `name` or `unit_price` from clients. It fetches
the trusted product name and price from `PRODUCT_SERVICE_URL` using
`GET /products/{product_id}` and calculates item subtotals and cart totals
server-side.
