# Ischuu App

Aplicación de tienda online para **Ischuu**, enfocada en la venta de productos tipo **Blind Box**, figuras coleccionables, anime, videojuegos y cultura pop.

El proyecto permite gestionar productos, usuarios, carrito de compras, pagos en línea, dirección de despacho, sistema de puntos, descuentos, seguimiento de pedidos y administración interna.

---

## 1. Descripción del proyecto

**Ischuu App** es una solución desarrollada para digitalizar y fortalecer el proceso de venta de la tienda Ischuu, la cual inicialmente operaba principalmente mediante redes sociales como Instagram y TikTok.

La aplicación busca centralizar el flujo de compra en una plataforma propia, permitiendo que los clientes puedan:

* Ver productos disponibles.
* Agregar productos al carrito.
* Guardar dirección de despacho.
* Aplicar puntos y descuentos.
* Pagar mediante Webpay.
* Revisar el seguimiento de sus pedidos.

Además, el sistema incorpora una vista de administrador para gestionar productos, stock, usuarios y estados de pedidos.

---

## 2. Objetivo del proyecto

El objetivo principal es desarrollar una aplicación escalable y funcional que permita a Ischuu mejorar su proceso de venta online, fidelizar clientes y entregar una experiencia de compra más confiable y ordenada.

### Objetivos específicos

* Implementar una tienda online con catálogo de productos.
* Permitir registro e inicio de sesión de usuarios.
* Gestionar carrito de compras.
* Integrar pagos con Webpay Plus.
* Implementar sistema de puntos y descuentos.
* Permitir guardar dirección de despacho por usuario.
* Crear pedidos automáticamente después de un pago autorizado.
* Permitir seguimiento de pedidos.
* Crear una vista de administrador.
* Desplegar el backend en la nube.
* Permitir pruebas desde dispositivo móvil.

---

## 3. Tecnologías utilizadas

### Frontend

* **Python**
* **Flet**

Flet fue utilizado para construir la interfaz gráfica de la aplicación, permitiendo ejecutar la app en escritorio, web y dispositivos móviles.

### Backend

* **Python**
* **FastAPI**
* **Uvicorn**

FastAPI fue utilizado para crear una API REST encargada de gestionar productos, usuarios, autenticación, pagos, pedidos, dirección de despacho y administración.

### Base de datos

* **MongoDB Atlas**
* **Motor**
* **PyMongo**

MongoDB Atlas fue utilizado como base de datos en la nube, permitiendo persistencia de productos, usuarios, pedidos, pagos, direcciones, puntos y preferencias.

### Pagos

* **Webpay Plus**
* **Transbank SDK**

Se utiliza Webpay Plus en ambiente de integración para procesar pagos online en pesos chilenos.

### Despliegue

* **Render**

Render fue utilizado para desplegar el backend FastAPI y exponerlo mediante una URL pública HTTPS.

### Correos

* **SMTP Gmail**

Se utiliza SMTP para enviar correos de actualización de pedidos. Para producción se recomienda usar un proveedor transaccional como Brevo, SendGrid, Mailgun o Amazon SES.

### Empaquetado

* **Flet build APK**
* **PyInstaller**

Flet se utiliza para generar APK Android. PyInstaller puede utilizarse para empaquetar la app de escritorio en Windows.

---

## 4. Arquitectura del sistema

La aplicación utiliza una arquitectura cliente-servidor.

```text
Cliente Flet
    ↓
Backend FastAPI en Render
    ↓
MongoDB Atlas
    ↓
Servicios externos: Webpay, SMTP
```

### Componentes principales

* **Frontend Flet:** interfaz para clientes y administradores.
* **Backend FastAPI:** API REST para lógica de negocio.
* **MongoDB Atlas:** almacenamiento persistente.
* **Webpay:** procesamiento de pagos.
* **Render:** despliegue del backend.
* **SMTP:** envío de notificaciones por correo.

---

## 5. Funcionalidades principales

### Usuario cliente

* Registro de usuario.
* Inicio de sesión.
* Visualización de catálogo.
* Búsqueda y filtrado de productos.
* Agregar productos al carrito.
* Guardar dirección de despacho.
* Modificar dirección de despacho.
* Usar puntos disponibles.
* Pagar con Webpay.
* Ver pedidos pagados.
* Revisar seguimiento del pedido.
* Consultar puntos ganados.

### Usuario administrador

