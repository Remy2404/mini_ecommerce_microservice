# Product Service

Owns `categories` and `products` in `products_db`.

Products are exposed with a stable `category` name in API responses while the
database stores a category foreign key internally. Product reads may use Valkey
as a short-lived cache with `product:{product_id}` keys.
