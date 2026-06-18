# Ischuu App

Aplicación móvil de comercio electrónico para **Ischuu**, una tienda de blind boxes, figuras coleccionables y productos de cultura pop. El cliente se distribuye únicamente para Android/iOS; FastAPI funciona como API remota y no existe una aplicación web.

[Backend desplegado](https://ischuu-app.onrender.com) · [Documentación de la API](https://ischuu-app.onrender.com/docs)

[Informe de implementación](docs/IMPLEMENTACION_Y_PRUEBAS.md) · [Referencia de API](docs/API.md) · [Backlog y criterios Scrum](docs/BACKLOG_SCRUM.md)

> El proyecto utiliza Webpay en ambiente de integración. No debe tratarse como una tienda en producción sin revisar primero la configuración de seguridad indicada al final de este documento.

## Funcionalidades

| Clientes | Administración |
| --- | --- |
| Registro, inicio de sesión y recuperación de contraseña | Resumen de ventas, pedidos, usuarios y stock |
| Catálogo con búsqueda y filtro por categoría | Creación, edición y eliminación de productos |
| Carrito con cálculo de envío y descuentos | Ajuste de inventario y permisos de usuarios |
| Dirección de despacho persistente | Actualización del seguimiento de pedidos |
| Pago con Webpay Plus | Exportación de pedidos a Excel |
| Puntos y descuentos por preferencias | Configuración de enlaces sociales |
| Historial y seguimiento de pedidos | Avisos por correo y notificaciones push |

## Arquitectura

```mermaid
flowchart LR
    F["App móvil Flet<br/>Android / iOS"] -->|HTTPS / JSON| A["API FastAPI<br/>Render"]
    A --> M[(MongoDB Atlas)]
    A --> W["Webpay Plus"]
    A --> S["SMTP"]
    A --> O["OneSignal"]
```

### Tecnologías principales

- **Aplicación móvil:** Python y Flet para Android/iOS.
- **API:** FastAPI y Uvicorn.
- **Persistencia:** MongoDB, Motor y PyMongo.
- **Autenticación:** JWT y Argon2.
- **Pagos:** Transbank SDK para Webpay Plus.
- **Integraciones:** SMTP para correos y OneSignal para notificaciones push.
- **Distribución:** APK/AAB para Android e IPA para iOS mediante Flet Build.

### Organización MVC

El frontend conserva una separación MVC explícita y el backend aplica MVC adaptado a una API:

| Capa | Ubicación | Responsabilidad |
| --- | --- | --- |
| Modelo | `app/backend/models.py`, `schemas.py` y `frontend/models/` | Documentos, estados y validación de datos |
| Vista | `frontend/views/` y respuestas JSON | Presentación Flet y representación HTTP |
| Controlador | `frontend/controllers/` y `backend/routers/` | Eventos de interfaz y endpoints |
| Servicios | `backend/services/` y `frontend/services/` | Reglas de negocio e integraciones externas |

Las reglas de stock, checkout y estados no viven en las vistas ni se duplican entre controladores.

## Puesta en marcha

### Requisitos

- Python 3.11.
- Una instancia de MongoDB Atlas accesible.
- PowerShell en Windows para los comandos de esta guía.
- Git, solo si vas a clonar o versionar el proyecto.

### 1. Preparar el entorno

Desde la raíz del repositorio:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configurar las variables de entorno

Copia `.env.example` como `.env` en la raíz. El repositorio ignora `.env` para evitar publicar credenciales.

```env
APP_NAME=Ischuu
SECRET_KEY=reemplazar-por-una-clave-larga-y-aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_EMAIL=
ADMIN_PASSWORD=

MONGODB_URL=mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=ischuu
# MONGODB_TLS=false  # Solo para MongoDB local sin TLS

# URL pública del backend; también se usa para el retorno de Webpay.
API_BASE_URL=http://127.0.0.1:8000
FRONTEND_API_BASE_URL=http://127.0.0.1:8000
CORS_ORIGINS=http://127.0.0.1:8000

TBK_ENV=integration
TBK_COMMERCE_CODE=
TBK_API_KEY=

# Opcionales: correo
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=

# Opcionales: notificaciones móviles
ONESIGNAL_APP_ID=
ONESIGNAL_REST_API_KEY=
```

`MONGODB_URL` es la única variable sin valor predeterminado y debe existir para que el backend pueda iniciar. En modo `integration`, el SDK de Transbank utiliza sus credenciales de prueba; las credenciales propias se requieren al cambiar `TBK_ENV` a `production`.

### 3. Ejecutar la aplicación

#### Probar en Android conectado al equipo

```powershell
flet run --android main.py
```

`main.py` es la única entrada del cliente móvil. Lee `FRONTEND_API_BASE_URL`; si no existe, usa `API_BASE_URL` y finalmente el backend desplegado como valor predeterminado.

#### Desarrollo local del backend

Inicia la API en una terminal:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Comprueba que responde en:

- API: <http://127.0.0.1:8000>
- Salud: <http://127.0.0.1:8000/health>
- Swagger UI: <http://127.0.0.1:8000/docs>

Para conectar Flet a esta API local, configura:

```env
FRONTEND_API_BASE_URL=http://127.0.0.1:8000
```

Después abre otra terminal y ejecuta la app en Android:

```powershell
.\.venv\Scripts\Activate.ps1
flet run --android main.py
```

> `API_BASE_URL` configura las URLs generadas por el backend, como el retorno de Webpay. `FRONTEND_API_BASE_URL` permite que el cliente Flet apunte a otro entorno.

## Reglas de negocio vigentes

Estas reglas proceden del módulo utilizado por pagos, `app/backend/services/pricing.py`:

| Regla | Valor actual |
| --- | ---: |
| Envío | $3.000 CLP |
| Envío gratis | Desde $25.000 CLP de subtotal |
| Acumulación | 1 punto por cada $500 CLP pagados en productos |
| Valor de canje | 1 punto = $25 CLP |
| Canje mínimo | 10 puntos |
| Tope del descuento por puntos | 20 % del subtotal |
| Descuento por categorías preferidas | 5 %, con tope de $5.000 CLP |

El envío no genera puntos. El pedido, el descuento de stock y la actualización del saldo de puntos ocurren solamente después de que Webpay devuelve una transacción autorizada.

El seguimiento administrativo utiliza estos estados:

1. `Pagado`
2. `Preparando`
3. `En despacho`
4. `Entregado`
5. `Cancelado`

## API

La API usa el prefijo `/api/v1` y agrupa sus endpoints en:

- `/auth`: registro, acceso, perfil, despacho y preferencias de notificación.
- `/password`: recuperación y cambio de contraseña.
- `/products`: catálogo público.
- `/payments`: cotización, inicio, retorno y consulta de pagos Webpay.
- `/orders`: pedidos del usuario.
- `/admin`: usuarios, productos, stock, pedidos, exportación y ajustes.
- `/notifications`: configuración pública del proveedor push.

La especificación OpenAPI completa está disponible en `/docs` cuando el backend está en ejecución.

## Notificaciones y correo

### OneSignal

Para habilitar notificaciones móviles de cambios de pedido:

1. Crea una aplicación en OneSignal.
2. Configura FCM para Android y APNs si distribuirás la app en iOS.
3. Define `ONESIGNAL_APP_ID` y `ONESIGNAL_REST_API_KEY` únicamente en el entorno del backend.
4. Comprueba en OneSignal que Google Android (FCM) esté configurado para la misma aplicación.
5. Instala `flet-onesignal`, recompila e instala nuevamente la APK.

La API entrega al cliente solo el App ID público mediante `/api/v1/notifications/config`. La REST API key permanece en el servidor. Cada usuario puede activar los avisos y ejecutar **Perfil → Probar aviso** para verificar permiso, vínculo y entrega.

### SMTP

Si `SMTP_HOST`, `SMTP_USER` y `SMTP_PASSWORD` están configurados, el backend envía un correo cuando cambia el estado de un pedido. Para Gmail debes utilizar una contraseña de aplicación. Si SMTP no está configurado, el contenido del correo se registra en la salida del backend y la operación continúa.

## Compilación y distribución

### Probar en un dispositivo Android

```powershell
flet run --android main.py
```

Este modo es apropiado para desarrollo y mantiene una sesión conectada al equipo.

### Generar una APK

```powershell
python -m pip install -r requirements.txt
flet build apk
```

`pyproject.toml` incluye `flet-onesignal` y el permiso Android `POST_NOTIFICATIONS`. Una APK compilada antes de estos cambios no puede recibir push y debe desinstalarse antes de instalar la nueva.

En Windows, Flet necesita soporte de enlaces simbólicos para plugins. Si aparece `Building with plugins requires symlink support`, activa **Modo de desarrollador** en Configuración de Windows y vuelve a compilar.

Para localizar el artefacto generado:

```powershell
Get-ChildItem -Recurse -Filter *.apk
```

Antes de compilar, confirma que `FRONTEND_API_BASE_URL` apunta al backend que utilizará la APK.

## Despliegue del backend en Render

Configuración base de la API remota. Este servicio HTTP es consumido por la app móvil y no contiene una interfaz web:

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.backend.main:app --host 0.0.0.0 --port $PORT
```

Configura en Render las mismas variables del `.env` y usa la URL pública en `API_BASE_URL`. Para el despliegue actual:

```env
API_BASE_URL=https://ischuu-app.onrender.com
```

El retorno esperado de Webpay será:

```text
https://ischuu-app.onrender.com/api/v1/payments/webpay/return
```

`runtime.txt` fija Python 3.11.9 para este despliegue.

## Estructura del repositorio

```text
ischuu_app_/
├── app/
│   ├── backend/
│   │   ├── core/          # Configuración y seguridad
│   │   ├── routers/       # Endpoints FastAPI
│   │   ├── services/      # Pagos, precios, correo, push y exportación
│   │   ├── db.py          # Cliente MongoDB
│   │   └── main.py        # Aplicación FastAPI
│   └── frontend/
│       ├── controllers/   # Estado y coordinación de la interfaz
│       ├── models/        # Entidades del cliente
│       ├── services/      # Cliente HTTP
│       └── views/         # Tienda, carrito, pedidos, perfil y admin
├── main.py                # Única entrada de la app móvil
├── pyproject.toml         # Build Android/iOS y dependencias móviles
├── docker-compose.yml     # MongoDB local de apoyo
├── requirements.txt
└── runtime.txt
```

La carpeta `build/` contiene archivos generados por Flet y no es código fuente principal.

## Solución de problemas

### El backend no inicia y pide `MONGODB_URL`

Comprueba que `.env` esté en la raíz y que la URL de Atlas sea válida. Si Atlas restringe las conexiones por IP, autoriza la dirección desde la que se ejecuta el backend.

### Webpay intenta volver a `127.0.0.1`

La variable `API_BASE_URL` del backend está apuntando al entorno local. En Render debe contener la URL HTTPS pública. Reinicia o vuelve a desplegar el servicio después de cambiarla.

### La aplicación móvil muestra 404 o no conecta

Revisa `FRONTEND_API_BASE_URL` en el entorno de compilación. Debe ser el origen del backend, sin `/docs` ni `/api/v1`. Desinstala la APK anterior antes de probar una compilación nueva si el dispositivo conserva una versión antigua.

### No llegan correos

Verifica las variables SMTP y revisa la salida del backend. Gmail puede rechazar contraseñas normales o alcanzar límites diarios; para producción conviene utilizar un proveedor de correo transaccional.

### No llegan notificaciones push

Instala la APK nueva, inicia sesión, activa los avisos y pulsa **Perfil → Probar aviso**. Si OneSignal informa que no encontró un teléfono vinculado, revisa FCM, el permiso Android y que el usuario haya iniciado sesión después de instalar la APK corregida.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

La suite cubre precios, puntos, permisos, usuarios inactivos, carrito vacío, stock insuficiente, rollback, pagos rechazados, monto alterado e idempotencia. Las pruebas reales de Webpay, SMTP y OneSignal requieren sus respectivos ambientes y credenciales.

## Notas de seguridad y desarrollo

- Cambia `SECRET_KEY` en cualquier entorno compartido o de producción.
- No hay credenciales administrativas predeterminadas. Define `ADMIN_EMAIL` y `ADMIN_PASSWORD` para crear el primer administrador en una base vacía y retira `ADMIN_PASSWORD` del entorno después del primer inicio.
- Configura `CORS_ORIGINS` con los orígenes permitidos antes de producción; `*` es solo el valor predeterminado de desarrollo.
- MongoDB Atlas activa TLS automáticamente. Para el servicio local de `docker-compose.yml`, define `MONGODB_URL=mongodb://127.0.0.1:27017` y `MONGODB_TLS=false`.
- Las reglas de precios viven únicamente en `app/backend/services/pricing.py`.
- Ejecuta `python -m unittest discover -s tests -v` antes de una entrega y completa las pruebas externas de Webpay, SMTP y OneSignal.

## Autores

- **Matías Alarcón** — jefe de proyecto.
- **Máximo Lorca** — desarrollador.

## Licencia

Proyecto académico desarrollado con fines educativos. El repositorio no declara por ahora una licencia de código abierto.
