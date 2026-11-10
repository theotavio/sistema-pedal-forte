from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QMessageBox,
    QFrame,
    QTabWidget,
)
from backend.services.inventory_service import (
    listar_situacao_todos_estoques,
    obter_kardex,
    obter_situacao_estoque,
    registrar_movimentacao,
)
from backend.services.item_service import listar_itens
from backend.exceptions import ErroRegraNegocio
from frontend.animations import animar_surgimento_widget


class DialogoMovimentacao(QDialog):
    def __init__(self, parent=None, codigo_preselecionado=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Movimentação de Estoque")
        self.resize(480, 360)
        self.codigo_preselecionado = codigo_preselecionado
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        quadro_formulario = QFrame()
        quadro_formulario.setProperty("class", "card")
        layout_formulario = QFormLayout(quadro_formulario)
        layout_formulario.setSpacing(10)

        self.combo_item = QComboBox()
        itens = listar_itens()
        for item in itens:
            rotulo = f"{item.codigo} - {item.descricao} ({item.unidade})"
            self.combo_item.addItem(rotulo, item.codigo)

        if self.codigo_preselecionado:
            indice = self.combo_item.findData(self.codigo_preselecionado)
            if indice >= 0:
                self.combo_item.setCurrentIndex(indice)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["ENTRADA", "SAIDA", "AJUSTE"])

        self.campo_quantidade = QDoubleSpinBox()
        self.campo_quantidade.setRange(0.01, 1000000.0)
        self.campo_quantidade.setDecimals(2)
        self.campo_quantidade.setValue(1.0)

        self.campo_documento = QLineEdit()
        self.campo_documento.setPlaceholderText("Ex: NF 1042, Inventário Físico, Requisição Almox.")

        layout_formulario.addRow("Item a Movimentar:", self.combo_item)
        layout_formulario.addRow("Tipo de Movimentação (RF04):", self.combo_tipo)
        layout_formulario.addRow("Quantidade / Novo Saldo:", self.campo_quantidade)
        layout_formulario.addRow("Documento / Motivo (RN10):", self.campo_documento)

        layout.addWidget(quadro_formulario)

        caixa_botoes = QHBoxLayout()
        caixa_botoes.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "btn-secondary")
        btn_cancelar.clicked.connect(self.reject)

        btn_confirmar = QPushButton("Confirmar Movimentação")
        btn_confirmar.setProperty("class", "btn-primary")
        btn_confirmar.clicked.connect(self.salvar_movimentacao)

        caixa_botoes.addWidget(btn_cancelar)
        caixa_botoes.addWidget(btn_confirmar)
        layout.addLayout(caixa_botoes)

    def salvar_movimentacao(self):
        codigo_item = self.combo_item.currentData()
        tipo_mov = self.combo_tipo.currentText()
        quantidade = self.campo_quantidade.value()
        documento = self.campo_documento.text().strip()

        if not documento:
            QMessageBox.warning(
                self, "Aviso", "O motivo/documento é obrigatório para auditoria no Kardex (RN10)."
            )
            return

        try:
            registrar_movimentacao(
                codigo_item=codigo_item,
                tipo_movimentacao=tipo_mov,
                quantidade=quantidade,
                documento_motivo=documento,
            )
            QMessageBox.information(self, "Sucesso", "Movimentação registrada com sucesso no Kardex.")
            self.accept()
        except ErroRegraNegocio as erro_regra:
            QMessageBox.warning(self, "Regra de Estoque (RN02)", str(erro_regra))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha na movimentação: {exc}")


