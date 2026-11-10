from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from backend.services.inventory_service import listar_situacao_todos_estoques
from backend.services.order_service import listar_ordens
from backend.services.crp_service import calcular_crp
from backend.services.item_service import listar_itens
from backend.services.mrp_service import calcular_mrp
from frontend.animations import animar_surgimento_widget


class VisaoPainelPrincipal(QWidget):
    solicitar_navegacao = Signal(str)
    dados_modificados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configurar_interface()

    def configurar_interface(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(28, 24, 28, 24)
        layout_principal.setSpacing(20)

        layout_cabecalho = QHBoxLayout()
        layout_textos = QVBoxLayout()
        titulo = QLabel("Painel de Controle - Visão Geral")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel("Acompanhamento executivo de estoques, ordens e capacidade fabril da Pedal Forte")
        subtitulo.setProperty("class", "view-header-subtitle")
        layout_textos.addWidget(titulo)
        layout_textos.addWidget(subtitulo)
        layout_cabecalho.addLayout(layout_textos)
        layout_cabecalho.addStretch()

        btn_executar_mrp = QPushButton("Executar Cálculo MRP")
        btn_executar_mrp.setProperty("class", "btn-primary")
        btn_executar_mrp.clicked.connect(self.ao_clicar_executar_mrp)
        layout_cabecalho.addWidget(btn_executar_mrp)

        layout_principal.addLayout(layout_cabecalho)

        layout_cartoes = QHBoxLayout()
        layout_cartoes.setSpacing(16)

        self.cartao_total_itens = self.criar_cartao_estatistica(
            "Total de Itens", "0", "#1D4ED8", "#EFF6FF", "#BFDBFE", "#2563EB"
        )
        self.cartao_itens_risco = self.criar_cartao_estatistica(
            "Itens em Risco (Abaixo Segurança)", "0", "#B91C1C", "#FEF2F2", "#FECACA", "#DC2626"
        )
        self.cartao_ordens_ativas = self.criar_cartao_estatistica(
            "Ordens Ativas (OP / OC)", "0", "#4338CA", "#EEF2FF", "#C7D2FE", "#4F46E5"
        )
        self.cartao_centros_sobrecarga = self.criar_cartao_estatistica(
            "Centros com Sobrecarga", "0", "#B45309", "#FFFBEB", "#FDE68A", "#D97706"
        )

        layout_cartoes.addWidget(self.cartao_total_itens)
        layout_cartoes.addWidget(self.cartao_itens_risco)
        layout_cartoes.addWidget(self.cartao_ordens_ativas)
        layout_cartoes.addWidget(self.cartao_centros_sobrecarga)

        layout_principal.addLayout(layout_cartoes)

        quadro_conteudo = QFrame()
        quadro_conteudo.setProperty("class", "card")
        layout_quadro = QHBoxLayout(quadro_conteudo)
        layout_quadro.setSpacing(20)

        layout_esquerda = QVBoxLayout()
        rotulo_estoque_critico = QLabel("Alerta de Estoque Crítico (Abaixo do Estoque de Segurança)")
        rotulo_estoque_critico.setStyleSheet("font-weight: 700; font-size: 14px; color: #DC2626;")
        layout_esquerda.addWidget(rotulo_estoque_critico)

        self.tabela_criticos = QTableWidget()
        self.tabela_criticos.setColumnCount(5)
        self.tabela_criticos.setHorizontalHeaderLabels([
            "Código", "Descrição", "Tipo", "Saldo Atual", "Est. Segurança"
        ])
        self.tabela_criticos.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabela_criticos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_criticos.verticalHeader().setVisible(False)
        self.tabela_criticos.setAlternatingRowColors(True)
        layout_esquerda.addWidget(self.tabela_criticos)

        layout_direita = QVBoxLayout()
        rotulo_ordens_recentes = QLabel("Ordens Recentes em Andamento (Firme / Liberada)")
        rotulo_ordens_recentes.setStyleSheet("font-weight: 700; font-size: 14px; color: #1E293B;")
        layout_direita.addWidget(rotulo_ordens_recentes)

        self.tabela_ordens = QTableWidget()
        self.tabela_ordens.setColumnCount(5)
        self.tabela_ordens.setHorizontalHeaderLabels([
            "ID", "Tipo", "Item", "Qtd", "Status"
        ])
        self.tabela_ordens.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabela_ordens.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabela_ordens.verticalHeader().setVisible(False)
        self.tabela_ordens.setAlternatingRowColors(True)
        layout_direita.addWidget(self.tabela_ordens)

        layout_quadro.addLayout(layout_esquerda, 1)
        layout_quadro.addLayout(layout_direita, 1)

        layout_principal.addWidget(quadro_conteudo, 1)

    def criar_cartao_estatistica(
        self, titulo, valor_padrao, cor_destaque, cor_fundo, cor_borda, cor_acento
    ):
        quadro = QFrame()
        quadro.setStyleSheet(
            f"QFrame {{ background-color: {cor_fundo}; border: 1px solid {cor_borda}; "
            f"border-left: 5px solid {cor_acento}; border-radius: 12px; }}"
        )
        layout = QVBoxLayout(quadro)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        rotulo_titulo = QLabel(titulo)
        rotulo_titulo.setStyleSheet(
            f"color: {cor_destaque}; font-size: 12px; font-weight: 700; "
            f"text-transform: uppercase; letter-spacing: 0.5px; border: none; background: transparent;"
        )

        rotulo_valor = QLabel(valor_padrao)
        rotulo_valor.setStyleSheet(
            f"color: {cor_destaque}; font-size: 30px; font-weight: 800; border: none; background: transparent;"
        )

        layout.addWidget(rotulo_titulo)
        layout.addWidget(rotulo_valor)
        quadro.rotulo_valor = rotulo_valor
        return quadro

    def atualizar_dados(self):
        try:
            todos_itens = listar_itens()
            self.cartao_total_itens.rotulo_valor.setText(str(len(todos_itens)))

            situacao_estoque = listar_situacao_todos_estoques()
            itens_criticos = [item for item in situacao_estoque if item.get("esta_abaixo_seguranca")]
            self.cartao_itens_risco.rotulo_valor.setText(str(len(itens_criticos)))

            fonte_alerta = QFont()
            fonte_alerta.setBold(True)

            self.tabela_criticos.setRowCount(len(itens_criticos))
            for linha_idx, item in enumerate(itens_criticos):
                self.tabela_criticos.setItem(linha_idx, 0, QTableWidgetItem(item["codigo"]))
                self.tabela_criticos.setItem(linha_idx, 1, QTableWidgetItem(item["descricao"]))

                tipo_widget = QTableWidgetItem(item["tipo_item"])
                tipo_widget.setTextAlignment(Qt.AlignCenter)
                self.tabela_criticos.setItem(linha_idx, 2, tipo_widget)

                saldo_widget = QTableWidgetItem(f"{item['estoque_atual']:.1f}")
                saldo_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                saldo_widget.setFont(fonte_alerta)
                saldo_widget.setBackground(QColor("#FEE2E2"))
                saldo_widget.setForeground(QColor("#DC2626"))
                self.tabela_criticos.setItem(linha_idx, 3, saldo_widget)

                seguranca_widget = QTableWidgetItem(f"{item['estoque_seguranca']:.1f}")
                seguranca_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_criticos.setItem(linha_idx, 4, seguranca_widget)

            self.tabela_criticos.resizeColumnsToContents()
            self.tabela_criticos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

            todas_ordens = listar_ordens()
            ordens_ativas = [ordem for ordem in todas_ordens if ordem.get("status") != "ENCERRADA"]
            self.cartao_ordens_ativas.rotulo_valor.setText(str(len(ordens_ativas)))

            ordens_exibicao = ordens_ativas[:10]
            self.tabela_ordens.setRowCount(len(ordens_exibicao))
            for linha_idx, ordem in enumerate(ordens_exibicao):
                id_widget = QTableWidgetItem(str(ordem.get("id")))
                id_widget.setTextAlignment(Qt.AlignCenter)
                self.tabela_ordens.setItem(linha_idx, 0, id_widget)

                tipo_widget = QTableWidgetItem(ordem.get("tipo_ordem", ""))
                tipo_widget.setTextAlignment(Qt.AlignCenter)
                if ordem.get("tipo_ordem") == "OP":
                    tipo_widget.setForeground(QColor("#1D4ED8"))
                else:
                    tipo_widget.setForeground(QColor("#047857"))
                self.tabela_ordens.setItem(linha_idx, 1, tipo_widget)

                self.tabela_ordens.setItem(
                    linha_idx, 2, QTableWidgetItem(f"{ordem.get('codigo_item', '')} - {ordem.get('descricao', '')}")
                )

                qtd_widget = QTableWidgetItem(f"{float(ordem.get('quantidade', 0.0)):.1f}")
                qtd_widget.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela_ordens.setItem(linha_idx, 3, qtd_widget)

                status_texto = ordem.get("status", "")
                status_widget = QTableWidgetItem(status_texto)
                status_widget.setTextAlignment(Qt.AlignCenter)
                status_widget.setFont(fonte_alerta)
                if status_texto == "LIBERADA":
                    status_widget.setBackground(QColor("#DBEAFE"))
                    status_widget.setForeground(QColor("#1E40AF"))
                elif status_texto == "FIRME":
                    status_widget.setBackground(QColor("#FEF3C7"))
                    status_widget.setForeground(QColor("#92400E"))
                elif status_texto == "PLANEJADA":
                    status_widget.setBackground(QColor("#F1F5F9"))
                    status_widget.setForeground(QColor("#475569"))
                elif status_texto == "ATRASADA":
                    status_widget.setBackground(QColor("#FEE2E2"))
                    status_widget.setForeground(QColor("#991B1B"))
                elif status_texto == "ENCERRADA":
                    status_widget.setBackground(QColor("#DCFCE7"))
                    status_widget.setForeground(QColor("#166534"))
                self.tabela_ordens.setItem(linha_idx, 4, status_widget)

            self.tabela_ordens.resizeColumnsToContents()
            self.tabela_ordens.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

            crp_resultado = calcular_crp(horizonte_semanas=8)
            centros_sobrecarregados = set()
            for registro in crp_resultado:
                for semana_dados in registro.semanas:
                    if semana_dados.tem_sobrecarga:
                        centros_sobrecarregados.add(registro.codigo_centro_trabalho)
                        break
            self.cartao_centros_sobrecarga.rotulo_valor.setText(str(len(centros_sobrecarregados)))

        except Exception as excecao:
            QMessageBox.critical(self, "Erro ao carregar Dashboard", str(excecao))

        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def ao_clicar_executar_mrp(self):
        try:
            calcular_mrp(horizonte_semanas=8)
            QMessageBox.information(
                self,
                "Cálculo Concluído",
                "O cálculo do MRP para o horizonte de 8 semanas foi executado com sucesso!\n"
                "As ordens planejadas foram recalculadas e os registros atualizados.",
            )
            self.atualizar_dados()
            self.dados_modificados.emit()
        except Exception as excecao:
            QMessageBox.critical(self, "Erro ao Executar MRP", f"Falha no processamento: {excecao}")


DashboardView = VisaoPainelPrincipal
