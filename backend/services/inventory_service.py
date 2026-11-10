import datetime
from typing import List, Dict, Any, Optional
from backend.database import obter_conexao
from backend.models import RegistroKardex
from backend.exceptions import (
    ErroEstoqueNegativo,
    ErroItemNaoEncontrado,
    ErroValidacao,
)


def registrar_movimentacao(
    codigo_item: str,
    tipo_movimentacao: str,
    quantidade: float,
    documento_motivo: str,
    data_movimentacao: Optional[str] = None,
    caminho_bd=None,
) -> RegistroKardex:
    codigo_limpo = codigo_item.strip().upper()
    tipo_limpo = tipo_movimentacao.strip().upper()

    if tipo_limpo not in ("ENTRADA", "SAIDA", "AJUSTE"):
        raise ErroValidacao("Tipo de movimentação deve ser ENTRADA, SAIDA ou AJUSTE.")

    motivo = documento_motivo.strip()
    if not motivo:
        raise ErroValidacao("O documento/motivo da movimentação é obrigatório.")

    if data_movimentacao is None:
        data_movimentacao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT codigo, descricao, estoque_atual, estoque_seguranca FROM itens WHERE codigo = ?",
        (codigo_limpo,),
    )
    item = cursor.fetchone()
    if not item:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item '{codigo_limpo}' não encontrado.")

    estoque_anterior = float(item["estoque_atual"])

    if tipo_limpo == "ENTRADA":
        if quantidade <= 0:
            conexao.close()
            raise ErroValidacao("Quantidade de entrada deve ser maior que zero.")
        novo_estoque = estoque_anterior + quantidade
        qtd_registrada = quantidade

    elif tipo_limpo == "SAIDA":
        if quantidade <= 0:
            conexao.close()
            raise ErroValidacao("Quantidade de saída deve ser maior que zero.")
        if quantidade > estoque_anterior:
            conexao.close()
            raise ErroEstoqueNegativo(
                f"Movimentação rejeitada: Saldo insuficiente para '{codigo_limpo}'. "
                f"Saldo atual: {estoque_anterior}, saída solicitada: {quantidade}."
            )
        novo_estoque = estoque_anterior - quantidade
        qtd_registrada = quantidade

    else:
        if quantidade < 0:
            conexao.close()
            raise ErroEstoqueNegativo(
                f"Ajuste rejeitado: O novo saldo não pode ser negativo ({quantidade})."
            )
        novo_estoque = quantidade
        qtd_registrada = abs(novo_estoque - estoque_anterior)

    cursor.execute(
        "UPDATE itens SET estoque_atual = ? WHERE codigo = ?",
        (novo_estoque, codigo_limpo),
    )

    cursor.execute(
        """
        INSERT INTO kardex (
            codigo_item, data_movimentacao, tipo_movimentacao, quantidade,
            estoque_anterior, novo_estoque, documento_motivo
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            codigo_limpo,
            data_movimentacao,
            tipo_limpo,
            qtd_registrada,
            estoque_anterior,
            novo_estoque,
            motivo,
        ),
    )
    id_kardex = cursor.lastrowid
    conexao.commit()
    conexao.close()

    return RegistroKardex(
        id=id_kardex,
        codigo_item=codigo_limpo,
        data_movimentacao=data_movimentacao,
        tipo_movimentacao=tipo_limpo,
        quantidade=qtd_registrada,
        estoque_anterior=estoque_anterior,
        novo_estoque=novo_estoque,
        documento_motivo=motivo,
    )


def obter_kardex(codigo_item: str, caminho_bd=None) -> List[RegistroKardex]:
    codigo_limpo = codigo_item.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT id, codigo_item, data_movimentacao, tipo_movimentacao, quantidade,
               estoque_anterior, novo_estoque, documento_motivo
        FROM kardex
        WHERE codigo_item = ?
        ORDER BY id DESC
        """,
        (codigo_limpo,),
    )
    linhas = cursor.fetchall()
    conexao.close()

    return [
        RegistroKardex(
            id=linha["id"],
            codigo_item=linha["codigo_item"],
            data_movimentacao=linha["data_movimentacao"],
            tipo_movimentacao=linha["tipo_movimentacao"],
            quantidade=linha["quantidade"],
            estoque_anterior=linha["estoque_anterior"],
            novo_estoque=linha["novo_estoque"],
            documento_motivo=linha["documento_motivo"],
        )
        for linha in linhas
    ]


def obter_situacao_estoque(codigo_item: str, caminho_bd=None) -> Dict[str, Any]:
    codigo_limpo = codigo_item.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT codigo, descricao, tipo_item, unidade, estoque_atual, estoque_seguranca
        FROM itens WHERE codigo = ?
        """,
        (codigo_limpo,),
    )
    linha = cursor.fetchone()
    conexao.close()
    if not linha:
        raise ErroItemNaoEncontrado(f"Item '{codigo_limpo}' não encontrado.")

    atual = float(linha["estoque_atual"])
    seguranca = float(linha["estoque_seguranca"])
    abaixo = atual < seguranca
    deficit = max(0.0, seguranca - atual)

    return {
        "codigo": linha["codigo"],
        "descricao": linha["descricao"],
        "tipo_item": linha["tipo_item"],
        "unidade": linha["unidade"],
        "estoque_atual": atual,
        "estoque_seguranca": seguranca,
        "esta_abaixo_seguranca": abaixo,
        "deficit": deficit,
    }


def listar_situacao_todos_estoques(caminho_bd=None) -> List[Dict[str, Any]]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT codigo, descricao, tipo_item, unidade, estoque_atual, estoque_seguranca
        FROM itens
        ORDER BY codigo ASC
        """
    )
    linhas = cursor.fetchall()
    conexao.close()

    resultado = []
    for linha in linhas:
        atual = float(linha["estoque_atual"])
        seguranca = float(linha["estoque_seguranca"])
        resultado.append(
            {
                "codigo": linha["codigo"],
                "descricao": linha["descricao"],
                "tipo_item": linha["tipo_item"],
                "unidade": linha["unidade"],
                "estoque_atual": atual,
                "estoque_seguranca": seguranca,
                "esta_abaixo_seguranca": atual < seguranca,
                "deficit": max(0.0, seguranca - atual),
            }
        )
    return resultado
