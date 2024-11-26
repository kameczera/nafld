    self.pacient_n, self.image_n = map(str, nome.split("-"))
        self.enable_cropping = True
        self.scene.clear()  # Limpar a cena para uma nova imagem
        self.resetTransform()  # Resetar a transformação
        self.pix_map = pixmap

        # Exibir a imagem
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)

        # Usar o border_item já existente para definir o retângulo
        self.current_rect = QRect(0, 0, 28, 28)  # Defina o retângulo de recorte
        self.border_item.setRect(QRectF(self.current_rect))  # Atualiza o retângulo existente
        self.scene.addItem(self.border_item)  # Adiciona à cena