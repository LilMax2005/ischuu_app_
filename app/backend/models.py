"""Modelos documentales de referencia para MongoDB.

En esta versión se usa Motor directamente, por lo que los documentos se guardan
como diccionarios en las colecciones: users, products y orders.
Los esquemas de entrada/salida están definidos en app.schemas.
"""

USERS_COLLECTION = "users"
PRODUCTS_COLLECTION = "products"
ORDERS_COLLECTION = "orders"
