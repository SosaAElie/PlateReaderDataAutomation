from PyQt5.QtWidgets import QStackedWidget, QApplication, QVBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from Pages.ElisaNeutralizationAssayPage import ElisaNeutralizationAssayPage
from Pages.ElisaStandardsPage import ElisaStandardsPage
from Pages.LuciferaseAssayPage import LuciferaseAssayPage
from Classes.SwitchPagesBar import SwitchPagesBar
import sys

class StackedPages(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400,600)
        self.setWindowTitle('ELISA and Neutralization Assay Automator')
        self.addWidget(ElisaStandardsPage(self))
        self.addWidget(ElisaNeutralizationAssayPage(self))
        self.addWidget(LuciferaseAssayPage(self))
        self.show()

class ParentPage(QWidget):
    def __init__(self)->None:
        super().__init__()
        stacked_pages = StackedPages()
        switch_pages_bar = SwitchPagesBar(stacked_pages)
        layout = QVBoxLayout(self)
        layout.addWidget(switch_pages_bar)
        layout.addWidget(stacked_pages)
        self.setLayout(layout)

        self.show()

def dark_theme(app:QApplication)->QApplication:
    '''
    Applies dark theme.
    Copied from
    https://github.com/pyqt/examples/blob/_/src/09%20Qt%20dark%20theme/main.py
    '''

    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    return app
	
if __name__ == '__main__':
    app = dark_theme(QApplication([]))
    main = ParentPage()
    sys.exit(app.exec_())