* Acceso a panel administrador.
* Visualización de estadísticas.
* Gestión de productos.
* Gestión de stock.
* Gestión de usuarios.
* Revisión de pedidos.
* Actualización de estados de pedido.
* Envío de correos al cambiar estado.
* Exportación de pedidos.
* Configuración de redes sociales.

### Estados de pedido

Los pedidos pueden tener los siguientes estados:

```text
Compra realizada
Artículo empaquetado
Artículo enviado
Artículo entregado
```

---

## 6. Sistema de puntos

El sistema de puntos fue implementado para fidelización de clientes.

La regla utilizada es:

```text
Cada $500 de compra = 1 punto
1 punto = $50 de descuento
```

Ejemplo:

```text
Compra: $12.000
Puntos ganados: 24
Valor equivalente futuro: $1.200 de descuento
```

Los puntos pueden utilizarse en futuras compras mediante el switch de uso de puntos dentro del carrito.

---

## 7. Dirección de despacho

Cada usuario puede registrar su propia dirección de despacho.

La dirección incluye:

* Nombre del destinatario.
* Teléfono.
* Región.
* Comuna.
* Calle.
* Número.
* Referencias o indicaciones.

La dirección se guarda en el usuario y, al momento de realizar una compra, se copia al pedido. Esto permite que los pedidos antiguos mantengan la dirección utilizada en esa compra, aunque el usuario modifique su dirección posteriormente.

---

## 8. Flujo de compra

El flujo general de compra es el siguiente:

```text
1. Usuario inicia sesión.
2. Usuario revisa catálogo.
3. Usuario agrega productos al carrito.
4. Usuario ingresa o confirma dirección de despacho.
5. Backend calcula subtotal, envío, descuentos y total.
6. Usuario paga con Webpay.
7. Webpay retorna al backend.
8. Si el pago es autorizado, se crea el pedido.
9. Se descuenta stock.
10. Se asignan puntos.
11. El pedido aparece en seguimiento.
12. El administrador puede actualizar el estado.
13. El usuario recibe notificación por correo.
```

El pedido solo se crea cuando el pago es autorizado por Webpay.

---

## 9. Estructura del proyecto

Estructura general del sistema:

```text
ischuu_app_
│
├── app/
│   ├── backend/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   │
│   │   ├── routers/
│   │   │   ├── admin.py
│   │   │   ├── auth.py
│   │   │   ├── orders.py
│   │   │   ├── payments.py
│   │   │   ├── products.py
│   │   │   └── password.py
│   │   │
│   │   ├── services/
│   │   │   ├── catalog.py
│   │   │   ├── email.py
│   │   │   ├── pricing.py
│   │   │   ├── shipping.py
│   │   │   └── transbank.py
│   │   │
│   │   ├── db.py
│   │   └── main.py
│   │
│   └── frontend/
│       ├── controllers/
│       │   └── app_controller.py
│       │
│       ├── models/
│       │   ├── entities.py
│       │   └── state.py
│       │
│       ├── services/
│       │   └── api_client.py
│       │
│       └── views/
│           ├── admin.py
│           ├── auth.py
│           ├── cart.py
│           ├── components.py
│           ├── orders.py
│           ├── products.py
│           ├── profile.py
│           └── theme.py
│
├── main.py
├── mobile_main.py
├── requirements.txt
├── runtime.txt
├── README.md
└── .env
```

---

## 10. Variables de entorno

El proyecto utiliza variables de entorno para separar configuración sensible del código.

Crear un archivo `.env` en la raíz del proyecto.

Ejemplo:

```env
APP_NAME=Ischuu
SECRET_KEY=CAMBIAR_SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

MONGODB_URL=mongodb+srv://USUARIO:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=ischuu

API_BASE_URL=http://127.0.0.1:8000

TBK_ENV=integration
TBK_COMMERCE_CODE=597055555532
TBK_API_KEY=API_KEY_DE_INTEGRACION

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo@gmail.com
SMTP_PASSWORD=clave_de_aplicacion
SMTP_FROM=correo@gmail.com
```

Para Render, la variable `API_BASE_URL` debe ser:

```env
API_BASE_URL=https://ischuu-app.onrender.com
```

Para desarrollo local puede ser:

```env
API_BASE_URL=http://127.0.0.1:8000
```

---

## 11. Instalación local

### Requisitos previos

* Python 3.11 recomendado.
* Git.
* Cuenta de MongoDB Atlas.
* Entorno virtual `.venv`.

### Crear entorno virtual

Desde la raíz del proyecto:

```powershell
py -3.11 -m venv .venv
```

Activar entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Actualizar pip:

