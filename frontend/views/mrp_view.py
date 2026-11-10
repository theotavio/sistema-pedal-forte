from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
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
    QMessageBox,
    QFrame,
    QSplitter,
)
from backend.services.mrp_service import calcular_mrp
from backend.services.item_service import listar_itens
from frontend.animations import animar_surgimento_widget


class VisaoMRP(QWidget):
    dados_modificados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.registros_armazenados = {}
        self.excecoes_armazenadas = []
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        cabecalho = QHBoxLayout()
        textos = QVBoxLayout()
        titulo = QLabel("Cálculo MRP e Registro Semanal")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Explosão de necessidades brutas, estoque projetado e ordens planejadas nas 8 semanas (RF08)"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_executar = QPushButton("Executar Cálculo MRP")
        btn_executar.setProperty("class", "btn-primary")
        btn_executar.clicked.connect(self.executar_calculo_mrp)
        cabecalho.addWidget(btn_executar)

        layout.addLayout(cabecalho)

        barra_superior = QFrame()
        barra_superior.setProperty("class", "card")
        layout_barra = QHBoxLayout(barra_superior)
        layout_barra.setContentsMargins(14, 10, 14, 10)

        rotulo_item = QLabel("Visualizar Registro do Item:")
        rotulo_item.setStyleSheet("font-weight: 700; color: #334155;")
        layout_barra.addWidget(rotulo_item)

        self.combo_item = QComboBox()
        self.combo_item.currentIndexChanged.connect(self.exibir_mrp_item)
        layout_barra.addWidget(self.combo_item, 1)

        self.rotulo_parametros_item = QLabel(
            "Lead Time: - | Est. Seg.: - | Lote Mín.: - | Saldo Inicial: -"
        )
        self.rotulo_parametros_item.setStyleSheet(
            "color: #475569; font-weight: 600; padding-left: 15px;"
        )
        layout_barra.addWidget(self.rotulo_parametros_item)

        layout.addWidget(barra_superior)

        divisor = QSplitter(Qt.Vertical)

        quadro_matriz = QFrame()
        quadro_matriz.setProperty("class", "card")
        layout_matriz = QVBoxLayout(quadro_matriz)

        rotulo_matriz = QLabel("Matriz de Planejamento de Necessidades de Materiais")
        rotulo_matriz.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_matriz.addWidget(rotulo_matriz)

        self.tabela_mrp = QTableWidget()
        self.tabela_mrp.setColumnCount(9)
        self.tabela_mrp.setHorizontalHeaderLabels([
            "Registro MRP", "Semana 1", "Semana 2", "Semana 3", "Semana 4",
            "Semana 5", "Semana 6", "Semana 7", "Semana 8"
        ])
        self.tabela_mrp.setRowCount(6)
        rotulos_linhas = [
            ("Necessidade Bruta (NB)", "#F8FAFC", "#1E293B"),
            ("Recebimentos Programados (RP)", "#EFF6FF", "#1D4ED8"),
            ("Estoque Projetado (EP)", "#F0FDF4", "#15803D"),
            ("Necessidade Líquida (NL)", "#FFFBEB", "#B45309"),
            ("Recebimentos Planejados (RecP)", "#F0FDF4", "#047857"),
            ("Liberações Planejadas (LibP)", "#FAF5FF", "#6D28D9"),
        ]
        for idx, (rotulo, cor_fundo, cor_texto) in enumerate(rotulos_linhas):
            item = QTableWidgetItem(rotulo)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            fonte = QFont()
            fonte.setBold(True)
            item.setFont(fonte)
            item.setBackground(QColor(cor_fundo))
            item.setForeground(QColor(cor_texto))
            self.tabela_mrp.setItem(idx, 0, item)

        self.tabela_mrp.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1, 9):
            self.tabela_mrp.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.tabela_mrp.verticalHeader().setVisible(False)
        self.tabela_mrp.setAlternatingRowColors(True)
        layout_matriz.addWidget(self.tabela_mrp)

        divisor.addWidget(quadro_matriz)

        quadro_excecoes = QFrame()
        quadro_excecoes.setProperty("class", "card")
        layout_excecoes = QVBoxLayout(quadro_excecoes)

        rotulo_excecoes = QLabel("Mensagens de Exceção e Alertas de Atraso (RN07)")
        rotulo_excecoes.setStyleSheet("font-weight: 700; color: #DC2626; font-size: 14px;")
        layout_excecoes.addWidget(rotulo_excecoes)

        self.tabela_excecoes = QTableWidget()
        self.tabela_excecoes.setColumnCount(2)
        self.tabela_excecoes.setHorizontalHeaderLabels(["Nº", "Mensagem de Exceção / Atraso"])
        self.tabela_excecoes.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabela_excecoes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_excecoes.verticalHeader().setVisible(False)
        self.tabela_excecoes.setAlternatingRowColors(True)
        layout_excecoes.addWidget(self.tabela_excecoes)

        divisor.addWidget(quadro_excecoes)
        divisor.setStretchFactor(0, 3)
        divisor.setStretchFactor(1, 2)

        layout.addWidget(divisor)

    def atualizar_dados(self):
        codigo_atual = self.combo_item.currentData()
        itens = listar_itens()
        if self.combo_item.count() != len(itens):
            self.combo_item.blockSignals(True)
            self.combo_item.clear()
            for item in itens:
                rotulo = f"{item.codigo} - {item.descricao} ({item.tipo_item})"
                self.combo_item.addItem(rotulo, item.codigo)

            if codigo_atual:
                indice = self.combo_item.findData(codigo_atual)
                if indice >= 0:
                    self.combo_item.setCurrentIndex(indice)
            self.combo_item.blockSignals(False)

        if not self.registros_armazenados:
            self.executar_calculo_mrp(silencioso=True)
        else:
            self.exibir_mrp_item()

        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def executar_calculo_mrp(self, silencioso=False):
        try:
            registros, excecoes, ordens_geradas = calcular_mrp()
            self.registros_armazenados = registros
            self.excecoes_armazenadas = excecoes

            self.tabela_excecoes.setRowCount(len(excecoes))
            for linha_idx, mensagem in enumerate(excecoes):
                num_widget = QTableWidgetItem(str(linha_idx + 1))
                num_widget.setTextAlignment(Qt.AlignCenter)
                num_widget.setBackground(QColor("#FEF2F2"))
                num_widget.setForeground(QColor("#991B1B"))
                self.tabela_excecoes.setItem(linha_idx, 0, num_widget)

                msg_widget = QTableWidgetItem(mensagem)
                msg_widget.setBackground(QColor("#FEF2F2"))
                msg_widget.setForeground(QColor("#991B1B"))
                self.tabela_excecoes.setItem(linha_idx, 1, msg_widget)

            self.exibir_mrp_item()
            if not silencioso:
                self.dados_modificados.emit()

            if not silencioso:
                QMessageBox.information(
                    self,
                    "MRP Executado",
                    f"Cálculo concluído com sucesso!\n\n"
                    f"• Itens processados: {len(registros)}\n"
                    f"• Novas ordens planejadas: {len(ordens_geradas)}\n"
                    f"• Exceções / atrasos detectados: {len(excecoes)}",
                )
        except Exception as exc:
            QMessageBox.critical(self, "Erro no MRP", f"Falha na execução do MRP: {exc}")

    def exibir_mrp_item(self):
        codigo = self.combo_item.currentData()
        if not codigo or codigo not in self.registros_armazenados:
            return

        registro = self.registros_armazenados[codigo]
        self.rotulo_parametros_item.setText(
            f"Tipo: {registro.tipo_item} | Lead Time: {registro.lead_time} sem | "
            f"Est. Segurança: {registro.estoque_seguranca:.1f} {registro.unidade} | "
            f"Lote Mínimo: {registro.lote_minimo:.1f} {registro.unidade} | "
            f"Saldo Inicial: {registro.estoque_inicial:.1f} {registro.unidade}"
        )

        fonte_padrao = QFont()
        fonte_destaque = QFont()
        fonte_destaque.setBold(True)

        for col_idx in range(1, 9):
            dados_sem = registro.semanas[col_idx - 1]

            nb_widget = QTableWidgetItem(f"{dados_sem.necessidade_bruta:.1f}")
            nb_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            nb_widget.setBackground(QColor("#F8FAFC"))
            nb_widget.setForeground(QColor("#1E293B"))
            self.tabela_mrp.setItem(0, col_idx, nb_widget)

            rp_widget = QTableWidgetItem(f"{dados_sem.recebimentos_programados:.1f}")
            rp_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rp_widget.setBackground(QColor("#EFF6FF"))
            rp_widget.setForeground(QColor("#1D4ED8"))
            self.tabela_mrp.setItem(1, col_idx, rp_widget)

            ep_widget = QTableWidgetItem(f"{dados_sem.estoque_projetado:.1f}")
            ep_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if dados_sem.estoque_projetado < registro.estoque_seguranca:
                ep_widget.setBackground(QColor("#FEE2E2"))
                ep_widget.setForeground(QColor("#DC2626"))
                ep_widget.setFont(fonte_destaque)
            else:
                ep_widget.setBackground(QColor("#F0FDF4"))
                ep_widget.setForeground(QColor("#15803D"))
                ep_widget.setFont(fonte_padrao)
            self.tabela_mrp.setItem(2, col_idx, ep_widget)

            nl_widget = QTableWidgetItem(f"{dados_sem.necessidade_liquida:.1f}")
            nl_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            nl_widget.setBackground(QColor("#FFFBEB"))
            nl_widget.setForeground(QColor("#B45309"))
            self.tabela_mrp.setItem(3, col_idx, nl_widget)

            recp_widget = QTableWidgetItem(f"{dados_sem.recebimentos_planejados:.1f}")
            recp_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            recp_widget.setBackground(QColor("#F0FDF4"))
            recp_widget.setForeground(QColor("#047857"))
            self.tabela_mrp.setItem(4, col_idx, recp_widget)

            libp_widget = QTableWidgetItem(f"{dados_sem.liberacoes_planejadas:.1f}")
            libp_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            libp_widget.setBackground(QColor("#FAF5FF"))
            libp_widget.setForeground(QColor("#6D28D9"))
            libp_widget.setFont(fonte_destaque)
            self.tabela_mrp.setItem(5, col_idx, libp_widget)


MRPView = VisaoMRP
