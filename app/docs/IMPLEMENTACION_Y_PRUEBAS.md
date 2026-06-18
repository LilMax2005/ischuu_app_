# Informe de implementación y pruebas

Este documento relaciona los requisitos solicitados con el código actual. Los estados utilizados son:

- **Verificado:** ya existía y se comprobó durante la revisión.
- **Corregido:** existía, pero tenía un error o riesgo.
- **Implementado:** se agregó durante esta entrega.
- **Externo:** requiere credenciales o servicios reales para completar la evidencia de punta a punta.

## Autenticación y usuarios

| Estado | Funcionalidad | Archivo y cambio | Funcionamiento y prueba |
| --- | --- | --- | --- |
| Verificado | Registro de usuarios | `routers/auth.py`, `schemas.py`: registro validado y correo único | `POST /api/v1/auth/register`; repetir correo debe responder 409 |
| Corregido | Inicio de sesión | `routers/auth.py`: respuesta 401 consistente y control de cuenta activa | `POST /api/v1/auth/login` con credenciales válidas, inválidas e inactivas |
| Verificado | Consultar puntos | `routers/auth.py`: `/me` mantiene los puntos; se agregó `/me/points` | Autenticarse y ejecutar `GET /api/v1/auth/me/points` |
| Corregido | Bloquear usuarios inactivos | `dependencies.py`: `get_current_active_user` protege todas las acciones privadas | Usar un token emitido antes de desactivar la cuenta; las rutas deben responder 403 |
| Verificado | Activar o desactivar usuarios | `routers/admin.py`: actualización de `is_active` | Admin: `PATCH /api/v1/admin/users/{id}` |
| Corregido | Validación del administrador | `dependencies.py` y `frontend/controllers/app_controller.py`: solo se acepta `is_admin`; se eliminó el correo especial | Una cuenta normal llamada `admin@ischuu.cl` debe recibir 403 |
| Corregido | Protección administrativa | `get_current_admin` se usa en todas las rutas de `routers/admin.py` y en el seed del catálogo | Probar cada ruta admin con usuario normal y administrador |
| Corregido | Administrador inicial | `main.py` y `core/config.py`: se eliminaron credenciales fijas; se usan `ADMIN_EMAIL` y `ADMIN_PASSWORD` | Iniciar una base vacía con ambas variables y comprobar la cuenta creada |

## Catálogo de productos

| Estado | Funcionalidad | Archivo y cambio | Funcionamiento y prueba |
| --- | --- | --- | --- |
| Verificado | Obtener productos | `routers/products.py`: `GET /api/v1/products` | Consultar el endpoint sin autenticación |
| Verificado | Mostrar blind boxes | `services/catalog.py` y vistas Flet | Iniciar con catálogo vacío y comprobar la carga inicial |
| Verificado | Precio, stock, categoría e imagen | `models.py`: serializador único de productos | Revisar la respuesta JSON y las tarjetas de tienda |
| Corregido | Orden por categoría | `routers/products.py`: orden por categoría y luego nombre | Crear productos desordenados y consultar el catálogo |
| Corregido | Stock insuficiente | `services/cart.py`: error 409 con disponible y solicitado | Cotizar una cantidad mayor al stock |
| Corregido | Seed de catálogo | `routers/products.py`: ahora exige administrador | Usuario normal debe recibir 403 en `POST /products/seed` |

## Carrito, puntos, descuentos y envío

