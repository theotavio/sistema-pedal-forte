import subprocess
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QFrame,
    QSizePolicy,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from backend.services.chart_service import (
    gerar_grafico_posicao_estoque,
    gerar_grafico_estoque_projetado,
    gerar_grafico_ordens_por_entrega,
    gerar_grafico_crp,
    DIRETORIO_GRAFICOS,
)
from backend.services.item_service import listar_itens
from backend.services.work_center_service import listar_centros_trabalho
from frontend.animations import animar_surgimento_widget


class VisaoGraficos(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.abas_renderizadas = set()
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        cabecalho = QHBoxLayout()
        textos = QVBoxLayout()
        titulo = QLabel("Gráficos de Gestão e Acompanhamento Visual (Matplotlib)")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel("Visualização interativa na tela e exportação automática em PNG (RF16)")
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_abrir_pasta = QPushButton("Abrir Pasta dos Gráficos")
        btn_abrir_pasta.setProperty("class", "btn-secondary")
        btn_abrir_pasta.clicked.connect(self.abrir_pasta_graficos)
        cabecalho.addWidget(btn_abrir_pasta)

        layout.addLayout(cabecalho)

        self.abas = QTabWidget()

        self.aba1 = self.criar_interface_aba1()
        self.aba2 = self.criar_interface_aba2()
        self.aba3 = self.criar_interface_aba3()
        self.aba4 = self.criar_interface_aba4()

        self.abas.addTab(self.aba1, "16.1 Posição de Estoque")
        self.abas.addTab(self.aba2, "16.2 Estoque Projetado")
        self.abas.addTab(self.aba3, "16.3 Ordens por Entrega")
        self.abas.addTab(self.aba4, "16.4 Carga x Capacidade")

        self.abas.currentChanged.connect(self.ao_mudar_aba)
        layout.addWidget(self.abas)

    def criar_interface_aba1(self):
        aba = QWidget()
        layout = QVBoxLayout(aba)
        layout.setContentsMargins(14, 14, 14, 14)

        barra = QHBoxLayout()
        rotulo = QLabel("Saldo Atual x Estoque de Segurança de Todos os Itens (Barras)")
        rotulo.setStyleSheet("font-weight: 700; color: #0F172A;")
        barra.addWidget(rotulo)
        barra.addStretch()

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(lambda: self.forcar_renderizar_aba(0))
        barra.addWidget(btn_atualizar)

        btn_salvar = QPushButton("Salvar PNG")
        btn_salvar.setProperty("class", "btn-primary")
        btn_salvar.clicked.connect(lambda: self.salvar_grafico_como(1))
        barra.addWidget(btn_salvar)

        layout.addLayout(barra)

        self.quadro_grafico_1 = QFrame()
        self.quadro_grafico_1.setProperty("class", "card")
        self.layout_grafico_1 = QVBoxLayout(self.quadro_grafico_1)
        layout.addWidget(self.quadro_grafico_1)
        return aba

    def criar_interface_aba2(self):
        aba = QWidget()
        layout = QVBoxLayout(aba)
        layout.setContentsMargins(14, 14, 14, 14)

        barra = QHBoxLayout()
        rotulo = QLabel("Selecionar Item:")
        rotulo.setStyleSheet("font-weight: 700; color: #0F172A;")
        barra.addWidget(rotulo)

        self.combo_aba2_item = QComboBox()
        self.combo_aba2_item.currentIndexChanged.connect(lambda: self.forcar_renderizar_aba(1))
        barra.addWidget(self.combo_aba2_item, 1)

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(lambda: self.forcar_renderizar_aba(1))
        barra.addWidget(btn_atualizar)

        btn_salvar = QPushButton("Salvar PNG")
        btn_salvar.setProperty("class", "btn-primary")
        btn_salvar.clicked.connect(lambda: self.salvar_grafico_como(2))
        barra.addWidget(btn_salvar)

        layout.addLayout(barra)

        self.quadro_grafico_2 = QFrame()
        self.quadro_grafico_2.setProperty("class", "card")
        self.layout_grafico_2 = QVBoxLayout(self.quadro_grafico_2)
        layout.addWidget(self.quadro_grafico_2)
        return aba

    def criar_interface_aba3(self):
        aba = QWidget()
        layout = QVBoxLayout(aba)
        layout.setContentsMargins(14, 14, 14, 14)

        barra = QHBoxLayout()
        rotulo = QLabel("Ordens de Produção (OP) e Compra (OC) por Semana de Entrega (Empilhadas)")
        rotulo.setStyleSheet("font-weight: 700; color: #0F172A;")
        barra.addWidget(rotulo)
        barra.addStretch()

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(lambda: self.forcar_renderizar_aba(2))
        barra.addWidget(btn_atualizar)

        btn_salvar = QPushButton("Salvar PNG")
        btn_salvar.setProperty("class", "btn-primary")
        btn_salvar.clicked.connect(lambda: self.salvar_grafico_como(3))
        barra.addWidget(btn_salvar)

        layout.addLayout(barra)

        self.quadro_grafico_3 = QFrame()
        self.quadro_grafico_3.setProperty("class", "card")
        self.layout_grafico_3 = QVBoxLayout(self.quadro_grafico_3)
        layout.addWidget(self.quadro_grafico_3)
        return aba

    def criar_interface_aba4(self):
        aba = QWidget()
        layout = QVBoxLayout(aba)
        layout.setContentsMargins(14, 14, 14, 14)

        barra = QHBoxLayout()
        rotulo = QLabel("Selecionar Centro de Trabalho:")
        rotulo.setStyleSheet("font-weight: 700; color: #0F172A;")
        barra.addWidget(rotulo)

        self.combo_aba4_ct = QComboBox()
        self.combo_aba4_ct.currentIndexChanged.connect(lambda: self.forcar_renderizar_aba(3))
        barra.addWidget(self.combo_aba4_ct, 1)

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(lambda: self.forcar_renderizar_aba(3))
        barra.addWidget(btn_atualizar)

        btn_salvar = QPushButton("Salvar PNG")
        btn_salvar.setProperty("class", "btn-primary")
        btn_salvar.clicked.connect(lambda: self.salvar_grafico_como(4))
        barra.addWidget(btn_salvar)

        layout.addLayout(barra)

        self.quadro_grafico_4 = QFrame()
        self.quadro_grafico_4.setProperty("class", "card")
        self.layout_grafico_4 = QVBoxLayout(self.quadro_grafico_4)
        layout.addWidget(self.quadro_grafico_4)
        return aba

    def atualizar_dados(self):
        self.abas_renderizadas.clear()
        if self.combo_aba2_item.count() == 0:
            self.combo_aba2_item.blockSignals(True)
            for item in listar_itens():
                self.combo_aba2_item.addItem(
                    f"{item.codigo} - {item.descricao} ({item.tipo_item})", item.codigo
                )
            self.combo_aba2_item.blockSignals(False)

        if self.combo_aba4_ct.count() == 0:
            self.combo_aba4_ct.blockSignals(True)
            for centro in listar_centros_trabalho():
                self.combo_aba4_ct.addItem(f"{centro.codigo} - {centro.nome}", centro.codigo)
            self.combo_aba4_ct.blockSignals(False)

        self.ao_mudar_aba(self.abas.currentIndex())
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def forcar_renderizar_aba(self, indice):
        self.abas_renderizadas.discard(indice)
        self.ao_mudar_aba(indice)

    def ao_mudar_aba(self, indice):
        if indice not in self.abas_renderizadas:
            if indice == 0:
                self.renderizar_grafico_1()
            elif indice == 1:
                self.renderizar_grafico_2()
            elif indice == 2:
                self.renderizar_grafico_3()
            elif indice == 3:
                self.renderizar_grafico_4()
            self.abas_renderizadas.add(indice)

    def limpar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        plt.close("all")

    def renderizar_grafico_1(self):
        self.limpar_layout(self.layout_grafico_1)
        figura, _ = gerar_grafico_posicao_estoque(salvar_arquivo=False)
        tela = FigureCanvas(figura)
        tela.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout_grafico_1.addWidget(tela)

    def renderizar_grafico_2(self):
        codigo = self.combo_aba2_item.currentData()
        if not codigo:
            return
        self.limpar_layout(self.layout_grafico_2)
        figura, _ = gerar_grafico_estoque_projetado(codigo, salvar_arquivo=False)
        tela = FigureCanvas(figura)
        tela.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout_grafico_2.addWidget(tela)

    def renderizar_grafico_3(self):
        self.limpar_layout(self.layout_grafico_3)
        figura, _ = gerar_grafico_ordens_por_entrega(salvar_arquivo=False)
        tela = FigureCanvas(figura)
        tela.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout_grafico_3.addWidget(tela)

    def renderizar_grafico_4(self):
        codigo_ct = self.combo_aba4_ct.currentData()
        if not codigo_ct:
            return
        self.limpar_layout(self.layout_grafico_4)
        figura, _ = gerar_grafico_crp(codigo_ct, salvar_arquivo=False)
        tela = FigureCanvas(figura)
        tela.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout_grafico_4.addWidget(tela)

    def salvar_grafico_como(self, numero_aba):
        nome_padrao = ""
        figura = None
        if numero_aba == 1:
            nome_padrao = "posicao_estoque.png"
            figura, _ = gerar_grafico_posicao_estoque()
        elif numero_aba == 2:
            codigo = self.combo_aba2_item.currentData() or "item"
            nome_padrao = f"estoque_projetado_{codigo}.png"
            figura, _ = gerar_grafico_estoque_projetado(codigo)
        elif numero_aba == 3:
            nome_padrao = "ordens_semana_entrega.png"
            figura, _ = gerar_grafico_ordens_por_entrega()
        elif numero_aba == 4:
            centro = self.combo_aba4_ct.currentData() or "centro"
            nome_padrao = f"carga_capacidade_{centro}.png"
            figura, _ = gerar_grafico_crp(centro)

        caminho_destino, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Gráfico em PNG",
            str(DIRETORIO_GRAFICOS / nome_padrao),
            "Imagens PNG (*.png)",
        )
        if caminho_destino:
            figura.savefig(caminho_destino, dpi=150)
            QMessageBox.information(
                self, "Sucesso", f"Gráfico salvo com sucesso em:\n{caminho_destino}"
            )

    def abrir_pasta_graficos(self):
        try:
            subprocess.run(["xdg-open", str(DIRETORIO_GRAFICOS)])
        except Exception:
            QMessageBox.information(
                self, "Diretório", f"Arquivos salvos em:\n{DIRETORIO_GRAFICOS}"
            )


ChartsView = VisaoGraficos
