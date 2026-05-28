# Ischuu Unificado

Aplicación de tienda online para **Ischuu**, orientada a la venta de Blind Box, coleccionables kawaii/anime, pagos con Webpay, sistema de puntos, seguimiento de pedidos y panel administrador.

El proyecto está desarrollado en **Python** usando:

- **Flet** para el frontend.
- **FastAPI** para el backend.
- **MongoDB Atlas** como base de datos.
- **JWT** para autenticación.
- **Transbank Webpay Plus** en ambiente de prueba.
- Arquitectura separada en backend, frontend, servicios, vistas, modelos y controladores.

---

## 1. Objetivo del proyecto

El objetivo es construir una app para que los usuarios puedan:

- Registrarse e iniciar sesión.
- Ver catálogo de productos.
- Buscar productos por nombre, serie o categoría.
- Agregar productos al carrito.
- Mantener el carrito guardado aunque se cierre sesión o la app.
- Pagar con Webpay Plus en ambiente de prueba.
- Generar pedidos solo cuando el pago sea confirmado.
- Ver seguimiento de pedidos.
- Acumular puntos por compras.
- Usar puntos como descuento.
- Recibir descuentos según preferencias de compra.
- Acceder a una vista de administrador con `admin@ischuu.cl`.

---

## 2. Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python | Lenguaje principal |
| Flet | Interfaz gráfica |
| FastAPI | API backend |
| Uvicorn | Servidor backend |
| MongoDB Atlas | Base de datos cloud |
| Motor / PyMongo | Conexión a MongoDB |
| JWT | Autenticación |
| pwdlib[argon2] | Hash de contraseñas |
| HTTPX | Cliente HTTP frontend-backend |
| Transbank SDK | Webpay Plus |
| python-dotenv | Variables de entorno |

---

## 3. Arquitectura general

El proyecto se ejecuta desde un único archivo raíz:

```text
main.py
```

Ese archivo levanta:

1. Backend FastAPI en `http://127.0.0.1:8000`.
2. Frontend Flet como aplicación visual.

Estructura esperada:

```text
ischuu_unificado/
├── main.py
├── requirements.txt
├── .env
├── README.md
│
└── app/
    ├── backend/
    │   ├── main.py
    │   ├── db.py
    │   ├── core/
    │   │   ├── config.py
    │   │   └── security.py
    │   ├── routers/
    │   │   ├── auth.py
    │   │   ├── products.py
    │   │   ├── orders.py
    │   │   ├── payments.py
    │   │   └── admin.py
    │   └── services/
    │       ├── catalog.py
    │       ├── pricing.py
    │       └── transbank.py
    │
    └── frontend/
        ├── controllers/
        │   └── app_controller.py
        ├── models/
        │   ├── entities.py
        │   └── state.py
        ├── services/
        │   └── api_client.py
        ├── utils/
        │   └── formatters.py
        └── views/
            ├── auth.py
            ├── store.py
            ├── cart.py
            ├── orders.py
            ├── profile.py
            ├── admin.py
            ├── components.py
            └── theme.py
```

---

## 4. Funcionalidades implementadas

### 4.1 Autenticación

La app permite:

- Login.
- Registro.
- Uso de token JWT.
- Diferenciación entre usuario normal y administrador.

Usuario administrador por defecto:

```text
Correo: admin@ischuu.cl
Clave: Admin1234
```

El backend fuerza que este usuario tenga:

```json
{
  "is_admin": true,
  "is_active": true
}
```

---

### 4.2 Catálogo de productos

El catálogo permite visualizar:

- Nombre.
- Serie.
- Categoría.
- Rareza.
- Precio.
- Stock.
- Imagen.
- Descripción.
- Indicador de producto original o alternativo.

Incluye:

- Buscador.
- Filtro por categoría.
- Cards visuales con estilo oscuro/kawaii inspirado en Instagram.

---

### 4.3 Carrito de compras

El carrito permite:

- Agregar productos.
- Aumentar cantidad.
- Disminuir cantidad.
- Eliminar productos.
- Ver subtotal.
- Ver envío.
- Ver descuentos.
- Ver total final calculado por backend.
- Verificar pagos pendientes.
- Mantener el carrito guardado aunque se cierre la app.

Archivo local del carrito:

```text
ischuu_cart_local.json
```

Cuando un pago queda autorizado, el carrito se limpia automáticamente.

---

### 4.4 Notificaciones de carrito

Al agregar un producto, la app muestra:

```text
Artículo añadido al carrito
```

