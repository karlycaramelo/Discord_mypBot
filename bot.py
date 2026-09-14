import logging

import discord
from discord import app_commands

from adaptadores import ProveedorFicticio
from configuracion import Configuracion, ErrorConfiguracion, cargar_configuracion
from dominio import ErrorProveedorNoDisponible, ErrorTemporalProveedor, ProveedorChat

LIMITE_CARACTERES_PREGUNTA = 500
LIMITE_CARACTERES_DISCORD = 2000

registro = logging.getLogger(__name__)


class BotDiscord(discord.Client):
    # El bot recibe un ProveedorChat ya construido: no sabe si es ficticio o real.
    def __init__(self, configuracion: Configuracion, proveedor: ProveedorChat) -> None:
        super().__init__(intents=discord.Intents.default())
        self.configuracion = configuracion
        self.proveedor = proveedor
        self.arbol = app_commands.CommandTree(self)
        self.registrar_comandos()

    def registrar_comandos(self) -> None:
        @self.arbol.command(name="preguntar", description="Haz una pregunta al bot.")
        @app_commands.describe(mensaje="Tu pregunta (máximo 500 caracteres)")
        async def preguntar(interaction: discord.Interaction, mensaje: str) -> None:
            await self.atender_pregunta(interaction, mensaje)

    async def setup_hook(self) -> None:
        # Registrar en un servidor específico hace que el comando aparezca al instante.
        id_servidor = self.configuracion.id_servidor
        if id_servidor is None:
            await self.arbol.sync()
            return
        servidor = discord.Object(id=id_servidor)
        self.arbol.copy_global_to(guild=servidor)
        await self.arbol.sync(guild=servidor)

    async def on_ready(self) -> None:
        registro.info("Bot conectado como %s.", self.user)

    async def atender_pregunta(self, interaction: discord.Interaction, mensaje: str) -> None:
        if len(mensaje) > LIMITE_CARACTERES_PREGUNTA:
            await interaction.response.send_message(
                f"Tu pregunta tiene {len(mensaje)} caracteres. "
                f"El máximo es {LIMITE_CARACTERES_PREGUNTA}.",
                ephemeral=True,
            )
            return

        # defer() avisa a Discord que responderemos después; sin esto la
        # interacción expira si el proveedor tarda más de 3 segundos.
        await interaction.response.defer(thinking=True)
        respuesta = await self.consultar_proveedor(mensaje)

        # AllowedMentions.none() impide que una respuesta con @everyone notifique a todos.
        await interaction.followup.send(
            respuesta[:LIMITE_CARACTERES_DISCORD],
            allowed_mentions=discord.AllowedMentions.none(),
        )

    async def consultar_proveedor(self, mensaje: str) -> str:
        try:
            return await self.proveedor.responder(mensaje)
        except ErrorProveedorNoDisponible:
            return "El proveedor de respuestas no está disponible en este momento."
        except ErrorTemporalProveedor:
            return "Ocurrió un error temporal. Intenta de nuevo en unos minutos."
        except Exception:
            # La traza se queda en la terminal de quien ejecuta el bot, nunca en Discord.
            registro.exception("Error inesperado al consultar el proveedor.")
            return "Ocurrió un error inesperado. Intenta de nuevo más tarde."


def main() -> None:
    try:
        configuracion = cargar_configuracion()
    except ErrorConfiguracion as error:
        print(f"Error de configuración: {error}")
        raise SystemExit(1)

    proveedor = ProveedorFicticio()
    bot = BotDiscord(configuracion, proveedor)

    try:
        bot.run(configuracion.token_discord, root_logger=True)
    except discord.LoginFailure:
        print("Discord rechazó el token. Revisa DISCORD_TOKEN en tu archivo .env.")
        raise SystemExit(1)
    except discord.Forbidden:
        print(
            "Discord no permitió registrar el comando. Verifica que el bot esté "
            "invitado al servidor indicado en DISCORD_GUILD_ID."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
