import unittest
from users import registerUser

class TestRegisterUser(unittest.TestCase):

    def test_registro_usuario_nuevo(self):
        resultado = registerUser(999000, "XD", "sistemas", "estudiante")
        self.assertEqual(resultado, "User successfully registered")

    def test_registro_usuario_existente(self):
        # Registramos una vez
        registerUser(10096758, "pepe", "electronica", "profesor")
        # Intentamos registrar el mismo usuario
        resultado = registerUser(10096758, "pepe", "electronica", "profesor")
        self.assertEqual(resultado, "User already registered")

    def test_registro_usuario_real(self):
        resultado = registerUser(101010846474747,"pepe", "Electronics Engineering", "estudiante")
        self.assertIn(resultado, ["User successfully registered", "User already registered"])

if __name__ == '__main__':
    unittest.main()