Además, la barra inferior puede mostrar la cantidad de productos:

```text
Carrito (1)
Carrito (2)
Carrito (3)
```

---

### 4.5 Envío

Regla de envío:

```text
Envío: $3.000
Envío gratis desde: $25.000
```

Ejemplo:

```text
Subtotal: $12.990
Envío: $3.000
Total sin descuentos: $15.990
```

---

### 4.6 Sistema de puntos

Lógica definida:

```text
Cada $500 pagados en productos = 1 punto
Cada 1 punto equivale a $50 de descuento
```

Importante:

- El envío no genera puntos.
- Los puntos se generan solo si el pago fue autorizado.
- Los puntos se descuentan solo si el usuario decide usarlos.
- Si el pago falla o se cancela, no se descuentan puntos.

Ejemplo:

```text
Compra de productos: $15.000
Puntos ganados: 30 puntos
```

Ejemplo de descuento:

```text
Usuario tiene: 100 puntos
100 puntos x $50 = $5.000 de descuento
```

---

### 4.7 Descuentos por puntos

El usuario puede activar:

```text
Usar puntos disponibles
```

El backend calcula:

- Puntos disponibles.
- Puntos usados.
- Descuento aplicado.
- Total final para Webpay.

Ejemplo:

```text
Subtotal backend: $12.990
Descuento preferencias: -$650
Descuento puntos: -$2.575
Total Webpay: $12.765
```

---

### 4.8 Preferencias del usuario

La app guarda preferencias según las categorías compradas.

Ejemplos:

```text
Anime
Labubu
Pokemon
```

Si una categoría se vuelve preferida, puede aplicar descuento.

Regla aplicada:

```text
Descuento por categoría preferida: 5%
```

---

### 4.9 Webpay Plus

La integración usa **Webpay Plus en ambiente de prueba**.

Flujo:

```text
Carrito
↓
Backend calcula total real
↓
Se crea transacción Webpay
↓
Usuario paga en banco de prueba
↓
Transbank retorna token_ws
↓
Backend confirma el pago
↓
Si el pago es AUTHORIZED:
    se crea el pedido
    se descuentan puntos usados
    se generan nuevos puntos
    se actualizan preferencias
    se descuenta stock
    se limpia carrito
```

Datos de banco de prueba:

```text
RUT: 11.111.111-1
Clave: 123
```

---

### 4.10 Seguimiento de pedidos

Los pedidos solo se crean cuando Webpay confirma:

```text
AUTHORIZED
```

Estados definidos:

```text
Compra realizada
Artículo empaquetado
Artículo enviado
Artículo entregado
```

El usuario normal solo ve el seguimiento.  
Solo el administrador puede modificar estados.

---

### 4.11 Panel administrador

El usuario:

```text
admin@ischuu.cl
```

tiene acceso a la vista **Admin**.

Puede:

- Ver productos.
- Añadir stock.
- Reponer/fijar stock.
- Ver usuarios.
- Activar/desactivar usuarios.
- Dar/quitar rol admin.
- Modificar puntos.
- Ver pedidos de todos los usuarios.
- Actualizar el estado del pedido.

Estados permitidos:

```text
Compra realizada
Artículo empaquetado
Artículo enviado
Artículo entregado
```

---

## 5. Variables de entorno

Crear archivo:

```text
.env
```

Ejemplo:

```env
APP_NAME=Ischuu
SECRET_KEY=CAMBIAR_SECRET_POR_UNA_CLAVE_SEGURA
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

MONGODB_URL=mongodb+srv://USUARIO:CLAVE@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGODB_DATABASE=ischuu

API_BASE_URL=http://127.0.0.1:8000

TBK_ENV=integration
MEMBERSHIP_AMOUNT=20000
```

No subir contraseñas reales a GitHub.

---

## 6. MongoDB Atlas

Pasos:

1. Crear cuenta en MongoDB Atlas.
2. Crear un cluster.
3. Crear usuario de base de datos.
4. Habilitar IP en Network Access.
5. Obtener connection string desde:

```text
Database > Cluster > Connect > Drivers > Python
```

Ejemplo:

