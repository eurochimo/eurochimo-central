# Central Eurochimo — Nivel 2

Publica en Facebook e Instagram desde la nube a las 14:00 y 18:00 (hora de Chile). No necesita el PC encendido y no tiene el límite de 29 días del programador de Meta.

## Qué hay aquí
- `publicar.py` revisa cada 15 min la cola y publica en FB + IG lo que venció. Para probar: `python publicar.py --simular`.
- `preparar_contenido.py` copia las piezas desde PUBLICACIONES y arma `contenido/cola.json`.
- `.github/workflows/publicar.yml` es el reloj en GitHub Actions (gratis).
- `contenido/` guarda las piezas y la cola; `publicados.json` es el registro, que evita duplicados.

## Pasos que debe hacer el dueño (una sola vez)
Las cuentas y las claves son tuyas: Claude no las crea ni las escribe.

1. **GitHub.** Crea una cuenta gratis en github.com y luego un repositorio **público** llamado `eurochimo-central`. Solo contendrá publicidad, nunca claves.
2. **App de Meta.** Entra a developers.facebook.com → Mis apps → Crear app → tipo **Empresa**, vinculada al portafolio "EuropaChina MotoresLtda".
   - Agrega el producto **API de Instagram (con inicio de sesión de Facebook)**.
   - En el **Explorador de la API Graph**, genera un token de usuario con estos permisos:
     - `pages_show_list`
     - `pages_read_engagement`
     - `pages_manage_posts`
     - `instagram_basic`
     - `instagram_content_publish`
     - `business_management`
   - Cambia ese token por uno de **página de larga duración**, que no vence.
   - Anota tres datos: el ID de la página Eurochimo (1734817460097957), el ID de la cuenta de Instagram profesional y el token de página.
3. **Secretos en GitHub.** En el repositorio, ve a Settings → Secrets and variables → Actions → New secret y crea:
   - `META_PAGE_ID`
   - `META_PAGE_TOKEN`
   - `IG_USER_ID`

   Pegas tú los valores; nunca van en un archivo ni en un chat.
4. **Subir el código.** Avísale a Claude: sube esta carpeta al repositorio con git (tú inicias la sesión de GitHub) y hace una prueba con "Run workflow".

## Al activar la central
- Se desactiva la tarea local "eurochimo-programar-black-week" (2/11) para no duplicar publicaciones. Las ya programadas en el Planificador de Meta se dejan como están.
- Contenido nuevo: Claude genera las piezas, corre `preparar_contenido.py` y sube los cambios.

## Siguientes módulos del Nivel 2
- **B. Bot de mensajes (Cloudflare Workers, gratis).**
  - Responde Messenger e Instagram revisando el stock real en WooCommerce.
  - Pregunta la comuna para aplicar la regla de agotados: Santiago "agotado hasta nuevo aviso"; regiones por encargo con abono del 10%.
  - Detecta proveedores y spam.
  - Requiere que Meta apruebe el permiso `pages_messaging` (revisión de la app, unos días).
- **C. Mercado Libre.** Crear app en developers.mercadolibre.cl para responder preguntas, sincronizar stock y pausar publicaciones sin stock.
- **D. Reporte diario 8:00 en la nube.** Ventas de la web y ML más pedidos por despachar, a cristianhpantoja@gmail.com.
