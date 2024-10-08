import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import cv2

class Histogram(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(Figure())
        self.layout.addWidget(self.canvas)

        self.ax = self.canvas.figure.subplots()

        self.compute_histogram(pixmap)
    
    def compute_histogram(self, pixmap):
        image = self.qpixmap_to_numpy(pixmap)

        hist = cv2.calcHist([image], [0], None, [256], [0,255])

        self.ax.plot(hist, color='black')

        self.ax.set_ylim(0, 3000)
        self.ax.margins(y=0)

        self.ax.set_title('Histograma Preto-Branco')
        self.ax.set_xlabel('Intensidade do Pixel')
        self.ax.set_ylabel('Frequencia')
        self.canvas.draw()

    def qpixmap_to_numpy(self, pixmap):
        qimage = pixmap.toImage()

        width = qimage.width()
        height = qimage.height()
        
        ptr = qimage.bits()
        ptr.setsize(height * width)
        arr = np.array(ptr).reshape((height, width))

        return arr
