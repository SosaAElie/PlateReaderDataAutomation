from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog, QPushButton
from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from Classes.ErrorMessageBox import ErrorMessageBox
from Classes.FileSelector import FileSelector
import ExcelAutomators.luciferase_assay as lucA

class LuciferaseAssayPage(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.file_selectors:list[FileSelector] = []
        self.vlayout = QVBoxLayout(self)
        self.setLayout(self.vlayout)
        
        self.description = QLabel("Luciferase Assay page", self)
        self.vlayout.addWidget(self.description)

        file_selector = FileSelector(self)
        self.vlayout.addWidget(file_selector)
        self.file_selectors.append(file_selector)

        self.add_button = QPushButton("Add", self, clicked = self.add_file_selectors)
        self.vlayout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove", self, clicked = self.remove_file_selector)
        self.vlayout.addWidget(self.remove_button)

        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.process)
        self.vlayout.addWidget(self.process_button)
    def select_destination(self):
        self.destination_filepath = QFileDialog.getExistingDirectory(self,'Select Directory')
    
    def add_file_selectors(self)->None:
        index = self.layout().indexOf(self.file_selectors[-1])+1
        file_selector = FileSelector(self)
        self.vlayout.insertWidget(index,file_selector)
        self.file_selectors.append(file_selector)

    def remove_file_selector(self)->None:
        if len(self.file_selectors) > 1: self.vlayout.removeWidget(self.file_selectors.pop())

    def process(self)->None:
        for file_selector in self.file_selectors:
            lucA.main(*file_selector.get_selection())