| Estado | Funcionalidad | Archivo y cambio | Funcionamiento y prueba |
| --- | --- | --- | --- |
| Verificado | Agregar productos | `frontend/controllers/app_controller.py` | Agregar desde Tienda y revisar Carrito |
| Corregido | Evitar agregar stock cero | `app_controller.py`: validación previa para productos agotados | Intentar agregar un producto con stock 0 |
| Verificado | Subtotal, envío, descuentos y total | `services/pricing.py` y `frontend/views/cart.py` | `POST /payments/webpay/quote` y revisar el resumen |
| Verificado | Canje de puntos | `services/pricing.py` | Activar “Usar puntos” con saldo suficiente |
| Verificado | Puntos ganados | `services/pricing.py`: 1 punto por $500 pagados en productos | Suite `tests/test_pricing.py` |
| Verificado | Categorías favoritas | `services/pricing.py`: 5 % sobre categorías preferidas | Suite `tests/test_pricing.py` |
| Verificado | Envío gratis | `services/pricing.py`: gratis desde $25.000 | Suite `tests/test_pricing.py` |
| Corregido | Carrito vacío | `services/cart.py`: respuesta 400 explícita; botón de pago deshabilitado | Suite `tests/test_cart_and_stock.py` |
| Corregido | Productos duplicados | `services/cart.py`: consolida cantidades antes de validar stock | Enviar el mismo `product_id` dos veces y comprobar suma única |

## Reglas de stock

| Estado | Funcionalidad | Archivo y cambio | Funcionamiento y prueba |
| --- | --- | --- | --- |
| Implementado | Regla central de reserva | `services/checkout.py`: `reserve_stock` | Suite `tests/test_cart_and_stock.py` |
| Verificado | Validación previa al pago | `services/cart.py`: consulta el producto real | Cotizar o pagar una cantidad superior al stock |
| Corregido | Descuento solo tras autorización | `services/checkout.py`: se ejecuta después de validar `AUTHORIZED` | Pago rechazado no debe llamar al update de productos |
| Corregido | Evitar stock negativo | Update atómico con filtro `stock >= quantity` | Dos confirmaciones concurrentes no pueden descontar por debajo de cero |
| Corregido | Descuento único | Claim atómico del pago e índice único por `webpay_token` | Repetir callback; solo existe un pedido y un descuento |
| Implementado | Compensación | Si una reserva parcial falla, se devuelve el stock ya descontado | Suite `test_partial_stock_reservation_is_rolled_back` |

## Webpay y creación del pedido

| Estado | Funcionalidad | Archivo y cambio | Funcionamiento y prueba |
| --- | --- | --- | --- |
| Verificado | Pagar carrito | `routers/payments.py` y cliente Flet | Iniciar checkout desde Carrito |
| Corregido | Crear transacción | `routers/payments.py`: validaciones antes de llamar Transbank | Mock del SDK y prueba manual en integración |
| Corregido | Confirmar token | `committed_transaction`: reutiliza transacción guardada en reintentos | Repetir retorno de un pago ya procesado |
| Implementado | Validar respuesta Webpay | `services/checkout.py`: estado, monto y buy order deben coincidir | Suite `tests/test_checkout.py` |
| Corregido | Momento de creación | Solo después de `AUTHORIZED` y de reclamar el pago | Pago rechazado devuelve `order_created=false` |
| Corregido | Error 500 inicial | Fallos del proveedor se convierten en 502 con mensaje estable y log interno | Simular excepción de `create_webpay_transaction` |
| Implementado | Revisión manual | Pago cobrado sin stock se marca `requires_manual_review` sin crear pedido inconsistente | Simular cambio de stock entre inicio y autorización |

## Pedidos y panel administrativo

| Estado | Funcionalidad | Archivo y cambio | Funcionamiento y prueba |
| --- | --- | --- | --- |
| Corregido | Pedido con estado Pagado | `services/checkout.py`: estado inicial `Pagado` | Autorizar pago y consultar pedido |
| Verificado | Cliente ve sus pedidos | `routers/orders.py` | `GET /api/v1/orders` solo devuelve pedidos propios |
| Implementado | Consultar un pedido | `GET /api/v1/orders/{id}` valida propietario | Consultar pedido propio y ajeno |
| Corregido | Cambiar estado | `services/orders.py` centraliza estado, historial, correo y push | Admin ejecuta `PATCH /admin/orders/{id}/status` |
| Corregido | Estados consistentes | `models.py`, vistas admin y pedidos: Pagado, Preparando, En despacho, Entregado y Cancelado | Revisar dropdown y seguimiento visual |
| Verificado | Ver usuarios | `GET /api/v1/admin/users` | Probar con admin y usuario normal |
| Corregido | Modificar stock | `StockUpdate` impide negativos y exige operación válida | Probar `add`, `set`, valores negativos y producto inexistente |
| Verificado | Activar usuarios | `PATCH /api/v1/admin/users/{id}` | Cambiar `is_active` y volver a iniciar sesión |
| Implementado | Evitar autobloqueo admin | Un administrador no puede desactivarse ni quitarse permisos a sí mismo | Enviar ambos cambios sobre su propio ID |

