from typing import List, Optional
from backend.database import obter_conexao
from backend.models import CentroTrabalho
from backend.exceptions import (
    ErroCentroTrabalhoNaoEncontrado,
    ErroItemNaoEncontrado,
    ErroValidacao,
)


def criar_centro_trabalho(
    codigo: str,
    nome: str,
    capacidade_horas_semana: float,
    custo_hora: float,
    caminho_bd=None,
) -> CentroTrabalho:
    codigo_limpo = codigo.strip().upper()
    nome_limpo = nome.strip()

    if not codigo_limpo:
        raise ErroValidacao("O código do centro de trabalho é obrigatório.")
    if not nome_limpo:
        raise ErroValidacao("O nome do centro de trabalho é obrigatório.")
    if capacidade_horas_semana <= 0:
        raise ErroValidacao("A capacidade semanal em horas deve ser maior que zero.")
    if custo_hora < 0:
        raise ErroValidacao("O custo por hora não pode ser negativo.")

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo FROM centros_trabalho WHERE codigo = ?", (codigo_limpo,))
    if cursor.fetchone():
        conexao.close()
        raise ErroValidacao(f"Centro de trabalho '{codigo_limpo}' já cadastrado.")

    cursor.execute(
        """
        INSERT INTO centros_trabalho (codigo, nome, capacidade_horas_semana, custo_hora)
        VALUES (?, ?, ?, ?)
        """,
        (codigo_limpo, nome_limpo, capacidade_horas_semana, custo_hora),
    )
    conexao.commit()
    conexao.close()

    return CentroTrabalho(
        codigo=codigo_limpo,
        nome=nome_limpo,
        capacidade_horas_semana=capacidade_horas_semana,
        custo_hora=custo_hora,
    )


def atualizar_centro_trabalho(
    codigo: str,
    nome: str,
    capacidade_horas_semana: float,
    custo_hora: float,
    caminho_bd=None,
) -> CentroTrabalho:
    codigo_limpo = codigo.strip().upper()
    nome_limpo = nome.strip()

    if not nome_limpo:
        raise ErroValidacao("O nome do centro de trabalho é obrigatório.")
    if capacidade_horas_semana <= 0:
        raise ErroValidacao("A capacidade semanal em horas deve ser maior que zero.")
    if custo_hora < 0:
        raise ErroValidacao("O custo por hora não pode ser negativo.")

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo FROM centros_trabalho WHERE codigo = ?", (codigo_limpo,))
    if not cursor.fetchone():
        conexao.close()
        raise ErroCentroTrabalhoNaoEncontrado(f"Centro de trabalho '{codigo_limpo}' não encontrado.")

    cursor.execute(
        """
        UPDATE centros_trabalho
        SET nome = ?, capacidade_horas_semana = ?, custo_hora = ?
        WHERE codigo = ?
        """,
        (nome_limpo, capacidade_horas_semana, custo_hora, codigo_limpo),
    )
    conexao.commit()
    conexao.close()

    return CentroTrabalho(
        codigo=codigo_limpo,
        nome=nome_limpo,
        capacidade_horas_semana=capacidade_horas_semana,
        custo_hora=custo_hora,
    )


def obter_centro_trabalho(codigo: str, caminho_bd=None) -> CentroTrabalho:
    codigo_limpo = codigo.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM centros_trabalho WHERE codigo = ?", (codigo_limpo,))
    linha = cursor.fetchone()
    conexao.close()
    if not linha:
        raise ErroCentroTrabalhoNaoEncontrado(f"Centro de trabalho '{codigo_limpo}' não encontrado.")
    return CentroTrabalho(
        codigo=linha["codigo"],
        nome=linha["nome"],
        capacidade_horas_semana=linha["capacidade_horas_semana"],
        custo_hora=linha["custo_hora"],
    )


def listar_centros_trabalho(caminho_bd=None) -> List[CentroTrabalho]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM centros_trabalho ORDER BY codigo ASC")
    linhas = cursor.fetchall()
    conexao.close()
    return [
        CentroTrabalho(
            codigo=linha["codigo"],
            nome=linha["nome"],
            capacidade_horas_semana=linha["capacidade_horas_semana"],
            custo_hora=linha["custo_hora"],
        )
        for linha in linhas
    ]


def excluir_centro_trabalho(codigo: str, caminho_bd=None) -> None:
    codigo_limpo = codigo.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo FROM centros_trabalho WHERE codigo = ?", (codigo_limpo,))
    if not cursor.fetchone():
        conexao.close()
        raise ErroCentroTrabalhoNaoEncontrado(f"Centro de trabalho '{codigo_limpo}' não encontrado.")

    cursor.execute(
        "SELECT COUNT(*) as contagem FROM itens WHERE codigo_centro_trabalho = ?",
        (codigo_limpo,),
    )
    if cursor.fetchone()["contagem"] > 0:
        conexao.close()
        raise ErroValidacao(
            f"O centro de trabalho '{codigo_limpo}' está associado a itens fabricados e não pode ser excluído."
        )

    cursor.execute("DELETE FROM centros_trabalho WHERE codigo = ?", (codigo_limpo,))
    conexao.commit()
    conexao.close()


def definir_roteiro_item(
    codigo_item: str,
    codigo_centro_trabalho: Optional[str],
    tempo_unitario: float,
    caminho_bd=None,
) -> None:
    item_limpo = codigo_item.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo, tipo_item FROM itens WHERE codigo = ?", (item_limpo,))
    item = cursor.fetchone()
    if not item:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item '{item_limpo}' não encontrado.")

    if item["tipo_item"] == "MP":
        conexao.close()
        raise ErroValidacao("Itens do tipo MP (comprados) não possuem roteiro de fabricação.")

    if tempo_unitario < 0:
        conexao.close()
        raise ErroValidacao("O tempo unitário de produção não pode ser negativo.")

    ct_limpo = None
    if codigo_centro_trabalho:
        ct_limpo = codigo_centro_trabalho.strip().upper()
        cursor.execute("SELECT codigo FROM centros_trabalho WHERE codigo = ?", (ct_limpo,))
        if not cursor.fetchone():
            conexao.close()
            raise ErroCentroTrabalhoNaoEncontrado(f"Centro de trabalho '{ct_limpo}' não encontrado.")

    cursor.execute(
        "UPDATE itens SET codigo_centro_trabalho = ?, tempo_unitario = ? WHERE codigo = ?",
        (ct_limpo, tempo_unitario, item_limpo),
    )
    conexao.commit()
    conexao.close()
