# Bot de Discord: patrones Adapter y Factory

Proyecto didáctico sobre patrones de diseño. Un bot de Discord recibe preguntas con
`/preguntar` y las delega a un **proveedor de respuestas**. El bot no sabe qué proveedor usa:
solo conoce la interfaz `ProveedorChat`.

> **Etapa 1 (`etapa-1-ficticio`)**: el bot funciona con un proveedor ficticio que regresa
> `Respuesta simulada para: <tu pregunta>`. No consume ninguna API de pago.
> La integración con OpenAI llega en la siguiente etapa.

## Estructura

```
bot.py                         Bot de Discord: recibe, valida, delega y publica
configuracion.py               Carga y valida variables de entorno
dominio/proveedor_chat.py      Interfaz ProveedorChat y errores del dominio
adaptadores/proveedor_ficticio.py
pruebas/                       Pruebas unitarias (sin red)
.env.example                   Plantilla de configuración (sin secretos)
```

## Requisitos

- Python 3.12 (compatible con Linux y macOS Apple Silicon).
- Una cuenta de Discord y un servidor donde puedas administrar.

## 1. Instalación

Todos los comandos se ejecutan **desde la carpeta del proyecto** (la que contiene `bot.py`).

### Linux

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### macOS (Apple Silicon, M1–M4)

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Si `python3` no existe o es anterior a 3.12, descarga el instalador **macOS 64-bit universal2**
de [python.org](https://www.python.org/downloads/macos/) (se ejecuta nativo en ARM64).
Después de instalarlo, abre la carpeta `Aplicaciones/Python 3.12` y ejecuta
**Install Certificates.command**; sin ese paso la conexión a Discord puede fallar con
`CERTIFICATE_VERIFY_FAILED`. Para confirmar la arquitectura:
`python3 -c "import platform; print(platform.machine())"` debe mostrar `arm64`.

## 2. Pruebas

```bash
python3 -m unittest -v
```

No se conectan a Discord ni a OpenAI.

## 3. Crear el bot en Discord

1. En <https://discord.com/developers/applications> pulsa **New Application**.
2. Menú **Bot** → **Reset Token** → copia el token. No actives ningún *Privileged Gateway Intent*.
3. Menú **OAuth2** → **OAuth2 URL Generator** (no uses la página *Installation*):
   - Scopes: `bot` y `applications.commands`.
   - Bot Permissions: `View Channels` y `Send Messages`.
   - Integration Type: **Guild Install**.
   - Abre la *Generated URL* en el navegador, elige **Add to server** y autoriza.
4. En la app de Discord: **Ajustes de usuario → Avanzado → Modo desarrollador**.
   - Clic derecho en el servidor → **Copiar ID del servidor**.
   - Clic derecho en el canal de texto → **Copiar ID del canal**.

## 4. Configuración

```bash
cp .env.example .env
```

Edita `.env` y llena `DISCORD_TOKEN`, `DISCORD_CHANNEL_ID` y `DISCORD_GUILD_ID`.

**El archivo `.env` contiene secretos**: está en `.gitignore`, nunca lo subas ni lo compartas.
Si un token se filtra, genera uno nuevo con **Reset Token**.

## 5. Ejecutar

```bash
python3 bot.py
```

El bot solo funciona mientras el programa corre (`Ctrl+C` para detenerlo). No ejecutes dos
copias con el mismo token al mismo tiempo.

En Discord:

| Prueba | Resultado esperado |
|---|---|
| `/preguntar mensaje: ¿Qué es un Adapter?` | `Respuesta simulada para: ¿Qué es un Adapter?` |
| Pregunta de 501 a 6000 caracteres | Mensaje privado: el máximo es 500 |
| Pregunta de más de 6000 caracteres | Discord la rechaza antes de llegar al bot |
