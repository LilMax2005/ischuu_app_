# Ischuu Flet App - Estructura MVC

Este proyecto reorganiza la app original en una arquitectura MVC para que sea más fácil de mantener, escalar y conectar a un backend.

## Estructura

```text
ischuu_app_/
├── app/
│   ├── controllers/
│   │   └── app_controller.py
│   ├── data/
│   │   └── seed.py
│   ├── models/
│   │   ├── entities.py
│   │   └── state.py
│   ├── utils/
│   │   └── formatters.py
│   └── views/
│       ├── auth.py
│       ├── cart.py
│       ├── components.py
│       ├── orders.py
│       ├── profile.py
│       └── store.py
├── main.py
├── README.md
└── requirements.txt
```

## Cómo ejecutar

```bash
pip install -r requirements.txt
pip install "flet[all]"
python main.py

```

## Qué quedó separado

### Modelos
- `entities.py`: clases `Product`, `CartItem`, `Order`, `User`
- `state.py`: lógica de negocio del carrito, login, registro, pedidos y filtros

### Vistas
- `auth.py`: login y registro
- `store.py`: tienda, tarjetas de productos y banner social
- `cart.py`: carrito y checkout visual
- `orders.py`: pedidos
- `profile.py`: perfil
- `components.py`: header, navbar y componentes reutilizables

### Controlador
- `app_controller.py`: conecta eventos de Flet con el estado y decide qué vista renderizar

## Siguiente paso recomendado

Después de esta base MVC, lo ideal es separar también una capa de servicios para conectar:
- FastAPI
- PostgreSQL o MongoDB
- autenticación JWT
- pagos
- administración de inventario real
