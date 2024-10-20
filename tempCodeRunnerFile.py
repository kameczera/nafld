  
    def mouseMoveEvent(self, event):
     if not self.origin.isNull() and self.rubber_band.isVisible():
        # Calcula o tamanho atual do retângulo de seleção
        current_rect = QRect(self.origin, event.pos()).normalized()
        
        # Limita o tamanho do retângulo para 28x28 pixels
        size = min(current_rect.width(), 28), min(current_rect.height(), 28)
        limited_rect = QRect(self.origin, QSize(*size))
        self.rubber_band.setGeometry(limited_rect)