```text
mongodb+srv://ischuu_user:<db_password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

Reemplazar `<db_password>` por la contraseña real, sin usar los símbolos `< >`.

---

## 7. Instalación

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Si `python` no funciona:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 8. Ejecución

```powershell
python main.py
```

Esto levanta:

```text
Backend: http://127.0.0.1:8000
Frontend: Flet App
```

Documentación API:

```text
http://127.0.0.1:8000/docs
```

---

## 9. Endpoints principales

### Auth

```text
POST /api/v1/auth/login
POST /api/v1/auth/register
GET  /api/v1/auth/me
```

### Productos

```text
GET  /api/v1/products
POST /api/v1/products/seed
```

### Pedidos

```text
GET /api/v1/orders
```

### Pagos

```text
POST /api/v1/payments/webpay/quote
POST /api/v1/payments/webpay/cart
GET  /api/v1/payments/webpay/status/{token}
GET  /api/v1/payments/webpay/return
POST /api/v1/payments/webpay/return
```

### Admin

```text
GET   /api/v1/admin/users
PATCH /api/v1/admin/users/{user_id}

GET   /api/v1/admin/products
PATCH /api/v1/admin/products/{product_id}/stock

GET   /api/v1/admin/orders
PATCH /api/v1/admin/orders/{order_id}/status
```

---

## 10. Archivos importantes

### `main.py`

Levanta backend y frontend en un solo comando.

### `app/backend/main.py`

Configura FastAPI, CORS, routers, usuario admin inicial y catálogo inicial.

### `app/backend/services/pricing.py`

Contiene reglas de:

- Envío.
- Puntos.
- Descuentos.
- Preferencias.
- Total final Webpay.

### `app/backend/services/transbank.py`

Contiene la conexión con Webpay Plus en ambiente de prueba.

### `app/frontend/controllers/app_controller.py`

Controlador principal del frontend.

Coordina:

- Login.
- Registro.
- Carrito.
- Pagos.
- Pedidos.
- Vista admin.
- Estado visual de la app.

### `app/frontend/views/`

Contiene las vistas:

```text
auth.py
store.py
cart.py
orders.py
profile.py
admin.py
components.py
theme.py
```

---

## 11. Problemas comunes

### `TU_CLUSTER.mongodb.net does not exist`

El `.env` sigue usando una URL falsa.

Solución:

```env
MONGODB_URL=mongodb+srv://usuario:clave@cluster-real.mongodb.net/?retryWrites=true&w=majority
```

---

### `argon2 hash algorithm is not available`

Instalar:

```powershell
pip install "pwdlib[argon2]"
```

---

### `coroutine was never awaited`

Se llamó una función async sin `await`.

Solución en Flet:

```python
controller.run_async(controller.handle_login(email, password))
```

---

### `User object has no attribute get`

El frontend usa objeto `User`, pero alguna vista lo trata como diccionario.

Mal:

```python
user.get("name")
```

Bien:

```python
getattr(user, "name", "")
```

---

### `User object is not subscriptable`

Mal:

```python
user["name"]
```

Bien:

```python
getattr(user, "name", "")
```

---

### `Tab.__init__() got unexpected keyword argument`

Algunas versiones de Flet no soportan ciertos argumentos de `ft.Tab`.

Solución aplicada:

- Evitar `ft.Tabs` en admin.
- Usar botones para cambiar entre:
  - Stock
  - Pedidos
  - Usuarios

---

## 12. Recomendaciones de seguridad

Antes de publicar:

- No subir `.env` con claves reales.
- Cambiar `SECRET_KEY`.
- Cambiar contraseña del usuario admin.
- No compartir URL de MongoDB con contraseña.
- Usar variables de entorno.
- Configurar CORS correctamente en producción.
- Usar HTTPS.
- Usar credenciales reales de Transbank solo en producción.

---

## 13. Estado actual del proyecto

El proyecto cuenta con:

- Frontend Flet funcional.
- Backend FastAPI funcional.
- MongoDB Atlas.
- Login y registro.
- Catálogo.
- Carrito persistente.
- Webpay Plus en prueba.
- Pedidos creados solo con pago autorizado.
- Sistema de puntos.
- Descuentos por puntos.
- Descuentos por preferencias.
- Envío gratis desde $25.000.
- Perfil.
- Seguimiento.
- Panel administrador.
- Gestión de stock.
- Gestión de usuarios.
- Gestión de pedidos.

---

## 14. Próximas mejoras sugeridas

- Estadísticas visuales en admin.
- CRUD completo de productos.
- Carga de imágenes desde formulario admin.
- Historial de cambios de pedidos.
- Notificación por correo al cambiar estado.
- Integración real con Instagram/TikTok.
- Exportación de pedidos a Excel.
- Vista de detalle de pedido.
- Recuperación de contraseña.
- Empaquetado como aplicación instalable.
