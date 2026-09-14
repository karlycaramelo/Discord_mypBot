import os
import unittest
from unittest.mock import patch

import configuracion
from configuracion import Configuracion, ErrorConfiguracion, cargar_configuracion

# Valor inventado: las pruebas nunca usan el .env real.
TOKEN_DE_PRUEBA = "token-inventado-para-pruebas"

VARIABLES_MINIMAS = {
    "DISCORD_TOKEN": TOKEN_DE_PRUEBA,
    "DISCORD_CHANNEL_ID": "123",
}


def cargar_con(variables: dict[str, str]) -> Configuracion:
    # clear=True vacía el entorno y el parche a load_dotenv evita leer el archivo .env.
    with patch.dict(os.environ, variables, clear=True):
        with patch.object(configuracion, "load_dotenv"):
            return cargar_configuracion()


class PruebasConfiguracion(unittest.TestCase):
    def test_valores_por_defecto(self) -> None:
        config = cargar_con(VARIABLES_MINIMAS)

        self.assertEqual(config.id_canal, 123)
        self.assertIsNone(config.id_servidor)
        self.assertEqual(config.proveedor_chat, "ficticio")
        self.assertEqual(config.limite_consultas_por_usuario, 5)

    def test_falta_token(self) -> None:
        with self.assertRaises(ErrorConfiguracion):
            cargar_con({"DISCORD_CHANNEL_ID": "123"})

    def test_id_de_canal_no_numerico(self) -> None:
        variables = {**VARIABLES_MINIMAS, "DISCORD_CHANNEL_ID": "general"}
        with self.assertRaises(ErrorConfiguracion):
            cargar_con(variables)

    def test_proveedor_desconocido(self) -> None:
        variables = {**VARIABLES_MINIMAS, "PROVEEDOR_CHAT": "otro"}
        with self.assertRaises(ErrorConfiguracion):
            cargar_con(variables)

    def test_limite_de_consultas_invalido(self) -> None:
        variables = {**VARIABLES_MINIMAS, "LIMITE_CONSULTAS_POR_USUARIO": "0"}
        with self.assertRaises(ErrorConfiguracion):
            cargar_con(variables)

    def test_el_token_no_aparece_al_imprimir(self) -> None:
        config = cargar_con(VARIABLES_MINIMAS)

        self.assertNotIn(TOKEN_DE_PRUEBA, repr(config))

    def test_los_errores_no_revelan_el_token(self) -> None:
        variables = {**VARIABLES_MINIMAS, "DISCORD_CHANNEL_ID": "abc"}
        with self.assertRaises(ErrorConfiguracion) as contexto:
            cargar_con(variables)

        self.assertNotIn(TOKEN_DE_PRUEBA, str(contexto.exception))


if __name__ == "__main__":
    unittest.main()
