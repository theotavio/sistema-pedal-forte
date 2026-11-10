from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDoubleSpinBox,
    QComboBox,
    QMessageBox,
    QFrame,
)
from backend.services.work_center_service import (
    listar_centros_trabalho,
    criar_centro_trabalho,
    atualizar_centro_trabalho,
    excluir_centro_trabalho,
    obter_centro_trabalho,
    definir_roteiro_item,
)
from backend.services.item_service import listar_itens
from backend.exceptions import ErroRegraNegocio
from frontend.animations import animar_surgimento_widget
from frontend.dialogs import confirmar_acao


class DialogoCentroTrabalho(QDialog):
    def __init__(self, parent=None, centro_trabalho=None):
        super().__init__(parent)
        self.centro = centro_trabalho
        self.setWindowTitle("Editar Centro de Trabalho" if centro_trabalho else "Novo Centro de Trabalho")
        self.resize(460, 290)
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        quadro = QFrame()
        quadro.setProperty("class", "card")
        formulario = QFormLayout(quadro)

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText("Ex: CT-01, CT-02")

        self.campo_nome = QLineEdit()
        self.campo_nome.setPlaceholderText("Ex: Solda de Quadros, Montagem Final")

        self.campo_capacidade = QDoubleSpinBox()
        self.campo_capacidade.setRange(1.0, 1000.0)
        self.campo_capacidade.setValue(40.0)
        self.campo_capacidade.setSuffix(" h/sem")

        self.campo_custo = QDoubleSpinBox()
        self.campo_custo.setRange(0.0, 10000.0)
        self.campo_custo.setValue(80.0)
        self.campo_custo.setPrefix("R$ ")
        self.campo_custo.setSuffix(" / h")

        formulario.addRow("Código do Centro (RF06):", self.campo_codigo)
        formulario.addRow("Nome do Centro:", self.campo_nome)
        formulario.addRow("Capacidade Semanal:", self.campo_capacidade)
        formulario.addRow("Custo da Hora-Máquina:", self.campo_custo)

        layout.addWidget(quadro)

        caixa_botoes = QHBoxLayout()
        caixa_botoes.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "btn-secondary")
        btn_cancelar.clicked.connect(self.reject)

        btn_salvar = QPushButton("Salvar")
        btn_salvar.setProperty("class", "btn-primary")
        btn_salvar.clicked.connect(self.salvar)

        caixa_botoes.addWidget(btn_cancelar)
        caixa_botoes.addWidget(btn_salvar)
        layout.addLayout(caixa_botoes)

        if self.centro:
            self.campo_codigo.setText(self.centro.codigo)
            self.campo_codigo.setEnabled(False)
            self.campo_nome.setText(self.centro.nome)
            self.campo_capacidade.setValue(self.centro.capacidade_horas_semana)
            self.campo_custo.setValue(self.centro.custo_hora)

    def salvar(self):
        codigo = self.campo_codigo.text().strip().upper()
        nome = self.campo_nome.text().strip()
        capacidade = self.campo_capacidade.value()
        custo = self.campo_custo.value()

        try:
            if self.centro:
                atualizar_centro_trabalho(codigo, nome, capacidade, custo)
            else:
                criar_centro_trabalho(codigo, nome, capacidade, custo)
            self.accept()
        except ErroRegraNegocio as erro_regra:
            QMessageBox.warning(self, "Aviso", str(erro_regra))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar: {exc}")


