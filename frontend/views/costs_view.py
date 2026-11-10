from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QSplitter,
    QMessageBox,
)
from backend.services.cost_service import (
    calcular_custo_padrao_item,
    calcular_todos_custos_fabricados,
)
from backend.services.item_service import listar_itens
from backend.exceptions import ErroRegraNegocio
from frontend.animations import animar_surgimento_widget


class VisaoCustos(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.custos_todos_calculados = None
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        cabecalho = QHBoxLayout()
        textos = QVBoxLayout()
        titulo = QLabel("Custo Padrão dos Itens Fabricados (Rollup Recursivo)")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Composição de custos de materiais e mão de obra percorrendo a BOM recursivamente (RF13)"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_atualizar = QPushButton("Recalcular Custos")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(self.recalcular_custos)
        cabecalho.addWidget(btn_atualizar)

        layout.addLayout(cabecalho)

        barra_superior = QFrame()
        barra_superior.setProperty("class", "card")
        layout_barra = QHBoxLayout(barra_superior)
        layout_barra.setContentsMargins(14, 10, 14, 10)

        rotulo_selecionar = QLabel("Selecionar Produto Fabricado (PA / SA):")
        rotulo_selecionar.setStyleSheet("font-weight: 700; color: #334155;")
        layout_barra.addWidget(rotulo_selecionar)

        self.combo_item = QComboBox()
        self.combo_item.currentIndexChanged.connect(self.exibir_custo_item)
        layout_barra.addWidget(self.combo_item, 1)

        layout.addWidget(barra_superior)

        layout_cartoes = QHBoxLayout()
        layout_cartoes.setSpacing(16)

        self.cartao_materiais = self.criar_cartao_custo(
            "Custo de Materiais (BOM)", "R$ 0,00", "#1D4ED8", "#EFF6FF", "#BFDBFE", "#2563EB"
        )
        self.cartao_mao_obra = self.criar_cartao_custo(
            "Custo de Mão de Obra / Centro", "R$ 0,00", "#047857", "#F0FDF4", "#BBF7D0", "#059669"
        )
        self.cartao_total = self.criar_cartao_custo(
            "Custo Padrão Total Unitário", "R$ 0,00", "#6D28D9", "#FAF5FF", "#E9D5FF", "#7C3AED"
        )

        layout_cartoes.addWidget(self.cartao_materiais)
        layout_cartoes.addWidget(self.cartao_mao_obra)
        layout_cartoes.addWidget(self.cartao_total)
        layout.addLayout(layout_cartoes)

        divisor = QSplitter(Qt.Vertical)

        quadro_componentes = QFrame()
        quadro_componentes.setProperty("class", "card")
        layout_comp = QVBoxLayout(quadro_componentes)

        rotulo_comp = QLabel("Desmembramento dos Componentes Diretos")
        rotulo_comp.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_comp.addWidget(rotulo_comp)

        self.tabela_componentes = QTableWidget()
        self.tabela_componentes.setColumnCount(7)
        self.tabela_componentes.setHorizontalHeaderLabels([
            "Código", "Descrição", "Tipo", "Quantidade", "Unidade", "Custo Unitário", "Custo Total Parcial"
        ])
        self.tabela_componentes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_componentes.verticalHeader().setVisible(False)
        self.tabela_componentes.setAlternatingRowColors(True)
        layout_comp.addWidget(self.tabela_componentes)

        divisor.addWidget(quadro_componentes)

        quadro_todos = QFrame()
        quadro_todos.setProperty("class", "card")
        layout_todos = QVBoxLayout(quadro_todos)

        rotulo_todos = QLabel("Resumo Geral de Custos de Todos os Itens Fabricados")
        rotulo_todos.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_todos.addWidget(rotulo_todos)

        self.tabela_todos = QTableWidget()
        self.tabela_todos.setColumnCount(6)
        self.tabela_todos.setHorizontalHeaderLabels([
            "Código", "Descrição", "Tipo", "Materiais", "Mão de Obra", "Custo Total"
        ])
        self.tabela_todos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_todos.verticalHeader().setVisible(False)
        self.tabela_todos.setAlternatingRowColors(True)
        self.tabela_todos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_todos.doubleClicked.connect(self.ao_clicar_duas_vezes_todos)
        layout_todos.addWidget(self.tabela_todos)

        divisor.addWidget(quadro_todos)
        divisor.setStretchFactor(0, 1)
        divisor.setStretchFactor(1, 1)

        layout.addWidget(divisor)

    def criar_cartao_custo(
        self, texto_titulo, valor_inicial, cor_destaque, cor_fundo, cor_borda, cor_acento
    ):
        quadro = QFrame()
        quadro.setStyleSheet(
            f"QFrame {{ background-color: {cor_fundo}; border: 1px solid {cor_borda}; "
            f"border-left: 5px solid {cor_acento}; border-radius: 12px; }}"
        )
        layout = QVBoxLayout(quadro)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        titulo = QLabel(texto_titulo)
        titulo.setStyleSheet(
            f"color: {cor_destaque}; font-size: 12px; font-weight: 700; "
            f"text-transform: uppercase; letter-spacing: 0.5px; border: none; background: transparent;"
        )

        valor = QLabel(valor_inicial)
        valor.setStyleSheet(
            f"color: {cor_destaque}; font-size: 28px; font-weight: 800; border: none; background: transparent;"
        )

        layout.addWidget(titulo)
        layout.addWidget(valor)
        setattr(quadro, "rotulo_valor", valor)
        return quadro

    def atualizar_dados(self):
        codigo_atual = self.combo_item.currentData()
        self.combo_item.blockSignals(True)
        self.combo_item.clear()

        fabricados = listar_itens(tipo_item="PA") + listar_itens(tipo_item="SA")
        for item in fabricados:
            rotulo = f"{item.codigo} - {item.descricao} ({item.tipo_item})"
            self.combo_item.addItem(rotulo, item.codigo)

        if codigo_atual:
            indice = self.combo_item.findData(codigo_atual)
            if indice >= 0:
                self.combo_item.setCurrentIndex(indice)

        self.combo_item.blockSignals(False)
        self.exibir_custo_item()
        self.atualizar_tabela_todos()
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def exibir_custo_item(self):
        codigo = self.combo_item.currentData()
        if not codigo:
            return

        try:
            dados_custo = calcular_custo_padrao_item(codigo)
            self.cartao_materiais.rotulo_valor.setText(f"R$ {dados_custo['custo_materiais']:.2f}")
            self.cartao_mao_obra.rotulo_valor.setText(f"R$ {dados_custo['custo_mao_obra']:.2f}")
            self.cartao_total.rotulo_valor.setText(f"R$ {dados_custo['custo_total']:.2f}")

            componentes = dados_custo.get("componentes", [])
            self.tabela_componentes.setRowCount(len(componentes))
            for linha_idx, comp in enumerate(componentes):
                self.tabela_componentes.setItem(linha_idx, 0, QTableWidgetItem(comp["codigo_componente"]))
                self.tabela_componentes.setItem(linha_idx, 1, QTableWidgetItem(comp["descricao"]))

                tipo_widget = QTableWidgetItem(comp["tipo_item"])
                tipo_widget.setTextAlignment(Qt.AlignCenter)
                self.tabela_componentes.setItem(linha_idx, 2, tipo_widget)

                qtd_widget = QTableWidgetItem(f"{comp['quantidade']:.2f}")
                qtd_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_componentes.setItem(linha_idx, 3, qtd_widget)

                unidade_widget = QTableWidgetItem(comp["unidade"])
                unidade_widget.setTextAlignment(Qt.AlignCenter)
                self.tabela_componentes.setItem(linha_idx, 4, unidade_widget)

                custo_widget = QTableWidgetItem(f"R$ {comp['custo_unitario']:.2f}")
                custo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_componentes.setItem(linha_idx, 5, custo_widget)

                tot_widget = QTableWidgetItem(f"R$ {comp['custo_total']:.2f}")
                tot_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_componentes.setItem(linha_idx, 6, tot_widget)

        except ErroRegraNegocio as erro_regra:
            QMessageBox.warning(self, "Aviso", str(erro_regra))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha no cálculo de custo: {exc}")

    def recalcular_custos(self):
        self.custos_todos_calculados = None
        self.atualizar_dados()

    def atualizar_tabela_todos(self):
        if self.custos_todos_calculados is None:
            self.custos_todos_calculados = calcular_todos_custos_fabricados()
        todos_custos = self.custos_todos_calculados
        self.tabela_todos.setRowCount(len(todos_custos))
        for linha_idx, (codigo, dados) in enumerate(todos_custos.items()):
            self.tabela_todos.setItem(linha_idx, 0, QTableWidgetItem(codigo))
            self.tabela_todos.setItem(linha_idx, 1, QTableWidgetItem(dados["descricao"]))

            tipo_widget = QTableWidgetItem(dados["tipo_item"])
            tipo_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela_todos.setItem(linha_idx, 2, tipo_widget)

            mat_widget = QTableWidgetItem(f"R$ {dados['custo_materiais']:.2f}")
            mat_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_todos.setItem(linha_idx, 3, mat_widget)

            mo_widget = QTableWidgetItem(f"R$ {dados['custo_mao_obra']:.2f}")
            mo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_todos.setItem(linha_idx, 4, mo_widget)

            tot_widget = QTableWidgetItem(f"R$ {dados['custo_total']:.2f}")
            tot_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            fonte = tot_widget.font()
            fonte.setBold(True)
            tot_widget.setFont(fonte)
            self.tabela_todos.setItem(linha_idx, 5, tot_widget)

    def ao_clicar_duas_vezes_todos(self):
        linha = self.tabela_todos.currentRow()
        if linha >= 0:
            codigo = self.tabela_todos.item(linha, 0).text()
            indice = self.combo_item.findData(codigo)
            if indice >= 0:
                self.combo_item.setCurrentIndex(indice)


CostsView = VisaoCustos
