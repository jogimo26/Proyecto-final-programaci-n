
import unittest
from users import registerUser, getQR

class TestGetQR(unittest.TestCase):
    def test_qr_con_credenciales_correctas(self):
         # Registramos un usuario primero
        registerUser(12345, "clave123", "sistemas", "estudiante")
        # Intentamos generar el QR con las mismas datos
        qr = getQR(12345, "clave123")
        self.assertIsNotNone(qr)

    def test_qr_con_credenciales_invalidas(self):
         # Intentamos generar un QR con usuario que no existe
        qr = getQR(111222333, "claveIncorrecta")
        self.assertIsNone(qr)# No debe devolver nada

if __name__ == '__main__':
    unittest.main()
