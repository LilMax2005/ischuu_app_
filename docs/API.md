# API principal de Ischuu

Base local: `http://127.0.0.1:8000/api/v1`  
Swagger: `http://127.0.0.1:8000/docs`

Las rutas privadas usan `Authorization: Bearer <token>`. Un usuario desactivado recibe 403 aunque su token no haya vencido.

## Autenticación

| Método | Ruta | Acceso | Descripción |
| --- | --- | --- | --- |
| POST | `/auth/register` | Público | Crea una cuenta activa |
| POST | `/auth/login` | Público | Recibe formulario `username` y `password`; devuelve JWT |
| GET | `/auth/me` | Usuario activo | Perfil, puntos, dirección y permisos |
| GET | `/auth/me/points` | Usuario activo | Saldo de puntos |
| PATCH | `/auth/me/shipping-address` | Usuario activo | Guarda dirección de despacho |
| PATCH | `/auth/me/notifications` | Usuario activo | Activa o desactiva push |
| GET | `/notifications/config` | Público | App ID público y estado de OneSignal |
| POST | `/notifications/test` | Usuario activo | Envía una prueba al teléfono vinculado |
| POST | `/password/forgot` | Público | Solicita recuperación sin revelar si existe el correo |
| POST | `/password/reset` | Público | Cambia contraseña con token vigente |

## Catálogo, pagos y pedidos

| Método | Ruta | Acceso | Descripción |
| --- | --- | --- | --- |
| GET | `/products` | Público | Catálogo ordenado por categoría y nombre |
| POST | `/products/seed` | Admin | Reinicia el catálogo de demostración |
| POST | `/payments/webpay/quote` | Usuario activo | Calcula subtotal, envío, descuentos y total |
| POST | `/payments/webpay/cart` | Usuario activo | Crea una transacción Webpay |
| POST | `/payments/webpay/commit` | Token de pago | Confirma la transacción |
| GET/POST | `/payments/webpay/return` | Webpay | Callback del proveedor |
| GET | `/payments/webpay/status/{token}` | Propietario o admin | Estado del pago y revisión manual |
| GET | `/orders` | Usuario activo | Lista pedidos propios |
| GET | `/orders/{id}` | Propietario | Detalle de un pedido propio |

Ejemplo de cotización:

```json
{
  "items": [{"product_id": "665000000000000000000001", "quantity": 2}],
  "use_points": true
}
```

## Administración

Todas estas rutas exigen una cuenta activa con `is_admin=true`.

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/admin/summary` | Métricas generales |
| GET/PATCH | `/admin/users`, `/admin/users/{id}` | Lista y administra usuarios |
| GET/POST | `/admin/products` | Lista y crea productos |
| PATCH/DELETE | `/admin/products/{id}` | Edita o elimina producto |
| PATCH | `/admin/products/{id}/stock` | Agrega o fija stock no negativo |
| POST | `/admin/products/upload-image` | Sube JPG, PNG o WebP de hasta 5 MB |
| GET | `/admin/orders` | Lista todos los pedidos |
| GET | `/admin/orders/export` | Exporta XLSX |
| GET | `/admin/orders/{id}` | Detalle administrativo |
| PATCH | `/admin/orders/{id}/status` | Cambia estado y notifica al cliente |
| GET/PATCH | `/admin/settings` | Configura enlaces sociales |

Ejemplo para cambiar un estado:

```json
{"status": "En despacho"}
```

Estados válidos: `Pagado`, `Preparando`, `En despacho`, `Entregado` y `Cancelado`.

## Respuestas de error relevantes

| Código | Significado |
| --- | --- |
| 400 | Entrada inválida o carrito vacío |
| 401 | Token ausente o inválido |
| 403 | Usuario inactivo o sin permisos |
| 404 | Recurso inexistente o pedido ajeno |
| 409 | Correo repetido, stock insuficiente o conflicto al confirmar pago |
| 413 | Imagen mayor a 5 MB |
| 422 | El body no cumple el esquema |
| 502 | Webpay no está disponible o rechazó la operación técnica |
