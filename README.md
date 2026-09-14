# Bot de Discord: patrones Adapter y Factory

Proyecto didáctico sobre patrones de diseño. Un bot de Discord recibe preguntas con
`/preguntar` y las delega a un **proveedor de respuestas**: uno ficticio (gratis, para probar)
o uno real con la API de OpenAI. Se cambia de proveedor **modificando una sola variable de
entorno**, sin tocar el código.

El objetivo no es un bot complejo, sino mostrar con claridad:

- el patrón **Adapter** (`AdaptadorOpenAI`);
- el patrón **Factory** (`crear_proveedor`);
- la separación de responsabilidades;
- el uso de variables de entorno y el manejo seguro de secretos.

## Etapas del repositorio

| Etiqueta | Contenido |
|---|---|
| `etapa-1-ficticio` | Bot funcionando con el proveedor ficticio |
| `etapa-2-openai` | Adaptador de OpenAI, fábrica, límites por canal y usuario, pruebas |

Para ver una etapa: `git checkout etapa-1-ficticio` (regresar con `git checkout main`),
o descarga el `.zip` desde la sección **Tags** de GitHub.
Para ver qué cambió entre etapas: `git diff etapa-1-ficticio etapa-2-openai`.

## Arquitectura

```
Discord ──> BotDiscord ──> ProveedorChat (interfaz)
                                 ▲
                   ┌─────────────┴─────────────┐
           ProveedorFicticio            AdaptadorOpenAI ──> SDK de OpenAI

bot.py: main() ──> crear_proveedor(configuracion) ──> elige uno según PROVEEDOR_CHAT
```

| Archivo | Responsabilidad |
|---|---|
| `bot.py` | Recibe `/preguntar`, valida canal, longitud y cupo, delega y publica la respuesta |
| `configuracion.py` | Carga y valida las variables de entorno |
| `dominio/proveedor_chat.py` | Interfaz `ProveedorChat` y errores propios de la aplicación |
| `adaptadores/proveedor_ficticio.py` | Respuesta simulada, sin consumir APIs |
| `adaptadores/adaptador_openai.py` | Único archivo que conoce a OpenAI |
| `fabricas/fabrica_proveedores.py` | Decide qué proveedor concreto crear |
| `pruebas/` | Pruebas unitarias; no se conectan a Discord ni a OpenAI |

### Adapter

El bot espera `await proveedor.responder(mensaje) -> str`. El SDK de OpenAI tiene otra forma
(`AsyncOpenAI`, `responses.create(...)`, un objeto `Response` y sus propias excepciones).
`AdaptadorOpenAI` traduce entre ambas: convierte la pregunta en una solicitud, la respuesta en
un `str` y las excepciones de OpenAI en `ErrorProveedorNoDisponible` o `ErrorTemporalProveedor`.
Por eso `bot.py` nunca importa `openai`.

### Factory

`crear_proveedor(configuracion)` es el único lugar que decide si se usa `ProveedorFicticio`
o `AdaptadorOpenAI`, y valida que existan la clave y el modelo cuando se elige OpenAI.
Quien la llama solo recibe un `ProveedorChat`.

## Requisitos

