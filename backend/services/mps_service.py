from typing import List, Dict, Any
from backend.database import obter_conexao
from backend.exceptions import (
    ErroItemNaoEncontrado,
    ErroValidacao,
)


def definir_demanda(codigo_item: str, semana: int, demanda: float, caminho_bd=None) -> None:
    codigo_limpo = codigo_item.strip().upper()
    if semana < 1 or semana > 8:
        raise ErroValidacao(f"A semana deve estar entre 1 e 8 (recebido: {semana}).")
    if demanda < 0:
        raise ErroValidacao("A demanda do MPS não pode ser negativa.")

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo, tipo_item FROM itens WHERE codigo = ?", (codigo_limpo,))
    item = cursor.fetchone()
    if not item:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item '{codigo_limpo}' não encontrado.")

    if item["tipo_item"] != "PA":
        conexao.close()
        raise ErroValidacao(
            f"Apenas produtos acabados (PA) podem ter demanda no MPS. '{codigo_limpo}' é {item['tipo_item']}."
        )

    cursor.execute(
        """
        INSERT INTO mps (codigo_item, semana, demanda)
        VALUES (?, ?, ?)
        ON CONFLICT(codigo_item, semana) DO UPDATE SET demanda = excluded.demanda
        """,
        (codigo_limpo, semana, demanda),
    )
    conexao.commit()
    conexao.close()


def obter_mps_item(codigo_item: str, caminho_bd=None) -> List[float]:
    codigo_limpo = codigo_item.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo FROM itens WHERE codigo = ?", (codigo_limpo,))
    if not cursor.fetchone():
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item '{codigo_limpo}' não encontrado.")

    cursor.execute(
        "SELECT semana, demanda FROM mps WHERE codigo_item = ? ORDER BY semana ASC",
        (codigo_limpo,),
    )
    linhas = cursor.fetchall()
    conexao.close()

    demandas = [0.0] * 8
    for linha in linhas:
        sem = linha["semana"]
        if 1 <= sem <= 8:
            demandas[sem - 1] = float(linha["demanda"])
    return demandas


def obter_todos_mps(caminho_bd=None) -> List[Dict[str, Any]]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT codigo, descricao, unidade
        FROM itens
        WHERE tipo_item = 'PA'
        ORDER BY codigo ASC
        """
    )
    itens_pa = cursor.fetchall()

    resultado = []
    for pa in itens_pa:
        codigo = pa["codigo"]
        cursor.execute(
            "SELECT semana, demanda FROM mps WHERE codigo_item = ? ORDER BY semana ASC",
            (codigo,),
        )
        linhas = cursor.fetchall()
        demandas = [0.0] * 8
        for linha in linhas:
            sem = linha["semana"]
            if 1 <= sem <= 8:
                demandas[sem - 1] = float(linha["demanda"])

        resultado.append(
            {
                "codigo": codigo,
                "descricao": pa["descricao"],
                "unidade": pa["unidade"],
                "demandas": demandas,
            }
        )

    conexao.close()
    return resultado


def salvar_tabela_mps(matriz_dados: List[Dict[str, Any]], caminho_bd=None) -> None:
    for linha in matriz_dados:
        codigo = linha.get("codigo")
        demandas = linha.get("demandas", [])
        for i, val in enumerate(demandas):
            definir_demanda(codigo, i + 1, float(val), caminho_bd=caminho_bd)
