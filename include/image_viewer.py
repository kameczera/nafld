from PyQt5.QtWidgets import QRubberBand, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QWheelEvent, QMouseEvent
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPointF, QRect, QSize
# import utility

class ImageViewer(QGraphicsView):
    cropped = pyqtSignal(int, QPixmap)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setDragMode(QGraphicsView.NoDrag)

        self.zoom_factor = 1.15
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.is_dragging = False
        self.enable_cropping = False
        self.last_mouse_pos = QPointF()
        self.setScene(self.scene)
        self.origin = QPoint()
        self.count_cropped = 0

    def display_image(self, pixmap):
        self.enable_cropping = True
        self.scene.clear()
        self.resetTransform()
        self.pix_map = pixmap
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)
    
    def get_pixmap(self):
        return self.pix_map

    # Metodos ja setados para o funcionamento do rubberband (recorte de imagem)
    # ------------------------------------------------------------------------------------------- #

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.enable_cropping:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()

        elif event.button() == Qt.RightButton:
            self.is_dragging = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()

            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

        elif not self.origin.isNull() and self.enable_cropping:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubber_band.hide()
            rubber_band_rect = self.rubber_band.geometry()
            if rubber_band_rect.width() > 1 and rubber_band_rect.height() > 1:
                scene_rect = self.mapToScene(rubber_band_rect).boundingRect()
                pixmap_item = self.scene.items()[0]
                original_pixmap = pixmap_item.pixmap()
                cropped_pixmap = original_pixmap.copy(scene_rect.toRect())
                self.cropped.emit(self.count_cropped, cropped_pixmap)
                self.count_cropped += 1
            # else:
            #     utility.MessageBox.show_alert("Selecao da ROI muito pequena.")
        elif event.button() == Qt.RightButton:
            self.is_dragging = False
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)