- Python 3.12.
- Una cuenta de Discord y un servidor donde tengas permiso de administrar.
- Para el proveedor real: una cuenta en [platform.openai.com](https://platform.openai.com) con saldo.

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

Si `python3` no existe o es anterior a 3.12:

1. Descarga el instalador **macOS 64-bit universal2** de
   [python.org](https://www.python.org/downloads/macos/). Se ejecuta de forma nativa en ARM64.
2. Al terminar, abre `Aplicaciones/Python 3.12` y ejecuta **Install Certificates.command**.
   Sin este paso la conexión a Discord puede fallar con `CERTIFICATE_VERIFY_FAILED`.
3. Verifica la arquitectura: `python3 -c "import platform; print(platform.machine())"` debe
   mostrar `arm64`.

En cada terminal nueva hay que activar el entorno otra vez con `source .venv/bin/activate`.

## 2. Pruebas

```bash
python3 -m unittest -v
```

## 3. Crear el bot en Discord

1. En <https://discord.com/developers/applications> pulsa **New Application**.
2. Menú **Bot** → **Reset Token** → copia el token. No actives ningún *Privileged Gateway Intent*.
3. Menú **OAuth2** → **OAuth2 URL Generator** (no uses el enlace de la página *Installation*):
   - Scopes: `bot` y `applications.commands`.
   - Bot Permissions: `View Channels` y `Send Messages`.
   - Integration Type: **Guild Install**.
   - Abre la *Generated URL* en el navegador, elige **Add to server** y autoriza.
   - Comprueba que el bot aparece en la lista de miembros con la etiqueta **APP**.
4. En la app de Discord: **Ajustes de usuario → Avanzado → Modo desarrollador**.
   - Clic derecho en el servidor → **Copiar ID del servidor**.
   - Clic derecho en el canal de texto → **Copiar ID del canal**.

## 4. Configurar OpenAI (solo para el proveedor real)

1. **Settings → Billing**: carga saldo prepagado y **desactiva la recarga automática**.
2. **Settings → Projects**: crea un proyecto solo para el bot. En **Limits**:
   - permite únicamente el modelo que usarás (por ejemplo `gpt-5.4-nano` y su snapshot);
   - fija un límite de gasto bajo y activa **Enforce hard limit**.
3. En <https://platform.openai.com/api-keys>, con ese proyecto seleccionado,
   **Create new secret key**:
   - Permissions: **Restricted**, y solo **Model capabilities → Responses (/v1/responses): Write**;
   - fecha de expiración corta;
   - una clave distinta por computadora, para poder revocarlas por separado.

## 5. Variables de entorno

```bash
cp .env.example .env
```

Edita `.env` (por ejemplo con `nano .env`):

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DISCORD_TOKEN` | Sí | Token del bot |
| `DISCORD_CHANNEL_ID` | Sí | Canal donde el bot responde; en otros canales rechaza el comando |
| `DISCORD_GUILD_ID` | Recomendada | Servidor donde se registra `/preguntar` (aparece al instante) |
| `PROVEEDOR_CHAT` | No | `ficticio` (por defecto) u `openai` |
| `LIMITE_CONSULTAS_POR_USUARIO` | No | Consultas por persona mientras el bot está encendido (por defecto 5) |
| `OPENAI_API_KEY` | Con `openai` | Clave secreta de OpenAI |
| `OPENAI_MODEL` | Con `openai` | Modelo, por ejemplo `gpt-5.4-nano` |

## 6. Ejecutar

```bash
python3 bot.py
```

La terminal muestra `Proveedor de respuestas: ...` y después `Bot conectado como ...`.
El bot funciona mientras el programa corre; se detiene con `Ctrl+C`.
Después de editar `.env` o el código hay que reiniciarlo.

## Comportamiento y límites

| Situación | Respuesta del bot |
|---|---|
| Pregunta válida | Respuesta pública del proveedor |
| Comando usado en otro canal | Mensaje privado indicando el canal permitido |
| Pregunta de más de 500 caracteres | Mensaje privado con el máximo (Discord rechaza por su cuenta más de 6000) |
| Se alcanzó el límite de consultas | Mensaje privado; se reinicia al reiniciar el bot |
| Clave inválida, modelo no permitido o saldo agotado | "El proveedor de respuestas no está disponible…" |
| Falla temporal de OpenAI | "Ocurrió un error temporal…" |
| Respuesta mayor a ~300 tokens | Se envía recortada con un aviso al final |

- Las consultas rechazadas o que fallan no descuentan cupo.
- Cada pregunta es independiente: el bot no tiene memoria de conversación.
- El modelo no tiene acceso a internet: responde con lo aprendido en su entrenamiento y puede
  equivocarse.
- Las respuestas no generan menciones (`@everyone` no notifica a nadie).

## Solución de problemas

| Mensaje | Causa probable |
|---|---|
| `Error de configuración: Falta la variable de entorno ...` | Falta esa variable en `.env` |
| `Discord rechazó el token` | Token incorrecto o regenerado; copia uno nuevo con **Reset Token** |
| `Discord no permitió registrar el comando` | El bot no está en el servidor de `DISCORD_GUILD_ID` o ese ID es incorrecto |
| `/preguntar` no aparece | Revisa `DISCORD_GUILD_ID` y recarga Discord (`Ctrl+R` / `Cmd+R`) |
| `CERTIFICATE_VERIFY_FAILED` (macOS) | Ejecuta **Install Certificates.command** |
| Terminal: `AuthenticationError` | Clave de OpenAI incorrecta, revocada o expirada |
| Terminal: `PermissionDeniedError` | Faltan permisos en la clave o el modelo no está permitido en el proyecto |
| Terminal: `NotFoundError` | `OPENAI_MODEL` no existe o está mal escrito |
| Respuestas duplicadas o errores de interacción | Hay dos copias del bot corriendo con el mismo token |

## Seguridad

- `.env` contiene secretos y está en `.gitignore`: **nunca** lo subas, lo compartas ni le
  tomes captura.
- Los estudiantes usan el comando en Discord; las claves solo existen en la computadora que
  ejecuta el bot.
- Los mensajes de error en Discord y en la terminal no incluyen claves ni trazas del proveedor.
- Si un token o clave se filtra: en Discord usa **Reset Token**; en OpenAI revoca la clave y
  crea otra.
