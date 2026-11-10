from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
)
from backend.services.item_service import listar_itens
from backend.services.bom_service import (
    explodir_arvore_estrutura,
    adicionar_componente_estrutura,
    remover_componente_estrutura,
)
from backend.exceptions import ErroRegraNegocio
from frontend.animations import animar_surgimento_widget
from frontend.dialogs import confirmar_acao


class VisaoEstrutura(QWidget):
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
        titulo = QLabel("Estrutura de Produto (BOM) e Explosão Multinível")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Gestão da lista de materiais em até 3 níveis (PA -> SA -> MP) com prevenção de ciclos (RN03)"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        layout.addLayout(cabecalho)

        barra_superior = QFrame()
        barra_superior.setProperty("class", "card")
        layout_barra = QHBoxLayout(barra_superior)
        layout_barra.setContentsMargins(14, 10, 14, 10)

        rotulo_selecao = QLabel("Item Fabricado (Pai):")
        rotulo_selecao.setStyleSheet("font-weight: 700; color: #334155;")
        layout_barra.addWidget(rotulo_selecao)

        self.combo_pais = QComboBox()
        self.combo_pais.currentIndexChanged.connect(self.ao_selecionar_pai)
        layout_barra.addWidget(self.combo_pais, 1)

        rotulo_multiplicador = QLabel("Qtd Lote / Multiplicador:")
        rotulo_multiplicador.setStyleSheet("font-weight: 600; color: #475569;")
        layout_barra.addWidget(rotulo_multiplicador)

        self.campo_multiplicador = QDoubleSpinBox()
        self.campo_multiplicador.setRange(1.0, 10000.0)
        self.campo_multiplicador.setValue(1.0)
        self.campo_multiplicador.valueChanged.connect(self.ao_mudar_multiplicador)
        layout_barra.addWidget(self.campo_multiplicador)

        btn_atualizar = QPushButton("Atualizar Árvore")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(self.atualizar_arvore)
        layout_barra.addWidget(btn_atualizar)

        layout.addWidget(barra_superior)

        layout_conteudo = QHBoxLayout()
        layout_conteudo.setSpacing(16)

        quadro_arvore = QFrame()
        quadro_arvore.setProperty("class", "card")
        layout_arvore = QVBoxLayout(quadro_arvore)

        rotulo_arvore = QLabel("Explosão da Estrutura (BOM)")
        rotulo_arvore.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_arvore.addWidget(rotulo_arvore)

        self.arvore = QTreeWidget()
        self.arvore.setColumnCount(6)
        self.arvore.setHeaderLabels([
            "Estrutura / Item", "Nível", "Tipo", "Qtd por Pai", "Qtd Total Acumulada", "Unidade"
        ])
        self.arvore.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.arvore.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.arvore.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.arvore.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.arvore.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.arvore.header().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        layout_arvore.addWidget(self.arvore)

        btn_remover_componente = QPushButton("Remover Componente")
        btn_remover_componente.setProperty("class", "btn-danger")
        btn_remover_componente.clicked.connect(self.ao_clicar_remover_componente)
        layout_arvore.addWidget(btn_remover_componente)

        layout_conteudo.addWidget(quadro_arvore, 3)

        quadro_formulario = QFrame()
        quadro_formulario.setProperty("class", "card")
        layout_formulario = QVBoxLayout(quadro_formulario)

        rotulo_adicionar = QLabel("Adicionar Componente à BOM")
        rotulo_adicionar.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_formulario.addWidget(rotulo_adicionar)

        rotulo_pai = QLabel("Item Pai (Fabricado):")
        rotulo_pai.setStyleSheet("font-weight: 600; color: #475569;")
        layout_formulario.addWidget(rotulo_pai)
        self.combo_formulario_pai = QComboBox()
        self.combo_formulario_pai.currentIndexChanged.connect(self.ao_mudar_formulario_pai)
        layout_formulario.addWidget(self.combo_formulario_pai)

        rotulo_comp = QLabel("Componente a Inserir:")
        rotulo_comp.setStyleSheet("font-weight: 600; color: #475569;")
        layout_formulario.addWidget(rotulo_comp)
        self.combo_formulario_componente = QComboBox()
        layout_formulario.addWidget(self.combo_formulario_componente)

        rotulo_qtd = QLabel("Quantidade por Unidade:")
        rotulo_qtd.setStyleSheet("font-weight: 600; color: #475569;")
        layout_formulario.addWidget(rotulo_qtd)
        self.campo_formulario_quantidade = QDoubleSpinBox()
        self.campo_formulario_quantidade.setRange(0.01, 10000.0)
        self.campo_formulario_quantidade.setDecimals(2)
        self.campo_formulario_quantidade.setValue(1.0)
        layout_formulario.addWidget(self.campo_formulario_quantidade)

        quadro_regras = QFrame()
        quadro_regras.setStyleSheet(
            "background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 10px;"
        )
        layout_regras = QVBoxLayout(quadro_regras)
        texto_regras = QLabel(
            "Regras de Negócio (RN03):\n"
            "• Máximo 3 níveis de profundidade\n"
            "• PA pode conter SA e MP\n"
            "• SA só pode conter MP\n"
            "• MP não possui componentes"
        )
        texto_regras.setStyleSheet("color: #1E40AF; font-size: 11px; line-height: 14px;")
        layout_regras.addWidget(texto_regras)
        layout_formulario.addWidget(quadro_regras)

        btn_adicionar = QPushButton("Adicionar Componente")
        btn_adicionar.setProperty("class", "btn-primary")
        btn_adicionar.clicked.connect(self.ao_clicar_adicionar_componente)
        layout_formulario.addWidget(btn_adicionar)

        layout_formulario.addStretch()
        layout_conteudo.addWidget(quadro_formulario, 2)

        layout.addLayout(layout_conteudo)

    def atualizar_dados(self):
        codigo_atual = self.combo_pais.currentData()
        self.combo_pais.blockSignals(True)
        self.combo_pais.clear()
        self.combo_formulario_pai.clear()

        pais = listar_itens(tipo_item="PA") + listar_itens(tipo_item="SA")
        for item in pais:
            rotulo = f"{item.codigo} - {item.descricao} ({item.tipo_item})"
            self.combo_pais.addItem(rotulo, item.codigo)
            self.combo_formulario_pai.addItem(rotulo, item.codigo)

        if codigo_atual:
            indice = self.combo_pais.findData(codigo_atual)
            if indice >= 0:
                self.combo_pais.setCurrentIndex(indice)

        self.combo_pais.blockSignals(False)
        self.ao_mudar_formulario_pai()
        self.atualizar_arvore()
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def ao_selecionar_pai(self):
        self.atualizar_arvore()

    def ao_mudar_multiplicador(self):
        self.atualizar_arvore()

    def ao_mudar_formulario_pai(self):
        codigo_pai = self.combo_formulario_pai.currentData()
        self.combo_formulario_componente.clear()
        if not codigo_pai:
            return

        eh_pa = codigo_pai.startswith("PA")
        componentes = []
        if eh_pa:
            componentes = listar_itens(tipo_item="SA") + listar_itens(tipo_item="MP")
        else:
            componentes = listar_itens(tipo_item="MP")

        for item in componentes:
            if item.codigo != codigo_pai:
                rotulo = f"{item.codigo} - {item.descricao} ({item.tipo_item})"
                self.combo_formulario_componente.addItem(rotulo, item.codigo)

    def atualizar_arvore(self):
        self.arvore.clear()
        codigo_pai = self.combo_pais.currentData()
        if not codigo_pai:
            return

        multiplicador = self.campo_multiplicador.value()

        try:
            no_raiz = explodir_arvore_estrutura(codigo_pai, multiplicador=multiplicador)
            item_raiz = QTreeWidgetItem(self.arvore)
            item_raiz.setText(0, f"[{no_raiz.tipo_item}] {no_raiz.codigo_item} - {no_raiz.descricao}")
            item_raiz.setText(1, f"Nível {no_raiz.nivel}")
            item_raiz.setText(2, no_raiz.tipo_item)
            item_raiz.setText(3, f"{no_raiz.quantidade_por_pai:.1f}")
            item_raiz.setText(4, f"{no_raiz.quantidade_total:.1f}")
            item_raiz.setText(5, no_raiz.unidade)

            fonte_raiz = QFont()
            fonte_raiz.setBold(True)
            for col in range(6):
                item_raiz.setFont(col, fonte_raiz)
                item_raiz.setForeground(col, QColor("#1D4ED8"))

            item_raiz.setTextAlignment(1, Qt.AlignCenter)
            item_raiz.setTextAlignment(2, Qt.AlignCenter)
            item_raiz.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
            item_raiz.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)
            item_raiz.setTextAlignment(5, Qt.AlignCenter)
            item_raiz.setData(0, Qt.UserRole, (None, no_raiz.codigo_item))
            item_raiz.setExpanded(True)

            def popular_filhos(item_interface_pai, filhos, codigo_pai_atual):
                for filho in filhos:
                    item_filho = QTreeWidgetItem(item_interface_pai)
                    cor_texto = "#B45309" if filho.tipo_item == "SA" else "#047857"
                    item_filho.setText(0, f"[{filho.tipo_item}] {filho.codigo_item} - {filho.descricao}")
                    item_filho.setText(1, f"Nível {filho.nivel}")
                    item_filho.setText(2, filho.tipo_item)
                    item_filho.setText(3, f"{filho.quantidade_por_pai:.2f}")
                    item_filho.setText(4, f"{filho.quantidade_total:.2f}")
                    item_filho.setText(5, filho.unidade)

                    fonte_filho = QFont()
                    if filho.tipo_item == "SA":
                        fonte_filho.setBold(True)
                    for col in range(6):
                        item_filho.setFont(col, fonte_filho)
                        item_filho.setForeground(col, QColor(cor_texto))

                    item_filho.setTextAlignment(1, Qt.AlignCenter)
                    item_filho.setTextAlignment(2, Qt.AlignCenter)
                    item_filho.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
                    item_filho.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)
                    item_filho.setTextAlignment(5, Qt.AlignCenter)
                    item_filho.setData(0, Qt.UserRole, (codigo_pai_atual, filho.codigo_item))
                    item_filho.setExpanded(True)
                    if filho.filhos:
                        popular_filhos(item_filho, filho.filhos, filho.codigo_item)

            popular_filhos(item_raiz, no_raiz.filhos, no_raiz.codigo_item)

        except Exception as excecao:
            QMessageBox.critical(self, "Erro na Explosão", f"Falha ao explodir a BOM: {excecao}")

    def ao_clicar_adicionar_componente(self):
        codigo_pai = self.combo_formulario_pai.currentData()
        codigo_comp = self.combo_formulario_componente.currentData()
        quantidade = self.campo_formulario_quantidade.value()

        if not codigo_pai or not codigo_comp:
            QMessageBox.warning(self, "Aviso", "Selecione o item pai e o componente.")
            return

        try:
            adicionar_componente_estrutura(codigo_pai, codigo_comp, quantidade)
            self.atualizar_arvore()
            self.dados_modificados.emit()
            QMessageBox.information(
                self, "Sucesso", f"Componente {codigo_comp} adicionado ao pai {codigo_pai}."
            )
        except ErroRegraNegocio as erro_regra:
            QMessageBox.warning(self, "Regra de Negócio (RN03)", str(erro_regra))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao adicionar componente: {exc}")

    def ao_clicar_remover_componente(self):
        item_atual = self.arvore.currentItem()
        if not item_atual:
            QMessageBox.information(self, "Aviso", "Selecione um componente na árvore para remover.")
            return

        dados = item_atual.data(0, Qt.UserRole)
        if not dados or not dados[0]:
            QMessageBox.information(self, "Aviso", "O item raiz não pode ser removido da própria estrutura.")
            return

        codigo_pai, codigo_comp = dados
        if confirmar_acao(
            self,
            "Confirmar Remoção",
            f"Deseja remover o componente '{codigo_comp}' do item pai '{codigo_pai}'?",
        ):
            try:
                remover_componente_estrutura(codigo_pai, codigo_comp)
                self.atualizar_arvore()
                self.dados_modificados.emit()
                QMessageBox.information(self, "Sucesso", "Componente removido com sucesso.")
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Falha ao remover componente: {exc}")


BOMView = VisaoEstrutura