## Errores encontrados y corregidos

1. Las cuentas inactivas podían iniciar sesión y seguir usando tokens antiguos.
2. Cualquier usuario con el correo fijo del administrador obtenía acceso administrativo en backend y frontend.
3. Existían credenciales administrativas codificadas en dos archivos.
4. El endpoint que borraba y recargaba todo el catálogo era público.
5. Había tres implementaciones distintas de autenticación por token.
6. `admin.py` contenía dos implementaciones de cambio de estado, una de ellas sin ruta asociada.
7. `payments.py` contenía dos funciones idénticas de dirección de despacho.
8. Dos líneas de negocio de puntos distintas convivían en módulos diferentes; se eliminó la copia sin uso.
9. El stock se descontaba con `$inc` sin condición y podía quedar negativo por concurrencia.
10. El stock se validaba al iniciar el pago, pero no nuevamente al autorizarlo.
11. Un carrito podía repetir el mismo producto y evadir la validación de cantidad acumulada.
12. El monto y la orden devueltos por Webpay no se comparaban con el pago guardado.
13. Un reintento concurrente podía crear dos pedidos antes de que `order_created` cambiara.
14. El endpoint de recuperación devolvía el token secreto en la respuesta (`dev_token`).
15. El script `seed.py` importaba un nombre de base de datos inexistente.
16. La conexión a MongoDB forzaba TLS incluso contra el contenedor local; ahora se detecta Atlas y puede configurarse con `MONGODB_TLS`.
17. El entorno `.venv` local apunta a una instalación de Python eliminada.
18. El controlador Flet repetía hasta tres veces los métodos de dirección de despacho; se dejó una sola implementación.

## Evidencia automatizada

Comando de la suite completa:

```powershell
python -m unittest discover -s tests -v
```

Pruebas incluidas:

- `test_pricing.py`: totales, envío gratis, puntos y preferencias.
- `test_security.py`: usuario inactivo, administrador real y token bearer.
- `test_cart_and_stock.py`: carrito vacío, duplicados, falta de stock, update condicional y rollback.
- `test_checkout.py`: pago rechazado, monto alterado, idempotencia, pedido Pagado y concurrencia.

Ejecución realizada en esta entrega:

```text
tests.test_pricing: 4 pruebas ejecutadas, 4 correctas.
compileall: todos los archivos Python compilaron sin errores de sintaxis.
```

La ejecución del resto de la suite quedó bloqueada porque `.venv` referencia una instalación eliminada de Python 3.11 y el entorno de trabajo no permitió una segunda ejecución externa. Las pruebas están preparadas, pero no se marcan como aprobadas hasta ejecutar el comando anterior en un entorno válido.

## Pendientes reales

- Ejecutar toda la suite con un Python 3.11 funcional.
- Ejecutar un pago completo contra Webpay Integration y adjuntar el comprobante.
- Verificar correo SMTP y push OneSignal con credenciales reales.
- Probar el despliegue contra una base de pruebas de MongoDB Atlas.
- Definir el proceso comercial de reembolso para un pago autorizado que quede en revisión manual por falta de stock.
- Agregar transacciones MongoDB si el clúster de producción las admite; la compensación actual evita negativos, pero una transacción ofrece garantías superiores ante una caída del proceso.
- Corregir o recrear `.venv` antes de la entrega final.
