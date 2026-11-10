from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox


def confirmar_acao(parent, titulo: str, mensagem: str) -> bool:
    caixa = QMessageBox(parent)
    caixa.setWindowTitle(titulo)
    caixa.setText(mensagem)
    caixa.setIcon(QMessageBox.Question)
    botao_sim = caixa.addButton("Sim", QMessageBox.YesRole)
    caixa.addButton("Não", QMessageBox.NoRole)
    caixa.setDefaultButton(botao_sim)
    caixa.setWindowModality(Qt.WindowModal)
    caixa.exec()
    return caixa.clickedButton() == botao_sim
