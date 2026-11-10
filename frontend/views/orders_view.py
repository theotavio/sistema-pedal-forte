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
    QMessageBox,
    QFrame,
)
from backend.services.order_service import (
    listar_ordens,
    firmar_ordem,
    liberar_ordem,
    encerrar_ordem,
    apontar_producao,
    receber_ordem_compra,
    obter_ordem,
)
from backend.exceptions import ErroRegraNegocio
from frontend.animations import animar_surgimento_widget
from frontend.dialogs import confirmar_acao


class VisaoOrdens(QWidget):
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
        titulo = QLabel("Gestão de Ordens de Produção (OP) e Compra (OC)")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Fluxo de ordens (RF10) e apontamento de produção com baixa na BOM (RF11)"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(self.atualizar_dados)
        cabecalho.addWidget(btn_atualizar)

        layout.addLayout(cabecalho)

        barra_filtros = QFrame()
        barra_filtros.setProperty("class", "card")
        layout_filtros = QHBoxLayout(barra_filtros)
        layout_filtros.setContentsMargins(14, 10, 14, 10)

        rotulo_tipo = QLabel("Tipo:")
        rotulo_tipo.setStyleSheet("font-weight: 600; color: #475569;")
        layout_filtros.addWidget(rotulo_tipo)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems([
            "Todos os Tipos", "OP - Ordem de Produção", "OC - Ordem de Compra"
        ])
        self.combo_tipo.currentIndexChanged.connect(self.atualizar_tabela)
        layout_filtros.addWidget(self.combo_tipo)

        rotulo_status = QLabel("Status:")
        rotulo_status.setStyleSheet("font-weight: 600; color: #475569;")
        layout_filtros.addWidget(rotulo_status)

        self.combo_status = QComboBox()
        self.combo_status.addItems([
            "Todos os Status", "PLANEJADA", "FIRME", "LIBERADA", "ENCERRADA", "ATRASADA"
        ])
        self.combo_status.currentIndexChanged.connect(self.atualizar_tabela)
        layout_filtros.addWidget(self.combo_status)

        rotulo_busca = QLabel("Buscar:")
        rotulo_busca.setStyleSheet("font-weight: 600; color: #475569;")
        layout_filtros.addWidget(rotulo_busca)

        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText("Filtrar por código ou descrição...")
        self.campo_busca.textChanged.connect(self.atualizar_tabela)
        layout_filtros.addWidget(self.campo_busca)

        layout.addWidget(barra_filtros)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(10)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Tipo", "Código", "Descrição", "Quantidade",
            "Sem. Liberação", "Sem. Entrega", "Status", "Atrasada?", "Tipo Item"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.itemSelectionChanged.connect(self.atualizar_botoes_acao)
        layout.addWidget(self.tabela)

        barra_acoes = QFrame()
        barra_acoes.setProperty("class", "card")
        layout_acoes = QHBoxLayout(barra_acoes)
        layout_acoes.setContentsMargins(14, 10, 14, 10)
        layout_acoes.setSpacing(10)

        self.btn_firmar = QPushButton("Firmar")
        self.btn_firmar.setProperty("class", "btn-secondary")
        self.btn_firmar.clicked.connect(self.ao_clicar_firmar)
        layout_acoes.addWidget(self.btn_firmar)

        self.btn_liberar = QPushButton("Liberar")
        self.btn_liberar.setProperty("class", "btn-secondary")
        self.btn_liberar.clicked.connect(self.ao_clicar_liberar)
        layout_acoes.addWidget(self.btn_liberar)

        self.btn_apontar = QPushButton("Apontar Produção")
        self.btn_apontar.setProperty("class", "btn-success")
        self.btn_apontar.clicked.connect(self.ao_clicar_apontar_producao)
        layout_acoes.addWidget(self.btn_apontar)

        self.btn_receber_oc = QPushButton("Receber Compra")
        self.btn_receber_oc.setProperty("class", "btn-primary")
        self.btn_receber_oc.clicked.connect(self.ao_clicar_receber_oc)
        layout_acoes.addWidget(self.btn_receber_oc)

        self.btn_encerrar = QPushButton("Encerrar")
        self.btn_encerrar.setProperty("class", "btn-secondary")
        self.btn_encerrar.clicked.connect(self.ao_clicar_encerrar)
        layout_acoes.addWidget(self.btn_encerrar)

        layout_acoes.addStretch()
        layout.addWidget(barra_acoes)

        self.atualizar_botoes_acao()

    def atualizar_dados(self):
        self.atualizar_tabela()
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def atualizar_tabela(self):
        texto_tipo = self.combo_tipo.currentText()
        tipo_filtro = "OP" if "OP" in texto_tipo else ("OC" if "OC" in texto_tipo else None)

        texto_status = self.combo_status.currentText()
        status_filtro = None if "Todos" in texto_status else texto_status

        termo_busca = self.campo_busca.text().strip().lower()

        ordens = listar_ordens(status=status_filtro, tipo_ordem=tipo_filtro)

        if termo_busca:
            ordens = [
                ordem for ordem in ordens
                if termo_busca in ordem["codigo_item"].lower() or termo_busca in ordem["descricao"].lower()
            ]

        self.tabela.blockSignals(True)
        self.tabela.setRowCount(len(ordens))
        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        for linha_idx, ordem in enumerate(ordens):
            self.tabela.setItem(linha_idx, 0, QTableWidgetItem(f"#{ordem['id']}"))

            tipo_widget = QTableWidgetItem(ordem["tipo_ordem"])
            tipo_widget.setTextAlignment(Qt.AlignCenter)
            tipo_widget.setFont(fonte_negrito)
            if ordem["tipo_ordem"] == "OP":
                tipo_widget.setBackground(QColor("#EFF6FF"))
                tipo_widget.setForeground(QColor("#1D4ED8"))
            else:
                tipo_widget.setBackground(QColor("#ECFDF5"))
                tipo_widget.setForeground(QColor("#047857"))
            self.tabela.setItem(linha_idx, 1, tipo_widget)

            self.tabela.setItem(linha_idx, 2, QTableWidgetItem(ordem["codigo_item"]))
            self.tabela.setItem(linha_idx, 3, QTableWidgetItem(ordem["descricao"]))

            qtd_widget = QTableWidgetItem(f"{ordem['quantidade']:.0f} {ordem['unidade']}")
            qtd_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(linha_idx, 4, qtd_widget)

            rel_widget = QTableWidgetItem(f"Semana {ordem['semana_liberacao']}")
            rel_widget.setTextAlignment(Qt.AlignCenter)
            if ordem["semana_liberacao"] < 1:
                rel_widget.setBackground(QColor("#FEE2E2"))
                rel_widget.setForeground(QColor("#DC2626"))
                rel_widget.setFont(fonte_negrito)
            self.tabela.setItem(linha_idx, 5, rel_widget)

            del_widget = QTableWidgetItem(f"Semana {ordem['semana_entrega']}")
            del_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha_idx, 6, del_widget)

            status_widget = QTableWidgetItem(ordem["status"])
            status_widget.setTextAlignment(Qt.AlignCenter)
            status_widget.setFont(fonte_negrito)
            if ordem["status"] == "PLANEJADA":
                status_widget.setBackground(QColor("#F1F5F9"))
                status_widget.setForeground(QColor("#475569"))
            elif ordem["status"] == "FIRME":
                status_widget.setBackground(QColor("#FEF3C7"))
                status_widget.setForeground(QColor("#92400E"))
            elif ordem["status"] == "LIBERADA":
                status_widget.setBackground(QColor("#DBEAFE"))
                status_widget.setForeground(QColor("#1E40AF"))
            elif ordem["status"] == "ENCERRADA":
                status_widget.setBackground(QColor("#DCFCE7"))
                status_widget.setForeground(QColor("#166534"))
            elif ordem["status"] == "ATRASADA":
                status_widget.setBackground(QColor("#FEE2E2"))
                status_widget.setForeground(QColor("#991B1B"))
            self.tabela.setItem(linha_idx, 7, status_widget)

            atrasada_bool = bool(ordem.get("atrasada"))
            atrasada_widget = QTableWidgetItem("SIM" if atrasada_bool else "NÃO")
            atrasada_widget.setTextAlignment(Qt.AlignCenter)
            if atrasada_bool:
                atrasada_widget.setBackground(QColor("#FEE2E2"))
                atrasada_widget.setForeground(QColor("#DC2626"))
                atrasada_widget.setFont(fonte_negrito)
            else:
                atrasada_widget.setForeground(QColor("#64748B"))
            self.tabela.setItem(linha_idx, 8, atrasada_widget)

            self.tabela.setItem(linha_idx, 9, QTableWidgetItem(ordem["tipo_item"]))

        self.tabela.resizeColumnsToContents()
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabela.blockSignals(False)
        self.atualizar_botoes_acao()

    def obter_id_ordem_selecionada(self):
        linha = self.tabela.currentRow()
        if linha < 0 or linha >= self.tabela.rowCount():
            return None
        item_id = self.tabela.item(linha, 0)
        if not item_id:
            return None
        texto_id = item_id.text().replace("#", "").strip()
        return int(texto_id) if texto_id.isdigit() else None

    def atualizar_botoes_acao(self):
        id_ordem = self.obter_id_ordem_selecionada()
        if not id_ordem:
            self.btn_firmar.setEnabled(False)
            self.btn_liberar.setEnabled(False)
            self.btn_apontar.setEnabled(False)
            self.btn_receber_oc.setEnabled(False)
            self.btn_encerrar.setEnabled(False)
            return

        try:
            dados_ordem = obter_ordem(id_ordem)
            st = dados_ordem["status"]
            tipo = dados_ordem["tipo_ordem"]

            self.btn_firmar.setEnabled(st in ("PLANEJADA", "ATRASADA"))
            self.btn_liberar.setEnabled(st == "FIRME")
            self.btn_apontar.setEnabled(st == "LIBERADA" and tipo == "OP")
            self.btn_receber_oc.setEnabled(st == "LIBERADA" and tipo == "OC")
            self.btn_encerrar.setEnabled(st == "LIBERADA")
        except Exception:
            pass

    def ao_clicar_firmar(self):
        id_ordem = self.obter_id_ordem_selecionada()
        if not id_ordem:
            QMessageBox.warning(self, "Aviso", "Selecione uma ordem na tabela para firmar.")
            return
        try:
            firmar_ordem(id_ordem)
            self.atualizar_tabela()
            self.dados_modificados.emit()
            QMessageBox.information(self, "Sucesso", f"Ordem #{id_ordem} firmada com sucesso.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao firmar ordem: {exc}")

    def ao_clicar_liberar(self):
        id_ordem = self.obter_id_ordem_selecionada()
        if not id_ordem:
            QMessageBox.warning(self, "Aviso", "Selecione uma ordem na tabela para liberar.")
            return
        try:
            liberar_ordem(id_ordem)
            self.atualizar_tabela()
            self.dados_modificados.emit()
            QMessageBox.information(self, "Sucesso", f"Ordem #{id_ordem} liberada com sucesso.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao liberar ordem: {exc}")

    def ao_clicar_encerrar(self):
        id_ordem = self.obter_id_ordem_selecionada()
        if not id_ordem:
            QMessageBox.warning(self, "Aviso", "Selecione uma ordem na tabela para encerrar.")
            return
        try:
            encerrar_ordem(id_ordem)
            self.atualizar_tabela()
            self.dados_modificados.emit()
            QMessageBox.information(self, "Sucesso", f"Ordem #{id_ordem} encerrada com sucesso.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao encerrar ordem: {exc}")

    def ao_clicar_apontar_producao(self):
        id_ordem = self.obter_id_ordem_selecionada()
        if not id_ordem:
            QMessageBox.warning(self, "Aviso", "Selecione uma ordem para apontar produção.")
            return

        if confirmar_acao(
            self,
            "Confirmar Apontamento de Produção (RF11)",
            f"Deseja apontar a produção total da OP #{id_ordem}?\n\n"
            "O sistema baixará todos os componentes necessários do estoque e dará entrada no produto acabado.",
        ):
            try:
                apontar_producao(id_ordem)
                self.atualizar_tabela()
                self.dados_modificados.emit()
                QMessageBox.information(
                    self,
                    "Apontamento Concluído",
                    f"Produção da OP #{id_ordem} apontada com sucesso!\n"
                    "Componentes consumidos e saldo do item produzido atualizado.",
                )
            except ErroRegraNegocio as erro_regra:
                QMessageBox.warning(self, "Apontamento Rejeitado (RF11 / RN02)", str(erro_regra))
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Falha no apontamento: {exc}")

    def ao_clicar_receber_oc(self):
        id_ordem = self.obter_id_ordem_selecionada()
        if not id_ordem:
            QMessageBox.warning(self, "Aviso", "Selecione uma ordem de compra para receber.")
            return

        if confirmar_acao(
            self,
            "Recebimento de Compra",
            f"Confirmar recebimento físico da OC #{id_ordem} e entrada no estoque?",
        ):
            try:
                receber_ordem_compra(id_ordem)
                self.atualizar_tabela()
                self.dados_modificados.emit()
                QMessageBox.information(self, "Sucesso", f"OC #{id_ordem} recebida e estoque atualizado.")
            except Exception as exc:
                QMessageBox.critical(self, "Erro", f"Falha no recebimento: {exc}")


OrdersView = VisaoOrdens
