from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
    QFrame,
)
from backend.services.item_service import (
    listar_itens,
    criar_item,
    atualizar_item,
    excluir_item,
    obter_item,
)
from backend.services.work_center_service import listar_centros_trabalho
from backend.exceptions import ErroRegraNegocio, ErroValidacao
from frontend.animations import animar_surgimento_widget
from frontend.dialogs import confirmar_acao


class DialogoItem(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Editar Item" if item else "Novo Item - Pedal Forte")
        self.resize(500, 540)
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        quadro_formulario = QFrame()
        quadro_formulario.setProperty("class", "card")
        layout_formulario = QFormLayout(quadro_formulario)
        layout_formulario.setSpacing(10)

        self.campo_tipo = QComboBox()
        self.campo_tipo.addItems(["PA", "SA", "MP"])
        self.campo_tipo.currentTextChanged.connect(self.ao_mudar_tipo)

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText("Ex: PA-001, SA-020, MP-201")

        self.campo_descricao = QLineEdit()
        self.campo_descricao.setPlaceholderText("Descrição completa do item")

        self.campo_unidade = QLineEdit()
        self.campo_unidade.setPlaceholderText("UN, KG, M, PAR, JG, KIT")

        self.campo_custo = QDoubleSpinBox()
        self.campo_custo.setRange(0.0, 1000000.0)
        self.campo_custo.setDecimals(2)
        self.campo_custo.setPrefix("R$ ")

        self.campo_lead_time = QSpinBox()
        self.campo_lead_time.setRange(0, 52)
        self.campo_lead_time.setSuffix(" sem")

        self.campo_estoque_seguranca = QDoubleSpinBox()
        self.campo_estoque_seguranca.setRange(0.0, 1000000.0)
        self.campo_estoque_seguranca.setDecimals(1)

        self.campo_lote_minimo = QDoubleSpinBox()
        self.campo_lote_minimo.setRange(0.1, 1000000.0)
        self.campo_lote_minimo.setDecimals(1)
        self.campo_lote_minimo.setValue(1.0)

        self.campo_estoque_atual = QDoubleSpinBox()
        self.campo_estoque_atual.setRange(0.0, 1000000.0)
        self.campo_estoque_atual.setDecimals(1)

        self.campo_centro_trabalho = QComboBox()
        self.campo_centro_trabalho.addItem("Nenhum / Comprado", None)
        try:
            for centro in listar_centros_trabalho():
                self.campo_centro_trabalho.addItem(f"{centro.codigo} - {centro.nome}", centro.codigo)
        except Exception:
            pass

        self.campo_tempo_unitario = QDoubleSpinBox()
        self.campo_tempo_unitario.setRange(0.0, 1000.0)
        self.campo_tempo_unitario.setDecimals(2)
        self.campo_tempo_unitario.setSuffix(" horas")

        layout_formulario.addRow("Tipo do Item (RN01):", self.campo_tipo)
        layout_formulario.addRow("Código do Item:", self.campo_codigo)
        layout_formulario.addRow("Descrição:", self.campo_descricao)
        layout_formulario.addRow("Unidade de Medida:", self.campo_unidade)
        layout_formulario.addRow("Custo Unitário:", self.campo_custo)
        layout_formulario.addRow("Lead Time:", self.campo_lead_time)
        layout_formulario.addRow("Estoque de Segurança:", self.campo_estoque_seguranca)
        layout_formulario.addRow("Lote Mínimo:", self.campo_lote_minimo)
        layout_formulario.addRow("Saldo de Estoque:", self.campo_estoque_atual)
        layout_formulario.addRow("Centro de Trabalho:", self.campo_centro_trabalho)
        layout_formulario.addRow("Tempo Unitário (Roteiro):", self.campo_tempo_unitario)

        layout.addWidget(quadro_formulario)

        caixa_botoes = QHBoxLayout()
        caixa_botoes.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "btn-secondary")
        btn_cancelar.clicked.connect(self.reject)

        btn_salvar = QPushButton("Salvar Item")
        btn_salvar.setProperty("class", "btn-primary")
        btn_salvar.clicked.connect(self.salvar_item)

        caixa_botoes.addWidget(btn_cancelar)
        caixa_botoes.addWidget(btn_salvar)
        layout.addLayout(caixa_botoes)

        if self.item:
            self.campo_codigo.setText(self.item.codigo)
            self.campo_codigo.setEnabled(False)
            self.campo_tipo.setCurrentText(self.item.tipo_item)
            self.campo_tipo.setEnabled(False)
            self.campo_descricao.setText(self.item.descricao)
            self.campo_unidade.setText(self.item.unidade)
            self.campo_custo.setValue(self.item.custo_unitario)
            self.campo_lead_time.setValue(self.item.lead_time)
            self.campo_estoque_seguranca.setValue(self.item.estoque_seguranca)
            self.campo_lote_minimo.setValue(self.item.lote_minimo)
            self.campo_estoque_atual.setValue(self.item.estoque_atual)
            self.campo_estoque_atual.setEnabled(False)
            self.campo_tempo_unitario.setValue(self.item.tempo_unitario)

            if self.item.codigo_centro_trabalho:
                for idx in range(self.campo_centro_trabalho.count()):
                    if self.campo_centro_trabalho.itemData(idx) == self.item.codigo_centro_trabalho:
                        self.campo_centro_trabalho.setCurrentIndex(idx)
                        break

        self.ao_mudar_tipo(self.campo_tipo.currentText())

    def ao_mudar_tipo(self, tipo_selecionado):
        eh_mp = tipo_selecionado == "MP"
        self.campo_centro_trabalho.setEnabled(not eh_mp)
        self.campo_tempo_unitario.setEnabled(not eh_mp)
        if eh_mp:
            self.campo_centro_trabalho.setCurrentIndex(0)
            self.campo_tempo_unitario.setValue(0.0)

    def salvar_item(self):
        dados = {
            "codigo": self.campo_codigo.text().strip(),
            "tipo_item": self.campo_tipo.currentText(),
            "descricao": self.campo_descricao.text().strip(),
            "unidade": self.campo_unidade.text().strip(),
            "custo_unitario": self.campo_custo.value(),
            "lead_time": self.campo_lead_time.value(),
            "estoque_seguranca": self.campo_estoque_seguranca.value(),
            "lote_minimo": self.campo_lote_minimo.value(),
            "estoque_atual": self.campo_estoque_atual.value(),
            "codigo_centro_trabalho": self.campo_centro_trabalho.currentData(),
            "tempo_unitario": self.campo_tempo_unitario.value(),
        }
        try:
            if self.item:
                atualizar_item(self.item.codigo, dados)
            else:
                criar_item(dados)
            self.accept()
        except ErroRegraNegocio as erro_regra:
            QMessageBox.warning(self, "Regra de Negócio", str(erro_regra))
        except ErroValidacao as erro_val:
            QMessageBox.warning(self, "Validação", str(erro_val))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro inesperado: {exc}")