```powershell
python -m pip install --upgrade pip
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Ejecutar aplicación local:

```powershell
python main.py
```

---

## 12. Ejecución local

El archivo `main.py` levanta el backend local y la aplicación Flet de escritorio.

```powershell
python main.py
```

Este modo utiliza normalmente:

```text
http://127.0.0.1:8000
```

La documentación local del backend se puede revisar en:

```text
http://127.0.0.1:8000/docs
```

---

## 13. Ejecución móvil con Render

Para ejecutar la aplicación en celular usando el backend desplegado en Render, utilizar `mobile_main.py`.

Contenido recomendado de `mobile_main.py`:

```python
from __future__ import annotations

import flet as ft

from app.frontend.controllers.app_controller import AppController


API_BASE_URL = "https://ischuu-app.onrender.com"


def main(page: ft.Page) -> None:
    AppController(
        page,
        api_base_url=API_BASE_URL,
    )


if __name__ == "__main__":
    ft.run(main)
```

Ejecutar en Android con Flet:

```powershell
flet run --android mobile_main.py
```

Ejecutar en iOS con Flet:

```powershell
flet run --ios mobile_main.py
```

Este modo depende del PC mientras se realizan pruebas.

---

## 14. Generar APK Android

Para que la app funcione en el celular sin depender del PC, se debe generar una APK.

### Paso 1: respaldar main.py

```powershell
copy main.py main_desktop_backup.py
```

### Paso 2: usar mobile_main.py como main.py temporal

```powershell
copy mobile_main.py main.py
```

### Paso 3: limpiar builds anteriores

```powershell
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
```

### Paso 4: generar APK

```powershell
flet build apk
```

### Paso 5: restaurar main.py original

```powershell
copy main_desktop_backup.py main.py
```

### Paso 6: buscar APK generada

```powershell
Get-ChildItem -Recurse -Filter *.apk
```

La APK puede quedar en rutas como:

```text
build\apk\
```

o:

```text
build\flutter\build\app\outputs\flutter-apk\
```

Luego se copia el archivo APK al celular y se instala manualmente.

---

## 15. Despliegue en Render

El backend se despliega en Render como servicio web.

### Configuración recomendada

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.backend.main:app --host 0.0.0.0 --port $PORT
```

### Archivo runtime.txt

Para fijar la versión de Python en Render:

```txt
python-3.11.9
```

### Variables importantes en Render

```env
API_BASE_URL=https://ischuu-app.onrender.com
MONGODB_URL=URL_DE_MONGODB_ATLAS
MONGODB_DATABASE=ischuu
SECRET_KEY=CLAVE_SECRETA
TBK_ENV=integration
TBK_COMMERCE_CODE=CODIGO_COMERCIO
TBK_API_KEY=API_KEY_TRANSBANK
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=CORREO
SMTP_PASSWORD=CLAVE_APLICACION
SMTP_FROM=CORREO
```

Después de modificar variables de entorno en Render, se recomienda ejecutar:

```text
Manual Deploy → Clear build cache & deploy
```

---

## 16. Webpay

La integración con Webpay Plus funciona mediante el backend.

El backend genera una transacción con:

* Monto total.
* Orden de compra.
* Token Webpay.
* URL de retorno.

La URL de retorno debe apuntar al backend público de Render:

```text
https://ischuu-app.onrender.com/api/v1/payments/webpay/return
```

No debe apuntar a:

```text
http://127.0.0.1:8000
```

Si Webpay retorna a `127.0.0.1`, revisar:

* Variable `API_BASE_URL` en Render.
* Archivo `config.py`.
* Archivo `payments.py`.
* Transacciones pendientes antiguas.
* APK compilada con URL antigua.

---

## 17. Correos SMTP

El sistema puede enviar correos cuando el administrador cambia el estado de un pedido.

El correo incluye:

* Número de seguimiento.
* Estado anterior.
* Estado nuevo.
* Fecha y hora de actualización.
* Dirección de despacho.
* Datos del pedido.

Para Gmail se necesita una clave de aplicación, no la contraseña normal de la cuenta.

