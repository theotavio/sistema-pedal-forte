from PySide6.QtCore import Qt
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
    QFrame,
    QSplitter,
)
from backend.services.crp_service import calcular_crp
from frontend.animations import animar_surgimento_widget


class VisaoCRP(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.crp_armazenado = []
        self.configurar_interface()

    def configurar_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        cabecalho = QHBoxLayout()
        textos = QVBoxLayout()
        titulo = QLabel("Planejamento da Capacidade de Manufatura (CRP)")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Carga x capacidade em horas/semana por centro com sinalização de gargalos (RF12 / RN09)"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_atualizar = QPushButton("Recalcular CRP")
        btn_atualizar.setProperty("class", "btn-secondary")
        btn_atualizar.clicked.connect(self.recalcular_crp)
        cabecalho.addWidget(btn_atualizar)

        layout.addLayout(cabecalho)

        barra_superior = QFrame()
        barra_superior.setProperty("class", "card")
        layout_barra = QHBoxLayout(barra_superior)
        layout_barra.setContentsMargins(14, 10, 14, 10)

        rotulo_ct = QLabel("Centro de Trabalho:")
        rotulo_ct.setStyleSheet("font-weight: 700; color: #334155;")
        layout_barra.addWidget(rotulo_ct)

        self.combo_ct = QComboBox()
        self.combo_ct.currentIndexChanged.connect(self.exibir_ct_selecionado)
        layout_barra.addWidget(self.combo_ct, 1)

        self.rotulo_info_ct = QLabel("Capacidade: - | Custo/Hora: -")
        self.rotulo_info_ct.setStyleSheet("color: #475569; font-weight: 600; padding-left: 15px;")
        layout_barra.addWidget(self.rotulo_info_ct)

        layout.addWidget(barra_superior)

        divisor = QSplitter(Qt.Vertical)

        quadro_resumo = QFrame()
        quadro_resumo.setProperty("class", "card")
        layout_resumo = QVBoxLayout(quadro_resumo)

        rotulo_tabela = QLabel("Carga x Capacidade nas 8 Semanas")
        rotulo_tabela.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_resumo.addWidget(rotulo_tabela)

        self.tabela_semanas = QTableWidget()
        self.tabela_semanas.setColumnCount(6)
        self.tabela_semanas.setHorizontalHeaderLabels([
            "Semana", "Carga Requerida (h)", "Capacidade (h)", "Sobrecarga (h)", "Ocupação (%)", "Situação"
        ])
        self.tabela_semanas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_semanas.verticalHeader().setVisible(False)
        self.tabela_semanas.setAlternatingRowColors(True)
        self.tabela_semanas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_semanas.itemSelectionChanged.connect(self.exibir_ops_semana)
        layout_resumo.addWidget(self.tabela_semanas)

        divisor.addWidget(quadro_resumo)

        quadro_detalhes = QFrame()
        quadro_detalhes.setProperty("class", "card")
        layout_detalhes = QVBoxLayout(quadro_detalhes)

        self.rotulo_titulo_ops = QLabel("Detalhamento das Ordens de Produção (Selecione uma semana acima)")
        self.rotulo_titulo_ops.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px;")
        layout_detalhes.addWidget(self.rotulo_titulo_ops)

        self.tabela_ops = QTableWidget()
        self.tabela_ops.setColumnCount(7)
        self.tabela_ops.setHorizontalHeaderLabels([
            "ID Ordem", "Item", "Descrição", "Quantidade", "Tempo Unit. (h)", "Carga Gerada (h)", "Status"
        ])
        self.tabela_ops.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabela_ops.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabela_ops.verticalHeader().setVisible(False)
        self.tabela_ops.setAlternatingRowColors(True)
        layout_detalhes.addWidget(self.tabela_ops)

        divisor.addWidget(quadro_detalhes)
        divisor.setStretchFactor(0, 3)
        divisor.setStretchFactor(1, 2)

        layout.addWidget(divisor)

    def recalcular_crp(self):
        self.crp_armazenado = []
        self.atualizar_dados()

    def atualizar_dados(self):
        codigo_atual = self.combo_ct.currentData()
        if not self.crp_armazenado:
            self.crp_armazenado = calcular_crp()

        self.combo_ct.blockSignals(True)
        self.combo_ct.clear()
        for ct in self.crp_armazenado:
            possui_sobrecarga = any(sem.tem_sobrecarga for sem in ct.semanas)
            marcador = " [SOBRECARGA]" if possui_sobrecarga else ""
            self.combo_ct.addItem(f"{ct.codigo_centro_trabalho} - {ct.nome}{marcador}", ct.codigo_centro_trabalho)

        if codigo_atual:
            indice = self.combo_ct.findData(codigo_atual)
            if indice >= 0:
                self.combo_ct.setCurrentIndex(indice)

        self.combo_ct.blockSignals(False)
        self.exibir_ct_selecionado()
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def exibir_ct_selecionado(self):
        codigo_ct = self.combo_ct.currentData()
        registro_ct = next(
            (c for c in self.crp_armazenado if c.codigo_centro_trabalho == codigo_ct), None
        )
        if not registro_ct:
            return

        self.rotulo_info_ct.setText(
            f"Capacidade: {registro_ct.capacidade_horas_semana:.1f} h/sem | "
            f"Custo-Hora: R$ {registro_ct.custo_hora:.2f}/h"
        )

        fonte_destaque = QFont()
        fonte_destaque.setBold(True)

        self.tabela_semanas.setRowCount(8)
        for linha_idx, sem in enumerate(registro_ct.semanas):
            sem_widget = QTableWidgetItem(f"Semana {sem.semana}")
            sem_widget.setTextAlignment(Qt.AlignCenter)
            self.tabela_semanas.setItem(linha_idx, 0, sem_widget)

            carga_widget = QTableWidgetItem(f"{sem.horas_carga:.1f} h")
            carga_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_semanas.setItem(linha_idx, 1, carga_widget)

            cap_widget = QTableWidgetItem(f"{sem.horas_capacidade:.1f} h")
            cap_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_semanas.setItem(linha_idx, 2, cap_widget)

            sobre_widget = QTableWidgetItem(f"{sem.horas_sobrecarga:.1f} h" if sem.tem_sobrecarga else "-")
            sobre_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if sem.tem_sobrecarga:
                sobre_widget.setBackground(QColor("#FEE2E2"))
                sobre_widget.setForeground(QColor("#DC2626"))
                sobre_widget.setFont(fonte_destaque)
            self.tabela_semanas.setItem(linha_idx, 3, sobre_widget)

            ocupacao = (sem.horas_carga / sem.horas_capacidade * 100.0) if sem.horas_capacidade > 0 else 0.0
            ocup_widget = QTableWidgetItem(f"{ocupacao:.1f}%")
            ocup_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if ocupacao > 100.0:
                ocup_widget.setBackground(QColor("#FEE2E2"))
                ocup_widget.setForeground(QColor("#DC2626"))
                ocup_widget.setFont(fonte_destaque)
            self.tabela_semanas.setItem(linha_idx, 4, ocup_widget)

            sit_widget = QTableWidgetItem("SOBRECARGA" if sem.tem_sobrecarga else "CAPACIDADE OK")
            sit_widget.setTextAlignment(Qt.AlignCenter)
            sit_widget.setFont(fonte_destaque)
            if sem.tem_sobrecarga:
                sit_widget.setBackground(QColor("#FEE2E2"))
                sit_widget.setForeground(QColor("#991B1B"))
            else:
                sit_widget.setBackground(QColor("#DCFCE7"))
                sit_widget.setForeground(QColor("#166534"))
            self.tabela_semanas.setItem(linha_idx, 5, sit_widget)

        if self.tabela_semanas.rowCount() > 0:
            self.tabela_semanas.selectRow(0)

    def exibir_ops_semana(self):
        linha = self.tabela_semanas.currentRow()
        codigo_ct = self.combo_ct.currentData()
        registro_ct = next(
            (c for c in self.crp_armazenado if c.codigo_centro_trabalho == codigo_ct), None
        )
        if not registro_ct or linha < 0 or linha >= len(registro_ct.semanas):
            return

        dados_sem = registro_ct.semanas[linha]
        self.rotulo_titulo_ops.setText(
            f"Ordens de Produção na Semana {dados_sem.semana} ({registro_ct.codigo_centro_trabalho}) - "
            f"Carga Total: {dados_sem.horas_carga:.1f}h / Capacidade: {dados_sem.horas_capacidade:.1f}h"
        )

        ops = dados_sem.detalhe_ordens
        self.tabela_ops.setRowCount(len(ops))
        for linha_idx, op in enumerate(ops):
            self.tabela_ops.setItem(linha_idx, 0, QTableWidgetItem(f"#{op['id_ordem']}"))
            self.tabela_ops.setItem(linha_idx, 1, QTableWidgetItem(op["codigo_item"]))
            self.tabela_ops.setItem(linha_idx, 2, QTableWidgetItem(op["descricao"]))

            qtd_widget = QTableWidgetItem(f"{op['quantidade']:.0f}")
            qtd_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_ops.setItem(linha_idx, 3, qtd_widget)

            tempo_widget = QTableWidgetItem(f"{op['tempo_unitario']:.2f} h")
            tempo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_ops.setItem(linha_idx, 4, tempo_widget)

            carga_widget = QTableWidgetItem(f"{op['carga_op']:.1f} h")
            carga_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_ops.setItem(linha_idx, 5, carga_widget)

            st_widget = QTableWidgetItem(op["status"])
            st_widget.setTextAlignment(Qt.AlignCenter)
            fonte_st = QFont()
            fonte_st.setBold(True)
            st_widget.setFont(fonte_st)
            if op["status"] == "LIBERADA":
                st_widget.setBackground(QColor("#DBEAFE"))
                st_widget.setForeground(QColor("#1E40AF"))
            elif op["status"] == "FIRME":
                st_widget.setBackground(QColor("#FEF3C7"))
                st_widget.setForeground(QColor("#92400E"))
            elif op["status"] == "PLANEJADA":
                st_widget.setBackground(QColor("#F1F5F9"))
                st_widget.setForeground(QColor("#475569"))
            self.tabela_ops.setItem(linha_idx, 6, st_widget)

        self.tabela_ops.resizeColumnsToContents()
        self.tabela_ops.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)


CRPView = VisaoCRP