class VisaoItens(QWidget):
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
        titulo = QLabel("Cadastro e Gestão de Itens")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel("Gerenciamento de Produtos Acabados (PA), Semiacabados (SA) e Matérias-Primas (MP)")
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_novo = QPushButton("Novo Item")
        btn_novo.setProperty("class", "btn-primary")
        btn_novo.clicked.connect(self.ao_clicar_novo_item)
        cabecalho.addWidget(btn_novo)

        layout.addLayout(cabecalho)

        barra_filtros = QFrame()
        barra_filtros.setProperty("class", "card")
        layout_filtros = QHBoxLayout(barra_filtros)
        layout_filtros.setContentsMargins(14, 10, 14, 10)

        rotulo_filtro = QLabel("Filtro:")
        rotulo_filtro.setStyleSheet("font-weight: 600; color: #475569;")
        layout_filtros.addWidget(rotulo_filtro)

        self.filtro_tipo = QComboBox()
        self.filtro_tipo.addItems([
            "Todos os Tipos", "PA - Produto Acabado", "SA - Semiacabado", "MP - Matéria-Prima"
        ])
        self.filtro_tipo.currentIndexChanged.connect(self.atualizar_tabela)
        layout_filtros.addWidget(self.filtro_tipo)

        rotulo_busca = QLabel("Buscar:")
        rotulo_busca.setStyleSheet("font-weight: 600; color: #475569;")
        layout_filtros.addWidget(rotulo_busca)

        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("Buscar por código ou descrição...")
        self.campo_busca.textChanged.connect(self.atualizar_tabela)
        layout_filtros.addWidget(self.campo_busca)

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(self.atualizar_dados)
        layout_filtros.addWidget(btn_atualizar)

        layout.addWidget(barra_filtros)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(11)
        self.tabela.setHorizontalHeaderLabels([
            "Código", "Tipo", "Descrição", "Unidade", "Custo Unit.", "Lead Time",
            "Est. Segurança", "Lote Mín.", "Saldo Atual", "Centro Trab.", "Tempo Unit."
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.doubleClicked.connect(self.ao_clicar_editar_item)
        layout.addWidget(self.tabela)

        linha_botoes = QHBoxLayout()
        btn_editar = QPushButton("Editar Item")
        btn_editar.setProperty("class", "btn-secondary")
        btn_editar.clicked.connect(self.ao_clicar_editar_item)
        linha_botoes.addWidget(btn_editar)

        btn_excluir = QPushButton("Excluir Item")
        btn_excluir.setProperty("class", "btn-danger")
        btn_excluir.clicked.connect(self.ao_clicar_excluir_item)
        linha_botoes.addWidget(btn_excluir)

        linha_botoes.addStretch()
        layout.addLayout(linha_botoes)

    def atualizar_dados(self):
        self.atualizar_tabela()
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def atualizar_tabela(self):
        texto_filtro = self.filtro_tipo.currentText()
        tipo_filtro = None
        if "PA" in texto_filtro:
            tipo_filtro = "PA"
        elif "SA" in texto_filtro:
            tipo_filtro = "SA"
        elif "MP" in texto_filtro:
            tipo_filtro = "MP"

        termo_busca = self.campo_busca.text().strip().lower()
        itens = listar_itens(tipo_item=tipo_filtro)

        if termo_busca:
            itens = [
                item for item in itens
                if termo_busca in item.codigo.lower() or termo_busca in item.descricao.lower()
            ]

        self.tabela.setRowCount(len(itens))
        for linha_idx, item in enumerate(itens):
            self.tabela.setItem(linha_idx, 0, QTableWidgetItem(item.codigo))

            tipo_item_widget = QTableWidgetItem(item.tipo_item)
            tipo_item_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha_idx, 1, tipo_item_widget)

            self.tabela.setItem(linha_idx, 2, QTableWidgetItem(item.descricao))

            unidade_widget = QTableWidgetItem(item.unidade)
            unidade_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha_idx, 3, unidade_widget)

            custo_widget = QTableWidgetItem(f"R$ {item.custo_unitario:.2f}")
            custo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(linha_idx, 4, custo_widget)

            lt_widget = QTableWidgetItem(f"{item.lead_time} sem")
            lt_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha_idx, 5, lt_widget)

            es_widget = QTableWidgetItem(f"{item.estoque_seguranca:.1f}")
            es_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(linha_idx, 6, es_widget)

            lm_widget = QTableWidgetItem(f"{item.lote_minimo:.1f}")
            lm_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(linha_idx, 7, lm_widget)

            saldo_widget = QTableWidgetItem(f"{item.estoque_atual:.1f}")
            saldo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if item.estoque_atual < item.estoque_seguranca:
                saldo_widget.setForeground(Qt.red)
            self.tabela.setItem(linha_idx, 8, saldo_widget)

            centro_widget = QTableWidgetItem(item.codigo_centro_trabalho or "-")
            centro_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha_idx, 9, centro_widget)

            tempo_widget = QTableWidgetItem(f"{item.tempo_unitario:.2f} h" if item.tempo_unitario else "-")
            tempo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(linha_idx, 10, tempo_widget)

        self.tabela.resizeColumnsToContents()
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def ao_clicar_novo_item(self):
        dialogo = DialogoItem(self)
        if dialogo.exec():
            self.atualizar_tabela()
            self.dados_modificados.emit()

    def ao_clicar_editar_item(self):
        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.information(self, "Aviso", "Selecione um item na tabela para editar.")
            return

        item_codigo = self.tabela.item(linha_selecionada, 0)
        if not item_codigo:
            return

        codigo = item_codigo.text()
        try:
            item = obter_item(codigo)
            dialogo = DialogoItem(self, item=item)
            if dialogo.exec():
                self.atualizar_tabela()
                self.dados_modificados.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar item: {exc}")

    def ao_clicar_excluir_item(self):
        linha_selecionada = self.tabela.currentRow()
        if linha_selecionada < 0:
            QMessageBox.information(self, "Aviso", "Selecione um item na tabela para excluir.")
            return

        item_codigo = self.tabela.item(linha_selecionada, 0)
        if not item_codigo:
            return
        codigo = item_codigo.text()

        if confirmar_acao(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir o item '{codigo}'?",
        ):
            try:
                excluir_item(codigo)
                self.atualizar_tabela()
                self.dados_modificados.emit()
                QMessageBox.information(self, "Sucesso", f"Item '{codigo}' excluído com sucesso.")
            except ErroRegraNegocio as erro_regra:
                QMessageBox.warning(self, "Aviso", str(erro_regra))
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir item: {exc}")


ItemsView = VisaoItens
ItemDialog = DialogoItem
