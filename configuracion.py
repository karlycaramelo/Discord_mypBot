import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

RUTA_ENV = Path(__file__).resolve().parent / ".env"
PROVEEDORES_VALIDOS = ("ficticio", "openai")
LIMITE_CONSULTAS_POR_DEFECTO = 5


class ErrorConfiguracion(Exception):
    """Error al cargar la configuración. Su mensaje nunca incluye secretos."""


@dataclass(frozen=True)
class Configuracion:
    # repr=False evita que los secretos aparezcan si alguien imprime la configuración.
    token_discord: str = field(repr=False)
    id_canal: int
    id_servidor: int | None
    proveedor_chat: str
    limite_consultas_por_usuario: int
    clave_openai: str | None = field(repr=False)
    modelo_openai: str | None


def leer_texto(nombre: str) -> str | None:
    valor = os.getenv(nombre, "").strip()
    if valor == "":
        return None
    return valor


def leer_obligatorio(nombre: str) -> str:
    valor = leer_texto(nombre)
    if valor is None:
        raise ErrorConfiguracion(f"Falta la variable de entorno {nombre}.")
    return valor


def convertir_id(nombre: str, valor: str) -> int:
    if not valor.isdigit():
        raise ErrorConfiguracion(f"La variable {nombre} debe ser un número (ID de Discord).")
    return int(valor)


def leer_limite_consultas() -> int:
    texto = leer_texto("LIMITE_CONSULTAS_POR_USUARIO")
    if texto is None:
        return LIMITE_CONSULTAS_POR_DEFECTO
    if not texto.isdigit() or int(texto) < 1:
        raise ErrorConfiguracion("LIMITE_CONSULTAS_POR_USUARIO debe ser un entero mayor que 0.")
    return int(texto)


def cargar_configuracion() -> Configuracion:
    # Las variables ya definidas en el sistema tienen prioridad sobre el archivo .env.
    load_dotenv(RUTA_ENV)

    id_canal = convertir_id("DISCORD_CHANNEL_ID", leer_obligatorio("DISCORD_CHANNEL_ID"))

    texto_servidor = leer_texto("DISCORD_GUILD_ID")
    id_servidor = None
    if texto_servidor is not None:
        id_servidor = convertir_id("DISCORD_GUILD_ID", texto_servidor)

    proveedor = (leer_texto("PROVEEDOR_CHAT") or "ficticio").lower()
    if proveedor not in PROVEEDORES_VALIDOS:
        raise ErrorConfiguracion(
            f"PROVEEDOR_CHAT debe ser uno de: {', '.join(PROVEEDORES_VALIDOS)}."
        )

    return Configuracion(
        token_discord=leer_obligatorio("DISCORD_TOKEN"),
        id_canal=id_canal,
        id_servidor=id_servidor,
        proveedor_chat=proveedor,
        limite_consultas_por_usuario=leer_limite_consultas(),
        clave_openai=leer_texto("OPENAI_API_KEY"),
        modelo_openai=leer_texto("OPENAI_MODEL"),
    )
