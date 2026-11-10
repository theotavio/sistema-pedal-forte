from pathlib import Path
from typing import Optional, Tuple
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from backend.database import obter_conexao
from backend.services.inventory_service import listar_situacao_todos_estoques
from backend.services.mrp_service import calcular_mrp
from backend.services.crp_service import calcular_crp

matplotlib.use("Agg")

DIRETORIO_GRAFICOS = Path(__file__).resolve().parent.parent.parent / "data" / "graficos"
DIRETORIO_GRAFICOS.mkdir(parents=True, exist_ok=True)


def gerar_grafico_posicao_estoque(
    caminho_saida: Optional[str] = None,
    caminho_bd=None,
    salvar_arquivo: bool = True,
) -> Tuple[plt.Figure, str]:
    caminho_alvo = Path(caminho_saida) if caminho_saida else DIRETORIO_GRAFICOS / "posicao_estoque.png"
    caminho_alvo.parent.mkdir(parents=True, exist_ok=True)

    dados_itens = listar_situacao_todos_estoques(caminho_bd=caminho_bd)
    codigos = [item["codigo"] for item in dados_itens]
    estoques_atuais = [item["estoque_atual"] for item in dados_itens]
    estoques_seguranca = [item["estoque_seguranca"] for item in dados_itens]

    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    x = np.arange(len(codigos))
    largura = 0.38

    ax.bar(
        x - largura / 2, estoques_atuais, largura, label="Saldo Atual", color="#2563EB", edgecolor="none"
    )
    ax.bar(
        x + largura / 2, estoques_seguranca, largura, label="Estoque de Segurança", color="#F59E0B", edgecolor="none"
    )

    ax.set_ylabel("Quantidade", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_title(
        "Posição de Estoque: Saldo Atual x Estoque de Segurança",
        fontsize=14,
        fontweight="bold",
        color="#0F172A",
        pad=15,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(codigos, rotation=45, ha="right", fontsize=9, color="#334155")
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#E2E8F0", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")

    fig.tight_layout()
    if salvar_arquivo:
        fig.savefig(str(caminho_alvo), dpi=150)
    return fig, str(caminho_alvo)


def gerar_grafico_estoque_projetado(
    codigo_item: str,
    caminho_saida: Optional[str] = None,
    caminho_bd=None,
    salvar_arquivo: bool = True,
) -> Tuple[plt.Figure, str]:
    codigo_limpo = codigo_item.strip().upper()
    caminho_alvo = (
        Path(caminho_saida)
        if caminho_saida
        else DIRETORIO_GRAFICOS / f"estoque_projetado_{codigo_limpo}.png"
    )
    caminho_alvo.parent.mkdir(parents=True, exist_ok=True)

    registros, _, _ = calcular_mrp(caminho_bd=caminho_bd)
    registro_item = registros.get(codigo_limpo)

    semanas = list(range(1, 9))
    if registro_item:
        projetado = [s.estoque_projetado for s in registro_item.semanas]
        seguranca = [registro_item.estoque_seguranca] * 8
        desc = registro_item.descricao
    else:
        projetado = [0.0] * 8
        seguranca = [0.0] * 8
        desc = ""

    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    ax.plot(
        semanas, projetado, marker="o", linewidth=2.5, color="#059669",
        label="Estoque Projetado (EP)", markersize=7
    )
    ax.axhline(
        y=seguranca[0], color="#DC2626", linestyle="--", linewidth=2,
        label=f"Estoque de Segurança ({seguranca[0]:.1f})"
    )

    for sem_idx, val in zip(semanas, projetado):
        ax.annotate(
            f"{val:.0f}",
            (sem_idx, val),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="#065F46",
        )

    ax.set_xlabel("Semana do Planejamento", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_ylabel("Quantidade Projetada", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_title(
        f"Estoque Projetado nas 8 Semanas - {codigo_limpo} ({desc})",
        fontsize=13,
        fontweight="bold",
        color="#0F172A",
        pad=15,
    )
    ax.set_xticks(semanas)
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#E2E8F0", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5, color="#CBD5E1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")

    fig.tight_layout()
    if salvar_arquivo:
        fig.savefig(str(caminho_alvo), dpi=150)
    return fig, str(caminho_alvo)


def gerar_grafico_ordens_por_entrega(
    caminho_saida: Optional[str] = None,
    caminho_bd=None,
    salvar_arquivo: bool = True,
) -> Tuple[plt.Figure, str]:
    caminho_alvo = Path(caminho_saida) if caminho_saida else DIRETORIO_GRAFICOS / "ordens_semana_entrega.png"
    caminho_alvo.parent.mkdir(parents=True, exist_ok=True)

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT tipo_ordem, semana_entrega, SUM(quantidade) as total_qtd
        FROM ordens
        WHERE semana_entrega BETWEEN 1 AND 8
        GROUP BY tipo_ordem, semana_entrega
        """
    )
    linhas = cursor.fetchall()
    conexao.close()

    quantidades_op = [0.0] * 8
    quantidades_oc = [0.0] * 8

    for linha in linhas:
        sem = int(linha["semana_entrega"]) - 1
        qtd = float(linha["total_qtd"])
        if linha["tipo_ordem"] == "OP":
            quantidades_op[sem] = qtd
        else:
            quantidades_oc[sem] = qtd

    semanas = np.arange(1, 9)
    largura = 0.55

    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    ax.bar(semanas, quantidades_op, largura, label="Ordens de Produção (OP)", color="#4F46E5")
    ax.bar(
        semanas, quantidades_oc, largura, bottom=quantidades_op,
        label="Ordens de Compra (OC)", color="#06B6D4"
    )

    for i in range(8):
        total = quantidades_op[i] + quantidades_oc[i]
        if total > 0:
            ax.text(
                semanas[i], total + 2, f"{total:.0f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1E293B"
            )

    ax.set_xlabel("Semana de Entrega", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_ylabel("Quantidade Total", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_title(
        "Ordens de Produção (OP) e Compra (OC) por Semana de Entrega",
        fontsize=13,
        fontweight="bold",
        color="#0F172A",
        pad=15,
    )
    ax.set_xticks(semanas)
    ax.set_xticklabels([f"Semana {s}" for s in semanas], fontsize=9, color="#334155")
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#E2E8F0", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")

    fig.tight_layout()
    if salvar_arquivo:
        fig.savefig(str(caminho_alvo), dpi=150)
    return fig, str(caminho_alvo)


def gerar_grafico_crp(
    codigo_centro_trabalho: str,
    caminho_saida: Optional[str] = None,
    caminho_bd=None,
    salvar_arquivo: bool = True,
) -> Tuple[plt.Figure, str]:
    ct_limpo = codigo_centro_trabalho.strip().upper()
    caminho_alvo = (
        Path(caminho_saida)
        if caminho_saida
        else DIRETORIO_GRAFICOS / f"carga_capacidade_{ct_limpo}.png"
    )
    caminho_alvo.parent.mkdir(parents=True, exist_ok=True)

    lista_crp = calcular_crp(caminho_bd=caminho_bd)
    registro_ct = next((c for c in lista_crp if c.codigo_centro_trabalho == ct_limpo), None)

    semanas = list(range(1, 9))
    if registro_ct:
        cargas = [s.horas_carga for s in registro_ct.semanas]
        capacidade = registro_ct.capacidade_horas_semana
        nome_ct = registro_ct.nome
    else:
        cargas = [0.0] * 8
        capacidade = 40.0
        nome_ct = ""

    cores = ["#EF4444" if val > capacidade else "#3B82F6" for val in cargas]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    ax.bar(semanas, cargas, width=0.5, color=cores, label="Carga (horas)")
    ax.axhline(
        y=capacidade, color="#DC2626", linestyle="--", linewidth=2.2,
        label=f"Capacidade ({capacidade:.0f}h/sem)"
    )

    for sem_idx, val in zip(semanas, cargas):
        if val > 0:
            cor_txt = "#B91C1C" if val > capacidade else "#1D4ED8"
            ax.text(
                sem_idx, val + 0.8, f"{val:.1f}h",
                ha="center", va="bottom", fontsize=9, fontweight="bold", color=cor_txt
            )

    ax.set_xlabel("Semana", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_ylabel("Horas", fontsize=11, fontweight="bold", color="#1E293B")
    ax.set_title(
        f"Carga x Capacidade (CRP) - {ct_limpo} ({nome_ct})",
        fontsize=13,
        fontweight="bold",
        color="#0F172A",
        pad=15,
    )
    ax.set_xticks(semanas)
    ax.set_xticklabels([f"Sem {s}" for s in semanas], fontsize=9, color="#334155")
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="#E2E8F0", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")

    fig.tight_layout()
    if salvar_arquivo:
        fig.savefig(str(caminho_alvo), dpi=150)
    return fig, str(caminho_alvo)
