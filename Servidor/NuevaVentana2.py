from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class NewWindow(QWidget):
    def __init__(self,imgBytes):
        super().__init__()
        self.resize(640,480)
        self.setWindowTitle("New Window")
        
        pixmap = QPixmap()       
        pixmap.loadFromData(imgBytes)

        self.canvas=QLabel()
        self.canvas.setPixmap(pixmap)

        layout=QGridLayout()
        layout.addWidget(self.canvas,0,0)

        self.setLayout(layout)
      

      

      
      
