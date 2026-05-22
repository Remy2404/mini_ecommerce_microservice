"""Cart service logic."""
from .repository import get_cart, save_cart, get_backup_cart, clear_backup_cart
from datetime import datetime

def calculate_total(items):
    return sum(item["subtotal"] for item in items)

def add_item(user_id: str,product: dict,quantity: int):
    cart = get_cart(user_id)
    
    if not cart: 
        cart = {
            "cart_id":f"cart_{user_id}",
            "user_id":user_id,
            "items":[],
            "total_amount":0,
        }
    # check if product exist
    found = False
    for item in cart['items']:
        if item['product_id'] == product['product_id']:
            item['quantity'] += quantity
            item['subtotal'] = item['quantity'] * item['unit_price']
            found = True
            
    if not found:
        cart['items'].append({
            "product_id": product['product_id'],
            "name": product['name'],
            'quantity':quantity,
            'unit_price':product['price'],
            'subtotal':quantity * product['price'], 
        })
    cart['total_amount'] = calculate_total(cart['items'])
    cart['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_cart(user_id,cart)
    return cart

def get_user_cart(user_id: str):
    return get_cart(user_id)

def remove_item(user_id: str,product_id: str):
    cart = get_cart(user_id)
    if not cart: 
        return None
    
    cart['items'] = [
        item for item in cart['items']
        if item['product_id'] != product_id
    ]
    
    cart['total_amount']  = calculate_total(cart['items'])
    cart['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_cart(user_id,cart)
    
    return cart

def restore_cart(order_id: str):
    backup = get_backup_cart(order_id)
    
    if not backup:
        return None
    
    user_id = backup['user_id']
    save_cart(user_id,backup)
    clear_backup_cart(order_id)
    return backup
    