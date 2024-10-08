from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QToolBar, QTreeWidget, QTreeWidgetItem

# Classe ToolBarImages: Classe que mostra as imagens adicionadas pelo botao load, "croppadas" e do dataset Liver
class ToolBarImages(QToolBar):
    display = pyqtSignal(QPixmap)
    

    def __init__(self, images = None):
        super().__init__("All Images")
        self.images = images

        # Inicialização da hierarquia de pastas
        # ------------------------------------------------------------------------------------------- #

        self.folder_hierarchy = QTreeWidget()
        self.pixmap_dictionary = {}
        self.addWidget(self.folder_hierarchy)


        self.folder_hierarchy.itemClicked.connect(self.display_image)
        self.folder_hierarchy.setHeaderHidden(True)

        self.cropped_imgs_node = QTreeWidgetItem(self.folder_hierarchy)
        self.cropped_imgs_node.setText(0, f"Coleção de Cortes")

        # ------------------------------------------------------------------------------------------- #

        # Fazendo o a extracao das imagens do formato images[0][n][m] para a hierarquia de pastas
        for id_pacient,patient in enumerate(self.images):
            # Inicialização do nós Raizes (Nó dos pacientes)
            patient_node = QTreeWidgetItem(self.folder_hierarchy)
            patient_node.setText(0, f"Paciente {id_pacient}")
            for id_image,image in enumerate(patient):
                self.open_image_patients(image, id_pacient, id_image, patient_node)

    def display_image(self, item, column):
        # Deixar Nós raiz inclicáveis (nós com header de paciente)
        if item.parent() is None:
            return
        # TODO: Nome dos nós folhas estranho. Mudar aqui
        self.display.emit(self.pixmap_dictionary[f"{item.text(1)}-{item.text(2)}"])

    def open_image_patients(self, image, id_pacient, id_image, father):
        # Inicialização dos nós Folhas (Imagens dos pacientes)
        child_item = QTreeWidgetItem(father)
        child_item.setText(0, f"Imagem {id_image}")
        child_item.setText(1, str(id_pacient))
        child_item.setText(2, str(id_image))
        height, width = image.shape
        image_bytes = image.tobytes()
        q_img = QImage(image_bytes, width, height, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_img)
        self.pixmap_dictionary[f"{id_pacient}-{id_image}"] = pixmap
    
    def create_image_from_cropped(self, id_crop, crop_qpixmap):
        child_item = QTreeWidgetItem(self.cropped_imgs_node)
        child_item.setText(0, f"Corte {id_crop} ")
        child_item.setText(1, "C")
        child_item.setText(2, str(id_crop))
        self.pixmap_dictionary[f"C-{id_crop}"] = crop_qpixmap