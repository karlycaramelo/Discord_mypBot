import logging

import discord
from discord import app_commands

from configuracion import Configuracion, ErrorConfiguracion, cargar_configuracion
from dominio import ErrorProveedorNoDisponible, ErrorTemporalProveedor, ProveedorChat
from fabricas import crear_proveedor

LIMITE_CARACTERES_PREGUNTA = 500
LIMITE_CARACTERES_DISCORD = 2000

registro = logging.getLogger(__name__)


class BotDiscord(discord.Client):
    # El bot recibe un ProveedorChat ya construido: no sabe si es ficticio o real.
    def __init__(self, configuracion: Configuracion, proveedor: ProveedorChat) -> None:
        super().__init__(intents=discord.Intents.default())
        self.configuracion = configuracion
        self.proveedor = proveedor
        # Memoria simple por ejecución: {id de usuario de Discord: consultas usadas}.
        self.consultas_usadas: dict[int, int] = {}
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
        motivo_rechazo = self.validar_pregunta(interaction, mensaje)
        if motivo_rechazo is not None:
            await interaction.response.send_message(motivo_rechazo, ephemeral=True)
            return

        # La consulta se reserva antes del primer await: así, si un usuario envía
        # varias preguntas al mismo tiempo, no puede rebasar su límite.
        id_usuario = interaction.user.id
        self.registrar_consulta(id_usuario)

        # defer() avisa a Discord que responderemos después; sin esto la
        # interacción expira si el proveedor tarda más de 3 segundos.
        await interaction.response.defer(thinking=True)
        respuesta = await self.consultar_proveedor(id_usuario, mensaje)

        # AllowedMentions.none() impide que una respuesta con @everyone notifique a todos.
        await interaction.followup.send(
            respuesta[:LIMITE_CARACTERES_DISCORD],
            allowed_mentions=discord.AllowedMentions.none(),
        )

    def validar_pregunta(self, interaction: discord.Interaction, mensaje: str) -> str | None:
        """Regresa el motivo por el que se rechaza la pregunta, o None si es válida."""
        id_canal = self.configuracion.id_canal
        if interaction.channel_id != id_canal:
            return f"Este comando solo funciona en el canal <#{id_canal}>."

        if len(mensaje) > LIMITE_CARACTERES_PREGUNTA:
            return (
                f"Tu pregunta tiene {len(mensaje)} caracteres. "
                f"El máximo es {LIMITE_CARACTERES_PREGUNTA}."
            )

        limite = self.configuracion.limite_consultas_por_usuario
        if self.consultas_de(interaction.user.id) >= limite:
            return (
                f"Llegaste al límite de consultas ({limite} por persona). "
                "Se reinicia cuando se reinicie el bot."
            )

        return None

    def consultas_de(self, id_usuario: int) -> int:
        return self.consultas_usadas.get(id_usuario, 0)

    def registrar_consulta(self, id_usuario: int) -> None:
        self.consultas_usadas[id_usuario] = self.consultas_de(id_usuario) + 1

    def devolver_consulta(self, id_usuario: int) -> None:
        self.consultas_usadas[id_usuario] = self.consultas_de(id_usuario) - 1

    async def consultar_proveedor(self, id_usuario: int, mensaje: str) -> str:
        try:
            return await self.proveedor.responder(mensaje)
        except Exception as error:
            # Si la consulta no se pudo atender, no debe costarle al usuario.
            self.devolver_consulta(id_usuario)
            return self.mensaje_de_error(error)

    def mensaje_de_error(self, error: Exception) -> str:
        if isinstance(error, ErrorProveedorNoDisponible):
            return "El proveedor de respuestas no está disponible en este momento."
        if isinstance(error, ErrorTemporalProveedor):
            return "Ocurrió un error temporal. Intenta de nuevo en unos minutos."

        # La traza se queda en la terminal de quien ejecuta el bot, nunca en Discord.
        registro.error("Error inesperado al consultar el proveedor.", exc_info=error)
        return "Ocurrió un error inesperado. Intenta de nuevo más tarde."


def main() -> None:
    try:
        configuracion = cargar_configuracion()
        proveedor = crear_proveedor(configuracion)
    except ErrorConfiguracion as error:
        print(f"Error de configuración: {error}")
        raise SystemExit(1)

    print(f"Proveedor de respuestas: {configuracion.proveedor_chat}")
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
