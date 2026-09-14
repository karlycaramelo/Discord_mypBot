import unittest

from adaptadores import AdaptadorOpenAI, ProveedorFicticio
from configuracion import Configuracion, ErrorConfiguracion
from dominio import ProveedorChat
from fabricas import crear_proveedor

# Valores inventados: crear el adaptador no hace ninguna solicitud a OpenAI.
CLAVE_DE_PRUEBA = "clave-inventada-para-pruebas"
MODELO_DE_PRUEBA = "modelo-de-prueba"


def configuracion_con(
    proveedor: str,
    clave: str | None = None,
    modelo: str | None = None,
) -> Configuracion:
    return Configuracion(
        token_discord="token-inventado",
        id_canal=123,
        id_servidor=None,
        proveedor_chat=proveedor,
        limite_consultas_por_usuario=5,
        clave_openai=clave,
        modelo_openai=modelo,
    )


class PruebasProveedorChat(unittest.TestCase):
    def test_no_se_puede_instanciar_la_interfaz(self) -> None:
        with self.assertRaises(TypeError):
            ProveedorChat()


class PruebasProveedorFicticio(unittest.IsolatedAsyncioTestCase):
    def test_implementa_la_interfaz(self) -> None:
        self.assertIsInstance(ProveedorFicticio(), ProveedorChat)

    async def test_responde_con_la_pregunta(self) -> None:
        proveedor = ProveedorFicticio()

        respuesta = await proveedor.responder("¿Qué es un Adapter?")

        self.assertEqual(respuesta, "Respuesta simulada para: ¿Qué es un Adapter?")


class PruebasFabricaProveedores(unittest.TestCase):
    def test_crea_proveedor_ficticio(self) -> None:
        proveedor = crear_proveedor(configuracion_con("ficticio"))

        self.assertIsInstance(proveedor, ProveedorFicticio)

    def test_crea_adaptador_openai(self) -> None:
        configuracion = configuracion_con("openai", CLAVE_DE_PRUEBA, MODELO_DE_PRUEBA)

        proveedor = crear_proveedor(configuracion)

        self.assertIsInstance(proveedor, AdaptadorOpenAI)
        self.assertIsInstance(proveedor, ProveedorChat)

    def test_openai_sin_clave_produce_error_claro(self) -> None:
        configuracion = configuracion_con("openai", modelo=MODELO_DE_PRUEBA)

        with self.assertRaises(ErrorConfiguracion) as contexto:
            crear_proveedor(configuracion)

        self.assertIn("OPENAI_API_KEY", str(contexto.exception))

    def test_openai_sin_modelo_produce_error_sin_revelar_la_clave(self) -> None:
        configuracion = configuracion_con("openai", clave=CLAVE_DE_PRUEBA)

        with self.assertRaises(ErrorConfiguracion) as contexto:
            crear_proveedor(configuracion)

        self.assertIn("OPENAI_MODEL", str(contexto.exception))
        self.assertNotIn(CLAVE_DE_PRUEBA, str(contexto.exception))

    def test_proveedor_desconocido(self) -> None:
        with self.assertRaises(ErrorConfiguracion):
            crear_proveedor(configuracion_con("otro"))


if __name__ == "__main__":
    unittest.main()
