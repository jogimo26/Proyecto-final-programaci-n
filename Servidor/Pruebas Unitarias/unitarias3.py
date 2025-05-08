import unittest
from users import registerUser, getQR, sendQR

class TestSendQR(unittest.TestCase):

    def test_sendqr_asigna_puesto_correctamente(self):
        # Registrar usuario
        registerUser(8765432, "pass456", "electronica", "estudiante")
        
        # Obtener el QR como buffer
        qr_buffer = getQR(8765432, "pass456")
        
        # Convertir el buffer a bytes PNG
        png_bytes = qr_buffer.getvalue()

        # Enviar el QR y obtener el puesto asignado
        puesto = sendQR(png_bytes)

        # Verificaciones 
        assert puesto is not None, "No se asignó ningún puesto"
        assert puesto[0] == "S", "El puesto asignado no es para estudiante"

if __name__ == '__main__':
    unittest.main()