class VisaoEstoque(QWidget):
    dados_modificados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        cabecalho = QHBoxLayout()
        textos = QVBoxLayout()
        titulo = QLabel("Gestão de Estoques e Auditoria de Kardex")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Posição física, controle do estoque de segurança (RF05) e histórico imutável (RN10)"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_movimento = QPushButton("Nova Movimentação")
        btn_movimento.setProperty("class", "btn-primary")
        btn_movimento.clicked.connect(self.ao_clicar_nova_movimentacao)
        cabecalho.addWidget(btn_movimento)

        layout.addLayout(cabecalho)

        self.abas = QTabWidget()

        aba_posicao = QWidget()
        layout_posicao = QVBoxLayout(aba_posicao)
        layout_posicao.setContentsMargins(16, 16, 16, 16)

        barra_filtro = QHBoxLayout()
        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("Filtrar itens por código ou descrição...")
        self.campo_busca.textChanged.connect(self.atualizar_tabela_posicao)
        barra_filtro.addWidget(self.campo_busca)

        btn_atualizar_pos = QPushButton("Atualizar")
        btn_atualizar_pos.setProperty("class", "btn-secondary")
        btn_atualizar_pos.clicked.connect(self.atualizar_dados)
        barra_filtro.addWidget(btn_atualizar_pos)
        layout_posicao.addLayout(barra_filtro)

        self.tabela_posicao = QTableWidget()
        self.tabela_posicao.setColumnCount(8)
        self.tabela_posicao.setHorizontalHeaderLabels([
            "Código", "Descrição", "Tipo", "Unidade", "Saldo Atual", "Est. Segurança", "Déficit", "Situação"
        ])
        self.tabela_posicao.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabela_posicao.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_posicao.verticalHeader().setVisible(False)
        self.tabela_posicao.setAlternatingRowColors(True)
        self.tabela_posicao.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_posicao.doubleClicked.connect(self.ao_clicar_duas_vezes_posicao)
        layout_posicao.addWidget(self.tabela_posicao)

        self.abas.addTab(aba_posicao, "Posição Geral de Estoque")

        aba_kardex = QWidget()
        layout_kardex = QVBoxLayout(aba_kardex)
        layout_kardex.setContentsMargins(16, 16, 16, 16)

        barra_selecao_kardex = QHBoxLayout()
        rotulo_k_item = QLabel("Consultar Kardex do Item:")
        rotulo_k_item.setStyleSheet("font-weight: 700; color: #334155;")
        barra_selecao_kardex.addWidget(rotulo_k_item)

        self.combo_item_kardex = QComboBox()
        self.combo_item_kardex.currentIndexChanged.connect(self.atualizar_visao_kardex)
        barra_selecao_kardex.addWidget(self.combo_item_kardex, 1)

        self.distintivo_status_kardex = QLabel("Saldo: -")
        self.distintivo_status_kardex.setStyleSheet(
            "padding: 6px 14px; border-radius: 6px; font-weight: 700; background-color: #F1F5F9; color: #334155;"
        )
        barra_selecao_kardex.addWidget(self.distintivo_status_kardex)

        layout_kardex.addLayout(barra_selecao_kardex)

        self.tabela_kardex = QTableWidget()
        self.tabela_kardex.setColumnCount(7)
        self.tabela_kardex.setHorizontalHeaderLabels([
            "ID", "Data / Hora", "Tipo Mov.", "Qtd Movimentada", "Saldo Anterior", "Novo Saldo", "Documento / Motivo"
        ])
        self.tabela_kardex.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabela_kardex.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.tabela_kardex.verticalHeader().setVisible(False)
        self.tabela_kardex.setAlternatingRowColors(True)
        layout_kardex.addWidget(self.tabela_kardex)

        self.abas.addTab(aba_kardex, "Kardex (Histórico Imutável)")

        layout.addWidget(self.abas)

    def atualizar_dados(self):
        self.atualizar_tabela_posicao()

        codigo_atual = self.combo_item_kardex.currentData()
        self.combo_item_kardex.blockSignals(True)
        self.combo_item_kardex.clear()
        itens = listar_itens()
        for item in itens:
            rotulo = f"{item.codigo} - {item.descricao} ({item.tipo_item})"
            self.combo_item_kardex.addItem(rotulo, item.codigo)

        if codigo_atual:
            indice = self.combo_item_kardex.findData(codigo_atual)
            if indice >= 0:
                self.combo_item_kardex.setCurrentIndex(indice)
        self.combo_item_kardex.blockSignals(False)

        self.atualizar_visao_kardex()
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def atualizar_tabela_posicao(self):
        termo = self.campo_busca.text().strip().lower()
        estoques = listar_situacao_todos_estoques()

        if termo:
            estoques = [
                item for item in estoques
                if termo in item["codigo"].lower() or termo in item["descricao"].lower()
            ]

        self.tabela_posicao.setRowCount(len(estoques))
        for linha_idx, item in enumerate(estoques):
            self.tabela_posicao.setItem(linha_idx, 0, QTableWidgetItem(item["codigo"]))
            self.tabela_posicao.setItem(linha_idx, 1, QTableWidgetItem(item["descricao"]))

            tipo_widget = QTableWidgetItem(item["tipo_item"])
            tipo_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela_posicao.setItem(linha_idx, 2, tipo_widget)

            unidade_widget = QTableWidgetItem(item["unidade"])
            unidade_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela_posicao.setItem(linha_idx, 3, unidade_widget)

            saldo_widget = QTableWidgetItem(f"{item['estoque_atual']:.1f}")
            saldo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_posicao.setItem(linha_idx, 4, saldo_widget)

            seguranca_widget = QTableWidgetItem(f"{item['estoque_seguranca']:.1f}")
            seguranca_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_posicao.setItem(linha_idx, 5, seguranca_widget)

            deficit_widget = QTableWidgetItem(f"{item['deficit']:.1f}" if item["deficit"] > 0 else "-")
            deficit_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_posicao.setItem(linha_idx, 6, deficit_widget)

            situacao_widget = QTableWidgetItem()
            situacao_widget.setTextAlignment(Qt.AlignCenter)
            fonte_sit = QFont()
            fonte_sit.setBold(True)
            situacao_widget.setFont(fonte_sit)
            if item["esta_abaixo_seguranca"]:
                situacao_widget.setText("ABAIXO DO SEGURANCA")
                situacao_widget.setForeground(QColor("#DC2626"))
                situacao_widget.setBackground(QColor("#FEE2E2"))
            else:
                situacao_widget.setText("ADEQUADO")
                situacao_widget.setForeground(QColor("#166534"))
                situacao_widget.setBackground(QColor("#DCFCE7"))
            self.tabela_posicao.setItem(linha_idx, 7, situacao_widget)

        self.tabela_posicao.resizeColumnsToContents()
        self.tabela_posicao.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def atualizar_visao_kardex(self):
        codigo = self.combo_item_kardex.currentData()
        if not codigo:
            return

        try:
            status = obter_situacao_estoque(codigo)
            if status["esta_abaixo_seguranca"]:
                self.distintivo_status_kardex.setText(
                    f"Saldo: {status['estoque_atual']:.1f} {status['unidade']} | "
                    f"ABAIXO DA SEGURANCA ({status['estoque_seguranca']:.1f})"
                )
                self.distintivo_status_kardex.setStyleSheet(
                    "padding: 6px 14px; border-radius: 6px; font-weight: 700; "
                    "background-color: #FEE2E2; color: #DC2626;"
                )
            else:
                self.distintivo_status_kardex.setText(
                    f"Saldo: {status['estoque_atual']:.1f} {status['unidade']} | "
                    f"Estoque Segurança: {status['estoque_seguranca']:.1f}"
                )
                self.distintivo_status_kardex.setStyleSheet(
                    "padding: 6px 14px; border-radius: 6px; font-weight: 700; "
                    "background-color: #DCFCE7; color: #15803D;"
                )

            registros = obter_kardex(codigo)
            self.tabela_kardex.setRowCount(len(registros))
            for linha_idx, reg in enumerate(registros):
                self.tabela_kardex.setItem(linha_idx, 0, QTableWidgetItem(f"#{reg.id}"))
                self.tabela_kardex.setItem(linha_idx, 1, QTableWidgetItem(reg.data_movimentacao))

                tipo_widget = QTableWidgetItem(reg.tipo_movimentacao)
                tipo_widget.setTextAlignment(Qt.AlignCenter)
                fonte_tipo = QFont()
                fonte_tipo.setBold(True)
                tipo_widget.setFont(fonte_tipo)
                if reg.tipo_movimentacao == "ENTRADA":
                    tipo_widget.setBackground(QColor("#DCFCE7"))
                    tipo_widget.setForeground(QColor("#166534"))
                elif reg.tipo_movimentacao == "SAIDA":
                    tipo_widget.setBackground(QColor("#FEF3C7"))
                    tipo_widget.setForeground(QColor("#B45309"))
                elif reg.tipo_movimentacao == "AJUSTE":
                    tipo_widget.setBackground(QColor("#DBEAFE"))
                    tipo_widget.setForeground(QColor("#1D4ED8"))
                self.tabela_kardex.setItem(linha_idx, 2, tipo_widget)

                qtd_widget = QTableWidgetItem(f"{reg.quantidade:.2f}")
                qtd_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_kardex.setItem(linha_idx, 3, qtd_widget)

                ant_widget = QTableWidgetItem(f"{reg.estoque_anterior:.2f}")
                ant_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_kardex.setItem(linha_idx, 4, ant_widget)

                novo_widget = QTableWidgetItem(f"{reg.novo_estoque:.2f}")
                novo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_kardex.setItem(linha_idx, 5, novo_widget)

                self.tabela_kardex.setItem(linha_idx, 6, QTableWidgetItem(reg.documento_motivo))

            self.tabela_kardex.resizeColumnsToContents()
            self.tabela_kardex.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar Kardex: {exc}")

    def ao_clicar_duas_vezes_posicao(self):
        linha = self.tabela_posicao.currentRow()
        if linha >= 0:
            codigo = self.tabela_posicao.item(linha, 0).text()
            indice = self.combo_item_kardex.findData(codigo)
            if indice >= 0:
                self.combo_item_kardex.setCurrentIndex(indice)
                self.abas.setCurrentIndex(1)

    def ao_clicar_nova_movimentacao(self):
        codigo_pre = None
        if self.abas.currentIndex() == 0:
            linha = self.tabela_posicao.currentRow()
            if linha >= 0:
                codigo_pre = self.tabela_posicao.item(linha, 0).text()
        else:
            codigo_pre = self.combo_item_kardex.currentData()

        dialogo = DialogoMovimentacao(self, codigo_preselecionado=codigo_pre)
        if dialogo.exec():
            self.atualizar_dados()
            self.dados_modificados.emit()


InventoryView = VisaoEstoque
MovementDialog = DialogoMovimentacao
