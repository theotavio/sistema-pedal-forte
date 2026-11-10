from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QFrame,
    QLabel,
    QPushButton,
    QButtonGroup,
)
from frontend.styles import ESTILO_CLARO_MODERNO
from frontend.animations import animar_surgimento_widget
from frontend.views.dashboard_view import VisaoPainelPrincipal
from frontend.views.items_view import VisaoItens
from frontend.views.bom_view import VisaoEstrutura
from frontend.views.inventory_view import VisaoEstoque
from frontend.views.work_centers_view import VisaoCentrosTrabalho
from frontend.views.mps_view import VisaoPlanoMestre
from frontend.views.mrp_view import VisaoMRP
from frontend.views.orders_view import VisaoOrdens
from frontend.views.crp_view import VisaoCRP
from frontend.views.costs_view import VisaoCustos
from frontend.views.charts_view import VisaoGraficos
from frontend.views.export_view import VisaoExportacao


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pedal Forte Bicicletas - Sistema de Planejamento de Manufatura (MRP II)")
        self.setStyleSheet(ESTILO_CLARO_MODERNO)
        self.setMinimumSize(1280, 800)

        tela = self.screen().availableGeometry() if self.screen() else None
        if tela:
            largura = min(1600, max(1360, tela.width() - 40))
            altura = min(1000, max(840, tela.height() - 50))
            self.resize(largura, altura)
            self.move((tela.width() - largura) // 2, (tela.height() - altura) // 2)
        else:
            self.resize(1580, 980)

        self.botoes_navegacao = {}
        self.visoes_carregadas = set()
        self.visoes_pendentes = set()
        self.configurar_interface()

    def configurar_interface(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        barra_lateral = self.criar_barra_lateral()
        layout_principal.addWidget(barra_lateral)

        self.pilha_visoes = QStackedWidget()
        layout_principal.addWidget(self.pilha_visoes, 1)

        self.visao_painel = VisaoPainelPrincipal()
        self.visao_itens = VisaoItens()
        self.visao_estrutura = VisaoEstrutura()
        self.visao_estoque = VisaoEstoque()
        self.visao_centros = VisaoCentrosTrabalho()
        self.visao_mps = VisaoPlanoMestre()
        self.visao_mrp = VisaoMRP()
        self.visao_ordens = VisaoOrdens()
        self.visao_crp = VisaoCRP()
        self.visao_custos = VisaoCustos()
        self.visao_graficos = VisaoGraficos()
        self.visao_exportacao = VisaoExportacao()

        self.visao_painel.solicitar_navegacao.connect(self.navegar_para_chave)

        self.mapa_visoes = {
            "painel": (0, self.visao_painel),
            "itens": (1, self.visao_itens),
            "estrutura": (2, self.visao_estrutura),
            "estoque": (3, self.visao_estoque),
            "centros": (4, self.visao_centros),
            "mps": (5, self.visao_mps),
            "mrp": (6, self.visao_mrp),
            "ordens": (7, self.visao_ordens),
            "crp": (8, self.visao_crp),
            "custos": (9, self.visao_custos),
            "graficos": (10, self.visao_graficos),
            "exportacao": (11, self.visao_exportacao),
        }

        for chave, (indice, widget_visao) in self.mapa_visoes.items():
            self.pilha_visoes.addWidget(widget_visao)
            if hasattr(widget_visao, "dados_modificados"):
                widget_visao.dados_modificados.connect(
                    lambda k=chave: self.notificar_dados_modificados(origem=k)
                )

        self.navegar_para_chave("painel", forcar=True)

    def notificar_dados_modificados(self, origem=None):
        todas = set(self.mapa_visoes.keys())
        if origem:
            todas.discard(origem)
        self.visoes_pendentes.update(todas)
        if hasattr(self.visao_crp, "crp_armazenado"):
            self.visao_crp.crp_armazenado = []

    def criar_barra_lateral(self):
        barra_lateral = QFrame()
        barra_lateral.setObjectName("sidebar")
        layout = QVBoxLayout(barra_lateral)
        layout.setContentsMargins(10, 14, 10, 16)
        layout.setSpacing(4)

        titulo_marca = QLabel("PEDAL FORTE")
        titulo_marca.setObjectName("brandTitle")
        subtitulo_marca = QLabel("Manufatura & MRP II")
        subtitulo_marca.setObjectName("brandSubtitle")

        layout.addWidget(titulo_marca)
        layout.addWidget(subtitulo_marca)
        layout.addSpacing(10)

        itens_navegacao = [
            ("painel", "Painel Geral"),
            ("itens", "Cadastro de Itens"),
            ("estrutura", "Estrutura BOM"),
            ("estoque", "Estoques e Kardex"),
            ("centros", "Centros e Roteiros"),
            ("mps", "Plano Mestre (MPS)"),
            ("mrp", "Cálculo MRP"),
            ("ordens", "Ordens (OP e OC)"),
            ("crp", "Capacidade (CRP)"),
            ("custos", "Custos Padrão"),
            ("graficos", "Gráficos Gerenciais"),
            ("exportacao", "Exportar CSV"),
        ]

        self.grupo_navegacao = QButtonGroup(barra_lateral)
        self.grupo_navegacao.setExclusive(True)

        for chave, texto_rotulo in itens_navegacao:
            botao = QPushButton(texto_rotulo)
            botao.setProperty("class", "nav-btn")
            botao.setCheckable(True)
            botao.setCursor(Qt.PointingHandCursor)
            botao.clicked.connect(lambda checked, k=chave: self.navegar_para_chave(k))
            self.grupo_navegacao.addButton(botao)
            layout.addWidget(botao)
            self.botoes_navegacao[chave] = botao

        layout.addStretch()
        return barra_lateral

    def navegar_para_chave(self, chave, forcar=False):
        if chave not in self.mapa_visoes:
            return

        indice, widget_visao = self.mapa_visoes[chave]
        botao = self.botoes_navegacao.get(chave)
        if botao and not botao.isChecked():
            botao.setChecked(True)

        ja_ativa = self.pilha_visoes.currentIndex() == indice
        precisa_atualizar = (
            chave not in self.visoes_carregadas
            or chave in self.visoes_pendentes
            or forcar
        )

        if ja_ativa and not precisa_atualizar:
            return

        self.pilha_visoes.setCurrentIndex(indice)

        if precisa_atualizar:
            if hasattr(widget_visao, "atualizar_dados"):
                widget_visao.atualizar_dados()
            elif hasattr(widget_visao, "refresh_data"):
                widget_visao.refresh_data()
            self.visoes_carregadas.add(chave)
            self.visoes_pendentes.discard(chave)

        animar_surgimento_widget(widget_visao)


MainWindow = JanelaPrincipal


MainWindow = JanelaPrincipal
