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

        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)

        # Variáveis de controle de interação com rubber band
        # ---------------------------------------------------------- #

        self.zoom_factor = 1.15
        self.is_dragging = False
        self.enable_cropping = False
        self.is_resizing_rb = False
        self.is_translating = False
        self.direction = -1
        
        self.origin = QPoint()
        self.last_mouse_pos = QPoint()
        self.current_rect = QRect()
        
        # ---------------------------------------------------------- #

        self.setScene(self.scene)

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

    # Metodos ja setados para o funcionamento recorte de imagem e zoom
    # ------------------------------------------------------------------------------------------- #

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.last_mouse_pos = event.pos()
        self.direction = self.click_near_border(event.pos())
        
        # Usuário clicando na borda do rubber band? -> Se sim, ativar Resize
        if ((event.button() == Qt.LeftButton and self.direction != -1)):
            self.is_resizing_rb = True
        
        # Usuário clicando dentro do rubber band? -> Se sim, ativar translação
        elif (self.current_rect.contains(event.pos())):
            self.is_translating = True

        # Usuário está criando um novo quadrado? -> Se sim, criar um novo quadrado
        elif event.button() == Qt.LeftButton and self.enable_cropping:
            self.current_rect = QRect(self.origin, QSize())
            self.rubber_band.setGeometry(self.current_rect)
            self.rubber_band.show()

        # Usuário está arrastando a visualização da imagem? -> Se sim, ative is_dragging
        elif event.button() == Qt.RightButton:
            self.is_dragging = True
            self.setCursor(Qt.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Escalando ou Arrastando a visualização da imagem
        if self.is_dragging:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

        # Dimensionando o rubber band
        elif self.is_resizing_rb:
            # Switch case da rosa dos ventos
            match self.direction:
                case 1:
                    self.current_rect.setRight(event.pos().x())
                case 2:
                    self.current_rect.setTop(event.pos().y())
                case 3:
                    self.current_rect.setLeft(event.pos().x())
                case 4:
                    self.current_rect.setBottom(event.pos().y())
            self.rubber_band.setGeometry(self.current_rect.normalized())
        
        # Transladando o rubber band
        elif self.is_translating:
            delta = event.pos() - self.last_mouse_pos
            self.current_rect.translate(delta)
            self.rubber_band.setGeometry(self.current_rect.normalized())
            self.last_mouse_pos = event.pos()

        # Criando o rubber band
        elif not self.origin.isNull() and self.enable_cropping:
            self.current_rect = QRect(self.origin, event.pos())
            self.rubber_band.setGeometry(self.current_rect.normalized())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
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
            self.is_translating = False
            self.is_resizing_rb = False
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------------------------------- #

    def click_near_border(self, pos):
        band_rect = self.rubber_band.geometry()

        margin = 10 # Margem de detecção de proximidade de borda (Mudar caso necessário)

        # Rosa dos ventos (Leste, Norte, Oeste, Sul - 1, 2, 3, 4) simplesmente para deixar o código mais eficiente, se tiver muito ilegível mudar
        if (abs(pos.x() - band_rect.right()) < margin): return 1 
        elif (abs(pos.y() - band_rect.top()) < margin): return 2
        elif (abs(pos.x() - band_rect.left()) < margin): return 3
        elif (abs(pos.y() - band_rect.bottom()) < margin): return 4
        
        return -1