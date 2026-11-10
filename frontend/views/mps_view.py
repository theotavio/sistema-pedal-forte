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
    QMessageBox,
    QFrame,
)
from backend.services.mps_service import obter_todos_mps, definir_demanda
from backend.exceptions import ErroRegraNegocio
from frontend.animations import animar_surgimento_widget


class VisaoPlanoMestre(QWidget):
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
        titulo = QLabel("Plano Mestre de Produção (MPS)")
        titulo.setProperty("class", "view-header-title")
        subtitulo = QLabel(
            "Planejamento da demanda semanal de Produtos Acabados (PA) no horizonte de 8 semanas (RF07)"
        )
        subtitulo.setProperty("class", "view-header-subtitle")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        btn_salvar = QPushButton("Salvar Alterações")
        btn_salvar.setProperty("class", "btn-primary")
        btn_salvar.clicked.connect(self.ao_clicar_salvar_mps)
        cabecalho.addWidget(btn_salvar)

        layout.addLayout(cabecalho)

        barra_info = QFrame()
        barra_info.setProperty("class", "card")
        layout_info = QHBoxLayout(barra_info)
        layout_info.setContentsMargins(14, 10, 14, 10)

        rotulo_dica = QLabel(
            "Dica: Você pode editar diretamente os valores de cada semana na tabela abaixo "
            "e clicar em 'Salvar Alterações'."
        )
        rotulo_dica.setStyleSheet("color: #334155; font-weight: 500;")
        layout_info.addWidget(rotulo_dica)
        layout_info.addStretch()

        btn_recarregar = QPushButton("Recarregar")
        btn_recarregar.setProperty("class", "btn-secondary")
        btn_recarregar.clicked.connect(self.atualizar_dados)
        layout_info.addWidget(btn_recarregar)

        layout.addWidget(barra_info)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(12)
        self.tabela.setHorizontalHeaderLabels([
            "Código", "Descrição do Produto", "Unidade",
            "Semana 1", "Semana 2", "Semana 3", "Semana 4",
            "Semana 5", "Semana 6", "Semana 7", "Semana 8",
            "Total Demanda"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.cellChanged.connect(self.ao_alterar_celula)
        layout.addWidget(self.tabela)

    def atualizar_dados(self):
        self.tabela.blockSignals(True)
        registros_mps = obter_todos_mps()
        self.tabela.setRowCount(len(registros_mps))

        for linha_idx, registro in enumerate(registros_mps):
            item_codigo = QTableWidgetItem(registro["codigo"])
            item_codigo.setFlags(item_codigo.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha_idx, 0, item_codigo)

            item_desc = QTableWidgetItem(registro["descricao"])
            item_desc.setFlags(item_desc.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha_idx, 1, item_desc)

            item_un = QTableWidgetItem(registro["unidade"])
            item_un.setTextAlignment(Qt.AlignCenter)
            item_un.setFlags(item_un.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha_idx, 2, item_un)

            total = 0.0
            for sem_idx in range(8):
                valor = registro["demandas"][sem_idx]
                total += valor
                item_sem = QTableWidgetItem(f"{valor:.0f}")
                item_sem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabela.setItem(linha_idx, 3 + sem_idx, item_sem)

            item_total = QTableWidgetItem(f"{total:.0f}")
            item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_total.setFlags(item_total.flags() & ~Qt.ItemIsEditable)
            fonte_tot = QFont()
            fonte_tot.setBold(True)
            item_total.setFont(fonte_tot)
            item_total.setBackground(QColor("#F1F5F9"))
            item_total.setForeground(QColor("#0F172A"))
            self.tabela.setItem(linha_idx, 11, item_total)

        self.tabela.blockSignals(False)
        animar_surgimento_widget(self)

    def refresh_data(self):
        self.atualizar_dados()

    def ao_alterar_celula(self, linha, coluna):
        if 3 <= coluna <= 10:
            total = 0.0
            for sem in range(3, 11):
                item = self.tabela.item(linha, sem)
                try:
                    total += float(item.text().strip().replace(",", ".")) if item else 0.0
                except ValueError:
                    pass
            item_tot = self.tabela.item(linha, 11)
            if item_tot:
                item_tot.setText(f"{total:.0f}")

    def ao_clicar_salvar_mps(self):
        total_linhas = self.tabela.rowCount()
        try:
            for linha in range(total_linhas):
                codigo = self.tabela.item(linha, 0).text()
                for sem_idx in range(8):
                    item = self.tabela.item(linha, 3 + sem_idx)
                    try:
                        valor = float(item.text().strip().replace(",", "."))
                        if valor < 0:
                            raise ErroRegraNegocio("Demanda não pode ser negativa.")
                    except ValueError:
                        raise ErroRegraNegocio(
                            f"Valor numérico inválido na linha {linha + 1}, semana {sem_idx + 1}."
                        )
                    definir_demanda(codigo, sem_idx + 1, valor)

            QMessageBox.information(
                self, "Sucesso", "Plano Mestre de Produção (MPS) atualizado com sucesso!"
            )
            self.atualizar_dados()
            self.dados_modificados.emit()
        except ErroRegraNegocio as erro_regra:
            QMessageBox.warning(self, "Aviso", str(erro_regra))
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar MPS: {exc}")


MPSView = VisaoPlanoMestre
