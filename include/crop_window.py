from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QRubberBand, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QVBoxLayout
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF, QRect, QSize
# from utility import MessageBox

class CropWindow(QWidget):
    cropped = pyqtSignal(int, QPixmap)
    def __init__(self, pixmap):
        super().__init__()
        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self.view)
        self.view.setScene(self.scene)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.view)
        self.origin = QPoint()
        self.count_cropped = 0

        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Recorte de Imagem")
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = QPoint(event.pos())
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
    
    def mouseMoveEvent(self, event):
        if not self.origin.isNull() and self.rubber_band.isVisible():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent (self, event):
        if event.button() == Qt.LeftButton:
            self.rubber_band.hide()
            rubber_band_rect = self.rubber_band.geometry()
            if rubber_band_rect.width() > 1 and rubber_band_rect.height() > 1:
                scene_rect = self.view.mapToScene(rubber_band_rect).boundingRect()
                pixmap_item = self.scene.items()[0]
                original_pixmap = pixmap_item.pixmap()
                cropped_pixmap = original_pixmap.copy(scene_rect.toRect())
                self.cropped.emit(self.count_cropped, cropped_pixmap)
                self.count_cropped += 1
            # else:
                # MessageBox.show_alert("Selecao da ROI muito pequena.")