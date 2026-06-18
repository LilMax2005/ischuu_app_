# Cambios aplicados para versión móvil

- `mobile_main.py` usa la API pública de Render mediante `app/frontend/config.py`.
- Carrito y pago pendiente usan `ft.SharedPreferences` en lugar de archivos JSON locales.
- La dirección de despacho se mantiene asociada al usuario en el backend.
- Se agregó verificación del pago pendiente al reanudar la aplicación.
- Todas las solicitudes `httpx.AsyncClient` usan el timeout configurado.
- Se redujo el padding general de la aplicación para pantallas pequeñas.
- Se eliminaron anchos fijos principales del formulario administrador.
- Se conservó el Centro de ayuda móvil y la navegación inferior protegida contra índices fuera de rango.
- Se eliminaron del paquete `.env`, entornos virtuales, builds, cachés y archivos locales sensibles.

## Ejecutar en modo móvil

```powershell
python mobile_main.py
```

## Probar en Android

```powershell
flet run mobile_main.py --android
```

## Generar APK

```powershell
copy main.py main_desktop_backup.py
copy mobile_main.py main.py
flet build apk
copy main_desktop_backup.py main.py
```
