import unittest

from adaptadores import ProveedorFicticio
from dominio import ProveedorChat


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


if __name__ == "__main__":
    unittest.main()
