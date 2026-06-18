# Revisión del backlog Scrum

## Épicas propuestas

1. **Identidad y acceso:** registro, sesión, perfil, actividad y roles.
2. **Catálogo e inventario:** productos, categorías, imágenes y stock.
3. **Compra y fidelización:** carrito, despacho, descuentos y puntos.
4. **Pagos:** creación, confirmación, idempotencia y conciliación Webpay.
5. **Pedidos:** creación, seguimiento, historial y notificaciones.
6. **Operación administrativa:** usuarios, productos, stock, pedidos y exportación.
7. **Calidad y entrega:** pruebas, seguridad, observabilidad y documentación.

Esta separación evita una épica “Backend” demasiado amplia y organiza el trabajo por valor entregado al usuario.

## Historias y criterios de aceptación

### HU-01 — Crear cuenta

Como visitante, quiero registrarme para comprar en Ischuu.

- El nombre tiene al menos 2 caracteres.
- El correo tiene formato válido y no puede repetirse.
- La contraseña tiene al menos 6 caracteres y se guarda como hash.
- La cuenta nace activa, sin permisos administrativos y con cero puntos.

### HU-02 — Iniciar sesión

Como cliente, quiero iniciar sesión para acceder a mi perfil y compras.

- Credenciales inválidas responden 401 sin revelar qué campo falló.
- Una cuenta inactiva responde 403.
- El token permite acceder solo mientras la cuenta siga activa.

### HU-03 — Administrar usuarios

Como administrador, quiero activar, desactivar y asignar permisos.

- Solo `is_admin=true` concede acceso.
- Un usuario normal recibe 403 en todas las rutas administrativas.
- Un administrador no puede desactivarse ni quitarse su propio rol.

### HU-04 — Comprar productos disponibles

Como cliente, quiero agregar productos con stock a mi carrito.

- Un producto agotado no se puede agregar.
- Las cantidades repetidas se consolidan.
- El backend informa stock disponible y solicitado.
- Carrito vacío responde 400, no 500.

### HU-05 — Conocer el total

Como cliente, quiero conocer todos los cargos antes de pagar.

- Se muestran subtotal, envío, descuentos y total.
- El envío cuesta $3.000 y es gratis desde $25.000 de subtotal.
- El descuento por puntos no supera 20 % del subtotal.
- Las categorías preferidas reciben 5 % con tope de $5.000.

### HU-06 — Pagar con Webpay

Como cliente, quiero pagar de forma segura y recibir mi pedido solo si se autoriza.

- El pedido no existe antes de `AUTHORIZED`.
- Estado, monto y buy order deben coincidir.
- Un callback repetido no crea otro pedido.
- Un pago rechazado no altera stock ni puntos.
- Errores técnicos del proveedor responden 502 y quedan en logs.

### HU-07 — Mantener inventario consistente

Como operador, quiero que ninguna venta deje stock negativo.

- Se valida stock antes de iniciar el pago y al autorizarlo.
- El descuento usa una condición atómica `stock >= cantidad`.
- Una reserva parcial fallida se revierte.
- El mismo pago descuenta una sola vez.

### HU-08 — Seguir pedidos

Como cliente, quiero ver el avance de mis pedidos.

- Solo puedo consultar pedidos propios.
- El pedido nace `Pagado`.
- Los estados válidos son Pagado, Preparando, En despacho, Entregado y Cancelado.
- Cada cambio guarda actor y fecha y genera notificación cuando está configurada.

## Flujo Scrum recomendado

1. Refinamiento semanal de historias y criterios.
2. Selección de historias pequeñas para un sprint de una o dos semanas.
3. Rama por historia o corrección.
4. Implementación con prueba automatizada en el mismo cambio.
5. Revisión de código y ejecución de la suite.
6. Demostración en Webpay Integration y MongoDB de pruebas.
7. Retrospectiva con errores, deuda y acciones concretas.

## Definición de terminado

Una historia está terminada únicamente cuando:

- cumple todos sus criterios de aceptación;
- tiene pruebas automatizadas y prueba funcional cuando aplica;
- no contiene credenciales ni datos personales en el repositorio;
- mantiene documentación de API y variables de entorno;
- fue verificada con usuario normal y administrador;
- tiene evidencia del resultado y de los errores esperados;
- está desplegada en el ambiente correspondiente o declara claramente el bloqueo.