class VisaoCentrosTrabalho(QWidget):
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
        titulo = QLabel("Centros de Trabalho e Roteiros de Fabricação")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel("Gestão de capacidade em horas/semana, custo-hora e amarração de roteiros (RF06)")
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_novo = QPushButton("Novo Centro de Trabalho")
        btn_novo.setProperty("class", "btn-primary")
        btn_novo.clicked.connect(self.ao_clicar_novo_centro)
        cabecalho.addWidget(btn_novo)

        layout.addLayout(cabecalho)

        secao_superior = QFrame()
        secao_superior.setProperty("class", "card")
        layout_superior = QVBoxLayout(secao_superior)

        rotulo_titulo_ct = QLabel("Centros de Trabalho Cadastrados")
        rotulo_titulo_ct.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_superior.addWidget(rotulo_titulo_ct)

        self.tabela_ct = QTableWidget()
        self.tabela_ct.setColumnCount(4)
        self.tabela_ct.setHorizontalHeaderLabels([
            "Código", "Nome do Centro", "Capacidade Semanal", "Custo / Hora"
        ])
        self.tabela_ct.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_ct.verticalHeader().setVisible(False)
        self.tabela_ct.setAlternatingRowColors(True)
        self.tabela_ct.setSelectionBehavior(QTableWidget.SelectRows)
        layout_superior.addWidget(self.tabela_ct)

        barra_botoes_ct = QHBoxLayout()
        btn_editar_ct = QPushButton("Editar Centro")
        btn_editar_ct.setProperty("class", "btn-secondary")
        btn_editar_ct.clicked.connect(self.ao_clicar_editar_centro)
        barra_botoes_ct.addWidget(btn_editar_ct)

        btn_excluir_ct = QPushButton("Excluir Centro")
        btn_excluir_ct.setProperty("class", "btn-danger")
        btn_excluir_ct.clicked.connect(self.ao_clicar_excluir_centro)
        barra_botoes_ct.addWidget(btn_excluir_ct)

        barra_botoes_ct.addStretch()
        layout_superior.addLayout(barra_botoes_ct)
        layout.addWidget(secao_superior, 1)

        secao_inferior = QFrame()
        secao_inferior.setProperty("class", "card")
        layout_inferior = QVBoxLayout(secao_inferior)

        rotulo_titulo_roteiro = QLabel("Roteiro de Fabricação (Itens Fabricados PA e SA)")
        rotulo_titulo_roteiro.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_inferior.addWidget(rotulo_titulo_roteiro)

        barra_formulario_roteiro = QHBoxLayout()
        rotulo_item = QLabel("Item Fabricado:")
        rotulo_item.setStyleSheet("font-weight: 600; color: #475569;")
        barra_formulario_roteiro.addWidget(rotulo_item)

        self.combo_item = QComboBox()
        barra_formulario_roteiro.addWidget(self.combo_item, 2)

        rotulo_alvo_ct = QLabel("Centro Responsável:")
        rotulo_alvo_ct.setStyleSheet("font-weight: 600; color: #475569;")
        barra_formulario_roteiro.addWidget(rotulo_alvo_ct)

        self.combo_ct_alvo = QComboBox()
        barra_formulario_roteiro.addWidget(self.combo_ct_alvo, 2)

        rotulo_tempo = QLabel("Tempo por Unidade:")
        rotulo_tempo.setStyleSheet("font-weight: 600; color: #475569;")
        barra_formulario_roteiro.addWidget(rotulo_tempo)

        self.campo_tempo_unitario = QDoubleSpinBox()
        self.campo_tempo_unitario.setRange(0.01, 1000.0)
        self.campo_tempo_unitario.setValue(1.0)
        self.campo_tempo_unitario.setSuffix(" horas")
        barra_formulario_roteiro.addWidget(self.campo_tempo_unitario, 1)

        btn_salvar_roteiro = QPushButton("Salvar Roteiro")
        btn_salvar_roteiro.setProperty("class", "btn-primary")
        btn_salvar_roteiro.clicked.connect(self.ao_clicar_salvar_roteiro)
        barra_formulario_roteiro.addWidget(btn_salvar_roteiro)

        layout_inferior.addLayout(barra_formulario_roteiro)

        self.tabela_roteiros = QTableWidget()
        self.tabela_roteiros.setColumnCount(5)
        self.tabela_roteiros.setHorizontalHeaderLabels([
            "Código do Item", "Descrição", "Tipo", "Centro de Trabalho", "Tempo Unitário (h)"
        ])
        self.tabela_roteiros.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_roteiros.verticalHeader().setVisible(False)
        self.tabela_roteiros.setAlternatingRowColors(True)
        layout_inferior.addWidget(self.tabela_roteiros)

        layout.addWidget(secao_inferior, 1)

    def atualizar_dados(self):
        centros = listar_centros_trabalho()
        self.tabela_ct.setRowCount(len(centros))
        for linha_idx, centro in enumerate(centros):
            self.tabela_ct.setItem(linha_idx, 0, QTableWidgetItem(centro.codigo))
            self.tabela_ct.setItem(linha_idx, 1, QTableWidgetItem(centro.nome))

            cap_widget = QTableWidgetItem(f"{centro.capacidade_horas_semana:.1f} h/sem")
            cap_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_ct.setItem(linha_idx, 2, cap_widget)

            custo_widget = QTableWidgetItem(f"R$ {centro.custo_hora:.2f}")
            custo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_ct.setItem(linha_idx, 3, custo_widget)

        self.combo_ct_alvo.clear()
        for centro in centros:
            self.combo_ct_alvo.addItem(f"{centro.codigo} - {centro.nome}", centro.codigo)

        fabricados = listar_itens(tipo_item="PA") + listar_itens(tipo_item="SA")
        self.combo_item.clear()
        for item in fabricados:
            self.combo_item.addItem(f"{item.codigo} - {item.descricao} ({item.tipo_item})", item.codigo)

        self.tabela_roteiros.setRowCount(len(fabricados))
        for linha_idx, item in enumerate(fabricados):
            self.tabela_roteiros.setItem(linha_idx, 0, QTableWidgetItem(item.codigo))
            self.tabela_roteiros.setItem(linha_idx, 1, QTableWidgetItem(item.descricao))

            tipo_widget = QTableWidgetItem(item.tipo_item)
            tipo_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela_roteiros.setItem(linha_idx, 2, tipo_widget)

            ct_widget = QTableWidgetItem(item.codigo_centro_trabalho or "Nenhum")
            ct_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela_roteiros.setItem(linha_idx, 3, ct_widget)

            tempo_widget = QTableWidgetItem(f"{item.tempo_unitario:.2f} h" if item.tempo_unitario else "-")
            tempo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_roteiros.setItem(linha_idx, 4, tempo_widget)

        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def ao_clicar_novo_centro(self):
        dialogo = DialogoCentroTrabalho(self)
        if dialogo.exec():
            self.atualizar_dados()
            self.dados_modificados.emit()

    def ao_clicar_editar_centro(self):
        linha = self.tabela_ct.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um centro de trabalho na tabela.")
            return
        codigo = self.tabela_ct.item(linha, 0).text()
        try:
            centro = obter_centro_trabalho(codigo)
            dialogo = DialogoCentroTrabalho(self, centro_trabalho=centro)
            if dialogo.exec():
                self.atualizar_dados()
                self.dados_modificados.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar centro: {exc}")

    def ao_clicar_excluir_centro(self):
        linha = self.tabela_ct.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Aviso", "Selecione um centro de trabalho para excluir.")
            return
        codigo = self.tabela_ct.item(linha, 0).text()
        if confirmar_acao(
            self,
            "Confirmar Exclusão",
            f"Deseja excluir o centro de trabalho '{codigo}'?",
        ):
            try:
                excluir_centro_trabalho(codigo)
                self.atualizar_dados()
                self.dados_modificados.emit()
                QMessageBox.information(self, "Sucesso", "Centro excluído.")
            except ErroRegraNegocio as erro_regra:
                QMessageBox.warning(self, "Aviso", str(erro_regra))
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir: {exc}")

    def ao_clicar_salvar_roteiro(self):
        codigo_item = self.combo_item.currentData()
        codigo_ct = self.combo_ct_alvo.currentData()
        tempo_un = self.campo_tempo_unitario.value()

        if not codigo_item or not codigo_ct:
            QMessageBox.warning(self, "Aviso", "Selecione o item e o centro de trabalho.")
            return

        try:
            definir_roteiro_item(codigo_item, codigo_ct, tempo_un)
            QMessageBox.information(self, "Sucesso", f"Roteiro atualizado para o item {codigo_item}.")
            self.atualizar_dados()
            self.dados_modificados.emit()
        except ErroRegraNegocio as erro_regra:
            QMessageBox.warning(self, "Aviso", str(erro_regra))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar roteiro: {exc}")


WorkCentersView = VisaoCentrosTrabalho
WorkCenterDialog = DialogoCentroTrabalho
