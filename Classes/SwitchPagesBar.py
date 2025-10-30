from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QStackedWidget, QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtGui import QFont

class SwitchPagesBar(QWidget):
    def __init__(self, parent: QStackedWidget) -> None:
        super().__init__(parent) 
        layout = QHBoxLayout(self)                   
        for n in range(parent.count()):            
            button = QPushButton(f"Page {n+1}")
            temp_func = lambda n: lambda: parent.setCurrentIndex(n)
            button.clicked.connect(temp_func(n))            
            layout.addWidget(button)
        self.setLayout(layout)


