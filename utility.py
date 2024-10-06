from PyQt5.QtWidgets import QMessageBox

class MessageBox:
    
    def show_alert(message):
        # Cria uma caixa de mensagem
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Alerta")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)

        # Exibe a caixa de mensagem
        msg.exec_()
