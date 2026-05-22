"""Cart router."""
from fastapi import APIRouter , Query
from .service import add_item, remove_item, get_user_cart, restore_cart
    
router = APIRouter(prefix="/cart",tags=['Cart'])

# fake product will call real product when have
def fake_product(product_id):
    return {
        "product_id": product_id,
        "name":"Keyboard",
        "price": 50
    }
@router.get("/")
def get_cart(user_id: str = Query(...)):
    return get_user_cart(user_id)

@router.post('/items')
def add_to_cart(user_id: str,product_id: str,quantity: int):
    product = fake_product(product_id)
    return add_item(user_id,product,quantity)

@router.delete("/items/{product_id}")
def remove_from_cart(user_id: str,product_id: str):
    return remove_item(user_id,product_id)