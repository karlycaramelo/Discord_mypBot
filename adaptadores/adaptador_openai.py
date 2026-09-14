import logging

import openai
from openai import AsyncOpenAI
from openai.types.responses import Response

from dominio import ErrorProveedorNoDisponible, ErrorTemporalProveedor, ProveedorChat

MAXIMO_TOKENS_RESPUESTA = 300
SEGUNDOS_DE_ESPERA = 30
REINTENTOS = 1
AVISO_RECORTE = "_(Respuesta recortada por el límite de longitud del bot.)_"

# Cada llamada es independiente: el modelo no recibe mensajes anteriores.
INSTRUCCIONES = (
    "Eres un modelo de lenguaje de OpenAI conectado al bot de Discord de un curso de "
    "Ciencias de la Computación. Responde en español, con tono amable y cercano, "
    "de forma clara y breve: unas 150 palabras como máximo. "
    "Si piden algo amplio, como un tutorial o un curso, da un resumen y los primeros "
    "pasos en lugar del contenido completo, porque una respuesta larga se corta. "
    "Cada pregunta llega sola: no tienes memoria de mensajes anteriores ni acceso a "
    "internet, así que no pidas más contexto ni ofrezcas continuar la conversación; "
    "da la mejor respuesta posible con lo que recibes. "
    "No inventes datos, noticias, citas ni enlaces. Si algo es incierto o reciente, "
    "dilo con honestidad y sugiere dónde verificarlo, como la documentación oficial."
)

# Errores que no se arreglan reintentando: clave inválida, modelo inexistente, etc.
ERRORES_NO_DISPONIBLE = (
    openai.AuthenticationError,
    openai.PermissionDeniedError,
    openai.NotFoundError,
    openai.BadRequestError,
)

registro = logging.getLogger(__name__)


class AdaptadorOpenAI(ProveedorChat):
    """Adapta el SDK de OpenAI a la interfaz ProveedorChat.

    Es el único archivo del proyecto que conoce a OpenAI: su cliente,
    sus parámetros, la forma de su respuesta y sus excepciones.
    """

    def __init__(self, clave_api: str, modelo: str) -> None:
        self._cliente = AsyncOpenAI(
            api_key=clave_api,
            timeout=SEGUNDOS_DE_ESPERA,
            max_retries=REINTENTOS,
        )
        self._modelo = modelo

    async def responder(self, mensaje: str) -> str:
        try:
            respuesta = await self._cliente.responses.create(
                model=self._modelo,
                instructions=INSTRUCCIONES,
                input=mensaje,
                max_output_tokens=MAXIMO_TOKENS_RESPUESTA,
                store=False,
            )
        except openai.APIError as error:
            # "from None" evita arrastrar el error original, cuyo texto puede
            # incluir fragmentos de la clave.
            raise traducir_error(error) from None

        # Si se alcanzó el límite de tokens, output_text trae el texto parcial.
        texto = respuesta.output_text.strip()
        if texto == "":
            registro.warning("OpenAI regresó una respuesta vacía (estado: %s).", respuesta.status)
            raise ErrorTemporalProveedor()

        if se_corto_por_tokens(respuesta):
            return marcar_recorte(texto)
        return texto


def se_corto_por_tokens(respuesta: Response) -> bool:
    detalles = respuesta.incomplete_details
    return detalles is not None and detalles.reason == "max_output_tokens"


def marcar_recorte(texto: str) -> str:
    # Un número impar de ``` significa que el corte dejó un bloque de código abierto.
    if texto.count("```") % 2 == 1:
        texto = texto + "\n```"
    return f"{texto}\n\n{AVISO_RECORTE}"


def traducir_error(error: openai.APIError) -> Exception:
    # Solo se registran el tipo y el código; el mensaje de OpenAI no se imprime.
    codigo = getattr(error, "code", None)
    registro.warning("OpenAI rechazó la solicitud: %s (código: %s).", type(error).__name__, codigo)

    if isinstance(error, openai.RateLimitError) and codigo == "insufficient_quota":
        return ErrorProveedorNoDisponible()
    if isinstance(error, ERRORES_NO_DISPONIBLE):
        return ErrorProveedorNoDisponible()
    return ErrorTemporalProveedor()
