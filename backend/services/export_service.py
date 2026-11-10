import csv
from pathlib import Path
from typing import Optional
from backend.database import obter_conexao
from backend.services.order_service import listar_ordens

DIRETORIO_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "csv"
DIRETORIO_CSV.mkdir(parents=True, exist_ok=True)


def exportar_posicao_estoque_csv(caminho_saida: Optional[str] = None, caminho_bd=None) -> str:
    caminho = Path(caminho_saida) if caminho_saida else DIRETORIO_CSV / "posicao_estoque.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT codigo, descricao, tipo_item, unidade, custo_unitario,
               estoque_seguranca, lote_minimo, estoque_atual
        FROM itens
        ORDER BY codigo ASC
        """
    )
    linhas = cursor.fetchall()
    conexao.close()

    with open(caminho, mode="w", newline="", encoding="utf-8-sig") as arquivo_csv:
        escritor = csv.writer(arquivo_csv, delimiter=";")
        escritor.writerow(
            [
                "Codigo",
                "Descricao",
                "Tipo",
                "Unidade",
                "Custo_Unitario_R$",
                "Estoque_Seguranca",
                "Lote_Minimo",
                "Saldo_Atual",
                "Situacao_Estoque",
                "Valor_Total_R$",
            ]
        )
        for linha in linhas:
            saldo_atual = float(linha["estoque_atual"])
            estoque_seguranca = float(linha["estoque_seguranca"])
            custo = float(linha["custo_unitario"])
            status_texto = "ABAIXO DO SEGURANÇA" if saldo_atual < estoque_seguranca else "ADEQUADO"
            valor_total = saldo_atual * custo
            escritor.writerow(
                [
                    linha["codigo"],
                    linha["descricao"],
                    linha["tipo_item"],
                    linha["unidade"],
                    f"{custo:.2f}".replace(".", ","),
                    f"{estoque_seguranca:.2f}".replace(".", ","),
                    f"{float(linha['lote_minimo']):.2f}".replace(".", ","),
                    f"{saldo_atual:.2f}".replace(".", ","),
                    status_texto,
                    f"{valor_total:.2f}".replace(".", ","),
                ]
            )

    return str(caminho)


def exportar_ordens_csv(caminho_saida: Optional[str] = None, caminho_bd=None) -> str:
    caminho = Path(caminho_saida) if caminho_saida else DIRETORIO_CSV / "lista_ordens.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)

    ordens = listar_ordens(caminho_bd=caminho_bd)

    with open(caminho, mode="w", newline="", encoding="utf-8-sig") as arquivo_csv:
        escritor = csv.writer(arquivo_csv, delimiter=";")
        escritor.writerow(
            [
                "ID_Ordem",
                "Tipo_Ordem",
                "Codigo_Item",
                "Descricao_Item",
                "Quantidade",
                "Unidade",
                "Semana_Liberacao",
                "Semana_Entrega",
                "Status",
                "Atrasada",
            ]
        )
        for o in ordens:
            escritor.writerow(
                [
                    o["id"],
                    o["tipo_ordem"],
                    o["codigo_item"],
                    o["descricao"],
                    f"{float(o['quantidade']):.2f}".replace(".", ","),
                    o["unidade"],
                    o["semana_liberacao"],
                    o["semana_entrega"],
                    o["status"],
                    "SIM" if o["atrasada"] else "NAO",
                ]
            )

    return str(caminho)
