# Cart Service

Owns cart state in Valkey only. Cart keys use `cart:{user_id}`.

`POST /cart/items` accepts only `user_id`, `product_id`, and `quantity`. The
service fetches trusted product name and price from Product Service before
calculating item subtotals and cart totals.
