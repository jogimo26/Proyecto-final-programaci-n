from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from new_window import NewWindow
from parking_client import registerUser

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro")
        # Se crean los labels
        l1 = QLabel('ID: ')
        l2 = QLabel('Contraseña: ')
        l3 = QLabel('Programa: ')
        l4 = QLabel('Rol: ')

        # Se crean los campos de entrada
        self.e1 = QLineEdit()
        self.e2 = QLineEdit()
        self.e3 = QLineEdit()
        self.e4 = QLineEdit()

        b1=QPushButton('Registrar Usuario')
        b1.clicked.connect(self.newWindow)
        
        
        gridLayout=QGridLayout()
        
        # Se añaden los widgets al layout
        # Textos
        gridLayout.addWidget(l1,0,0)
        gridLayout.addWidget(l2,1,0)
        gridLayout.addWidget(l3,2,0)
        gridLayout.addWidget(l4,3,0)
        
        #Entradas de texto
        gridLayout.addWidget(self.e1,0,1)
        gridLayout.addWidget(self.e2,1,1)
        gridLayout.addWidget(self.e3,2,1)
        gridLayout.addWidget(self.e4,3,1)

        # Botón del registro
        gridLayout.addWidget(b1,4,0,1,2)
        
        widget = QWidget()
        widget.setLayout(gridLayout)

        #QMainWindow requiere un widget central
        self.setCentralWidget(widget)
        
        # Deshabilita el botón de maximizar
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
    
    def newWindow(self):
        id = self.e1.text()
        password = self.e2.text()
        program = self.e3.text()
        role = self.e4.text()

        if len(id) and len(password) and len(program) and len(role):
            url="http://localhost:80"

            # Registra el usuario
            Usuario = registerUser(url, id, password, program, role)
            if Usuario == "User successfully registered":
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setText("Usuario registrado con éxito")
                msgBox.setWindowTitle("Información")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
            else:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.setText("Usuario ya existente dentro del sistema")
                msgBox.setWindowTitle("Alerta")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()

app = QApplication([])
ex = MainWindow()
ex.show()
app.exec()
