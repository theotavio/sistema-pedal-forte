import subprocess
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
    QFileDialog,
)
from backend.services.export_service import (
    exportar_posicao_estoque_csv,
    exportar_ordens_csv,
    DIRETORIO_CSV,
)
from frontend.animations import animar_surgimento_widget


class VisaoExportacao(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        cabecalho = QHBoxLayout()
        textos = QVBoxLayout()
        titulo = QLabel("Exportação de Dados em CSV (RF14)")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Extração padronizada de relatórios gerenciais para auditoria e integração com planilhas"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_abrir_pasta = QPushButton("Abrir Pasta CSV")
        btn_abrir_pasta.setProperty("class", "btn-secondary")
        btn_abrir_pasta.clicked.connect(self.abrir_pasta_dados)
        cabecalho.addWidget(btn_abrir_pasta)

        layout.addLayout(cabecalho)

        container_cartoes = QHBoxLayout()
        container_cartoes.setSpacing(20)

        cartao_estoque = QFrame()
        cartao_estoque.setProperty("class", "card")
        layout_ce = QVBoxLayout(cartao_estoque)
        layout_ce.setSpacing(14)

        titulo_ce = QLabel("Posição Geral de Estoque")
        titulo_ce.setStyleSheet("font-size: 17px; font-weight: 700; color: #0F172A;")
        layout_ce.addWidget(titulo_ce)

        desc_ce = QLabel(
            "Exporta a lista completa de todos os itens cadastrados (PA, SA, MP), incluindo "
            "saldo atual, estoque de segurança, lote mínimo, custo unitário e valor total em estoque."
        )
        desc_ce.setWordWrap(True)
        desc_ce.setStyleSheet("color: #64748B; font-size: 13px; line-height: 18px;")
        layout_ce.addWidget(desc_ce)

        layout_ce.addStretch()

        btn_exportar_estoque = QPushButton("Exportar Posição (.CSV)")
        btn_exportar_estoque.setProperty("class", "btn-primary")
        btn_exportar_estoque.clicked.connect(self.ao_clicar_exportar_estoque)
        layout_ce.addWidget(btn_exportar_estoque)

        container_cartoes.addWidget(cartao_estoque)

        cartao_ordens = QFrame()
        cartao_ordens.setProperty("class", "card")
        layout_co = QVBoxLayout(cartao_ordens)
        layout_co.setSpacing(14)

        titulo_co = QLabel("Lista Geral de Ordens (OP / OC)")
        titulo_co.setStyleSheet("font-size: 17px; font-weight: 700; color: #0F172A;")
        layout_co.addWidget(titulo_co)

        desc_co = QLabel(
            "Exporta todas as Ordens de Produção (OP) e Ordens de Compra (OC), "
            "com quantidades, semanas de liberação e entrega, status atual e sinalização de atraso."
        )
        desc_co.setWordWrap(True)
        desc_co.setStyleSheet("color: #64748B; font-size: 13px; line-height: 18px;")
        layout_co.addWidget(desc_co)

        layout_co.addStretch()

        btn_exportar_ordens = QPushButton("Exportar Ordens (.CSV)")
        btn_exportar_ordens.setProperty("class", "btn-primary")
        btn_exportar_ordens.clicked.connect(self.ao_clicar_exportar_ordens)
        layout_co.addWidget(btn_exportar_ordens)

        container_cartoes.addWidget(cartao_ordens)

        layout.addLayout(container_cartoes)
        layout.addStretch()

    def atualizar_dados(self):
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def ao_clicar_exportar_estoque(self):
        caminho_padrao = str(DIRETORIO_CSV / "posicao_estoque.csv")
        caminho_arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Posição de Estoque CSV",
            caminho_padrao,
            "Arquivos CSV (*.csv)",
        )
        if caminho_arquivo:
            try:
                saida = exportar_posicao_estoque_csv(caminho_arquivo)
                QMessageBox.information(
                    self,
                    "Exportação Concluída",
                    f"Posição de estoque exportada com sucesso em:\n{saida}",
                )
            except Exception as exc:
                QMessageBox.critical(self, "Erro na Exportação", f"Falha ao exportar CSV: {exc}")

    def ao_clicar_exportar_ordens(self):
        caminho_padrao = str(DIRETORIO_CSV / "lista_ordens.csv")
        caminho_arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Lista de Ordens CSV",
            caminho_padrao,
            "Arquivos CSV (*.csv)",
        )
        if caminho_arquivo:
            try:
                saida = exportar_ordens_csv(caminho_arquivo)
                QMessageBox.information(
                    self,
                    "Exportação Concluída",
                    f"Lista de ordens exportada com sucesso em:\n{saida}",
                )
            except Exception as exc:
                QMessageBox.critical(self, "Erro na Exportação", f"Falha ao exportar CSV: {exc}")

    def abrir_pasta_dados(self):
        try:
            subprocess.run(["xdg-open", str(DIRETORIO_CSV)])
        except Exception:
            QMessageBox.information(
                self, "Diretório", f"Arquivos CSV localizados em:\n{DIRETORIO_CSV}"
            )


ExportView = VisaoExportacao
