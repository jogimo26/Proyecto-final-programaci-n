from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from new_window import NewWindow
from parking_client import *

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test new window")
       
        # Se crean los labels
        l1=QLabel('ID: ')
        l2=QLabel('Contraseña: ')

        # Se crean los campos de entrada
        self.e1=QLineEdit()
        self.e2=QLineEdit()

        b1=QPushButton('Obtener QR')
        b1.clicked.connect(self.newWindow)
        
        
        gridLayout=QGridLayout()
        
         # Se añaden los widgets al layout
        gridLayout.addWidget(l1,0,0)
        gridLayout.addWidget(l2,1,0)
        
        gridLayout.addWidget(self.e1,0,1)
        gridLayout.addWidget(self.e2,1,1)

        gridLayout.addWidget(b1,2,0,1,2)
        


        widget = QWidget()
        widget.setLayout(gridLayout)
        #QMainWindow requiere un widget central
        self.setCentralWidget(widget)

        
        # Deshabilita el botón de maximizar
        self.setWindowFlags( Qt.MSWindowsFixedSizeDialogHint)
    
    def newWindow(self):
        id=self.e1.text()
        password=self.e2.text()
        if len(id) and len(password):
            url="http://localhost:80"

            # Solicita un código QR al servidor (los códigos QR cambian cada fecha o cuando se reinicia el servidor)
            imgBytes=getQR(url,id,password)
            if len(imgBytes):
                self.nw=NewWindow(imgBytes)
                self.nw.show()
            else:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.setText("Usuario no Existe o Contraseña Incorrecta")
                msgBox.setWindowTitle("Alerta")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()

       
app = QApplication([])
ex = MainWindow()
ex.show()
app.exec()