Ejemplo de configuración:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=correo@gmail.com
SMTP_PASSWORD=clave_de_aplicacion
SMTP_FROM=correo@gmail.com
```

Si aparece el error:

```text
Daily user sending limit exceeded
```

significa que Gmail alcanzó el límite diario de envío. Para producción se recomienda usar Brevo, SendGrid, Mailgun o Amazon SES.

---

## 18. Comandos útiles

### Ejecutar local

```powershell
python main.py
```

### Ejecutar móvil con Render

```powershell
flet run --android mobile_main.py
```

### Generar APK

```powershell
flet build apk
```

### Buscar APK

```powershell
Get-ChildItem -Recurse -Filter *.apk
```

### Instalar dependencias

```powershell
pip install -r requirements.txt
```

### Subir cambios a GitHub

```powershell
git add .
git commit -m "Update Ischuu App"
git push
```

### Ver rutas en Render

```text
https://ischuu-app.onrender.com/docs
```

### Ver productos desde navegador

```text
https://ischuu-app.onrender.com/api/v1/products
```

---

## 19. Solución de problemas frecuentes

### Error: 127.0.0.1 rechazó la conexión

Causa probable:

Webpay o la app móvil están usando una URL local.

Solución:

Configurar:

```env
API_BASE_URL=https://ischuu-app.onrender.com
```

en Render y recompilar la APK usando `mobile_main.py`.

---

### Error: HTTP Error 404 Not Found en celular

Causa probable:

La app móvil está usando mal la URL base.

La URL correcta debe ser:

```text
https://ischuu-app.onrender.com
```

No usar:

```text
https://ischuu-app.onrender.com/docs
https://ischuu-app.onrender.com/api/v1
http://127.0.0.1:8000
```

---

### Error: Gmail Daily user sending limit exceeded

Causa:

Gmail alcanzó el límite diario de envío.

Solución:

Esperar el reinicio del límite o usar un proveedor transaccional.

---

### Error: MongoDB SSL handshake failed en Render

Posibles causas:

* Versión de Python no compatible.
* Falta `runtime.txt`.
* URL de MongoDB mal configurada.
* IP no permitida en MongoDB Atlas.

Solución:

Usar `runtime.txt`:

```txt
python-3.11.9
```

Permitir acceso en MongoDB Atlas:

```text
0.0.0.0/0
```

Verificar `MONGODB_URL` en Render.

---

### Error: App móvil sigue usando versión antigua

Solución:

* Desinstalar APK anterior del celular.
* Limpiar carpeta `build`.
* Compilar nuevamente usando `mobile_main.py`.
* Instalar la nueva APK.

---

## 20. Plan de pruebas

### Pruebas de usuario

* Registrar usuario.
* Iniciar sesión.
* Modificar dirección de despacho.
* Agregar productos al carrito.
* Usar puntos.
* Pagar con Webpay.
* Revisar seguimiento.

### Pruebas de administrador

* Iniciar sesión como administrador.
* Ver productos.
* Ver usuarios.
* Ver pedidos.
* Actualizar estado de pedido.
* Confirmar envío de correo.
* Revisar historial de cambios.

### Pruebas de pago

* Verificar monto enviado a Webpay.
* Confirmar pedido solo si el pago es autorizado.
* Validar descuento de stock.
* Validar asignación de puntos.
* Validar que el carrito se limpie después del pago.

### Pruebas móviles

* Ejecutar con `flet run --android`.
* Instalar APK.
* Probar login.
* Probar carrito.
* Probar Webpay.
* Probar seguimiento.

---

## 21. Estado actual del proyecto

Actualmente el proyecto cuenta con:

* Backend funcional en FastAPI.
* Despliegue en Render.
* Base de datos MongoDB Atlas.
* Catálogo de productos.
* Carrito de compras.
* Login y registro.
* Sistema de puntos.
* Descuentos por preferencias.
* Dirección de despacho por usuario.
* Webpay Plus en ambiente de integración.
* Creación automática de pedidos.
* Seguimiento de pedidos.
* Panel administrador.
* Correos por cambio de estado.
* Pruebas móviles con Flet.
* Proceso de generación APK.

---

## 22. Próximas mejoras

* Mejorar diseño visual móvil.
* Optimizar panel administrador.
* Implementar proveedor profesional de correos.
* Mejorar exportación de pedidos.
* Agregar recuperación de contraseña.
* Completar integración con Instagram y TikTok.
* Publicar APK estable.
* Agregar logs y monitoreo.
* Agregar pruebas automatizadas.
* Mejorar seguridad de producción.
* Configurar dominio propio.

---

## 23. Autores

Proyecto desarrollado por:

* **Matías Alarcón** – Jefe de proyecto.
* **Máximo Lorca** – Desarrollador.

---

## 24. Licencia

Proyecto académico desarrollado para fines educativos.

---

## 25. URL del backend

Backend desplegado en Render:

```text
https://ischuu-app.onrender.com
```

Documentación Swagger:

```text
https://ischuu-app.onrender.com/docs
```
