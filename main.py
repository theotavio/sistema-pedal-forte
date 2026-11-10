import os
import sys
from PySide6.QtWidgets import QApplication
from backend.seed_data import popular_dados_iniciais
from frontend.main_window import JanelaPrincipal

os.environ["QT_LOGGING_RULES"] = (
    "qt.qpa.wayland*=false;qt.qpa.wayland.textinput*=false;qt.textinput*=false;qt.qpa.*=false"
)


def iniciar_sistema():
    popular_dados_iniciais()

    aplicacao = QApplication(sys.argv)
    aplicacao.setApplicationName("Pedal Forte Bicicletas - MRP II")
    aplicacao.setOrganizationName("Pedal Forte Manufatura")

    janela = JanelaPrincipal()
    janela.show()

    sys.exit(aplicacao.exec())


if __name__ == "__main__":
    iniciar_sistema()
