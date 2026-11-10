import datetime
import re
from typing import List, Optional, Dict, Any
from backend.database import obter_conexao
from backend.models import Item
from backend.exceptions import (
    ErroCodigoItemInvalido,
    ErroValidacao,
    ErroItemNaoEncontrado,
    ErroCentroTrabalhoNaoEncontrado,
)


PADRAO_CODIGO_ITEM = re.compile(r"^(PA|SA|MP)-\d{3,}$")


def validar_codigo_item(codigo: str, tipo_esperado: Optional[str] = None) -> str:
    limpo = codigo.strip().upper()
    correspondencia = PADRAO_CODIGO_ITEM.match(limpo)
    if not correspondencia:
        raise ErroCodigoItemInvalido(
            f"Código '{codigo}' inválido. O formato deve ser Tipo-Número (ex: PA-001, SA-020, MP-201)."
        )
    prefixo = correspondencia.group(1)
    if tipo_esperado and prefixo != tipo_esperado:
        raise ErroValidacao(
            f"Prefixo '{prefixo}' incompatível com o tipo '{tipo_esperado}'."
        )
    return limpo


def criar_item(dados: Dict[str, Any], caminho_bd=None) -> Item:
    tipo_item = str(dados.get("tipo_item", "")).strip().upper()
    if tipo_item not in ("PA", "SA", "MP"):
        raise ErroValidacao("O tipo do item deve ser PA, SA ou MP.")

    codigo = validar_codigo_item(str(dados.get("codigo", "")), tipo_esperado=tipo_item)
    descricao = str(dados.get("descricao", "")).strip()
    if not descricao:
        raise ErroValidacao("A descrição do item é obrigatória.")

    unidade = str(dados.get("unidade", "")).strip().upper()
    if not unidade:
        raise ErroValidacao("A unidade de medida é obrigatória.")

    try:
        custo_unitario = float(dados.get("custo_unitario", 0.0))
        lead_time = int(dados.get("lead_time", 1))
        estoque_seguranca = float(dados.get("estoque_seguranca", 0.0))
        lote_minimo = float(dados.get("lote_minimo", 1.0))
        estoque_atual = float(dados.get("estoque_atual", 0.0))
        tempo_unitario = float(dados.get("tempo_unitario", 0.0))
    except (ValueError, TypeError) as exc:
        raise ErroValidacao(f"Valor numérico inválido: {exc}")

    if custo_unitario < 0:
        raise ErroValidacao("O custo unitário não pode ser negativo.")
    if lead_time < 0:
        raise ErroValidacao("O lead time não pode ser negativo.")
    if estoque_seguranca < 0:
        raise ErroValidacao("O estoque de segurança não pode ser negativo.")
    if lote_minimo <= 0:
        raise ErroValidacao("O lote mínimo deve ser maior que zero.")
    if estoque_atual < 0:
        raise ErroValidacao("O saldo de estoque inicial não pode ser negativo.")
    if tempo_unitario < 0:
        raise ErroValidacao("O tempo unitário não pode ser negativo.")

    codigo_centro_trabalho = dados.get("codigo_centro_trabalho")
    if codigo_centro_trabalho:
        codigo_centro_trabalho = str(codigo_centro_trabalho).strip().upper()
        if not codigo_centro_trabalho:
            codigo_centro_trabalho = None

    if tipo_item == "MP":
        codigo_centro_trabalho = None
        tempo_unitario = 0.0

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo FROM itens WHERE codigo = ?", (codigo,))
    if cursor.fetchone():
        conexao.close()
        raise ErroValidacao(f"Item com código '{codigo}' já cadastrado.")

    if codigo_centro_trabalho:
        cursor.execute("SELECT codigo FROM centros_trabalho WHERE codigo = ?", (codigo_centro_trabalho,))
        if not cursor.fetchone():
            conexao.close()
            raise ErroCentroTrabalhoNaoEncontrado(
                f"Centro de trabalho '{codigo_centro_trabalho}' não encontrado."
            )

    cursor.execute(
        """
        INSERT INTO itens (
            codigo, descricao, tipo_item, unidade, custo_unitario,
            lead_time, estoque_seguranca, lote_minimo, estoque_atual,
            codigo_centro_trabalho, tempo_unitario
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            codigo,
            descricao,
            tipo_item,
            unidade,
            custo_unitario,
            lead_time,
            estoque_seguranca,
            lote_minimo,
            estoque_atual,
            codigo_centro_trabalho,
            tempo_unitario,
        ),
    )

    if estoque_atual > 0:
        agora_texto = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO kardex (
                codigo_item, data_movimentacao, tipo_movimentacao, quantidade,
                estoque_anterior, novo_estoque, documento_motivo
            ) VALUES (?, ?, 'ENTRADA', ?, 0.0, ?, 'Saldo Inicial de Cadastro')
            """,
            (codigo, agora_texto, estoque_atual, estoque_atual),
        )

    conexao.commit()
    conexao.close()

    return Item(
        codigo=codigo,
        descricao=descricao,
        tipo_item=tipo_item,
        unidade=unidade,
        custo_unitario=custo_unitario,
        lead_time=lead_time,
        estoque_seguranca=estoque_seguranca,
        lote_minimo=lote_minimo,
        estoque_atual=estoque_atual,
        codigo_centro_trabalho=codigo_centro_trabalho,
        tempo_unitario=tempo_unitario,
    )


def atualizar_item(codigo: str, dados: Dict[str, Any], caminho_bd=None) -> Item:
    codigo_limpo = codigo.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM itens WHERE codigo = ?", (codigo_limpo,))
    existente = cursor.fetchone()
    if not existente:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item com código '{codigo_limpo}' não encontrado.")

    tipo_item = existente["tipo_item"]
    descricao = str(dados.get("descricao", existente["descricao"])).strip()
    if not descricao:
        conexao.close()
        raise ErroValidacao("A descrição do item é obrigatória.")

    unidade = str(dados.get("unidade", existente["unidade"])).strip().upper()
    if not unidade:
        conexao.close()
        raise ErroValidacao("A unidade de medida é obrigatória.")

    try:
        custo_unitario = float(dados.get("custo_unitario", existente["custo_unitario"]))
        lead_time = int(dados.get("lead_time", existente["lead_time"]))
        estoque_seguranca = float(dados.get("estoque_seguranca", existente["estoque_seguranca"]))
        lote_minimo = float(dados.get("lote_minimo", existente["lote_minimo"]))
        tempo_unitario = float(dados.get("tempo_unitario", existente["tempo_unitario"]))
    except (ValueError, TypeError) as exc:
        conexao.close()
        raise ErroValidacao(f"Valor numérico inválido: {exc}")

    if custo_unitario < 0 or lead_time < 0 or estoque_seguranca < 0 or lote_minimo <= 0 or tempo_unitario < 0:
        conexao.close()
        raise ErroValidacao("Valores de custos, estoque, lead time ou tempo inválidos.")

    codigo_centro_trabalho = dados.get("codigo_centro_trabalho", existente["codigo_centro_trabalho"])
    if codigo_centro_trabalho:
        codigo_centro_trabalho = str(codigo_centro_trabalho).strip().upper()
        if not codigo_centro_trabalho:
            codigo_centro_trabalho = None

    if tipo_item == "MP":
        codigo_centro_trabalho = None
        tempo_unitario = 0.0

    if codigo_centro_trabalho:
        cursor.execute("SELECT codigo FROM centros_trabalho WHERE codigo = ?", (codigo_centro_trabalho,))
        if not cursor.fetchone():
            conexao.close()
            raise ErroCentroTrabalhoNaoEncontrado(
                f"Centro de trabalho '{codigo_centro_trabalho}' não encontrado."
            )

    cursor.execute(
        """
        UPDATE itens
        SET descricao = ?, unidade = ?, custo_unitario = ?, lead_time = ?,
            estoque_seguranca = ?, lote_minimo = ?, codigo_centro_trabalho = ?, tempo_unitario = ?
        WHERE codigo = ?
        """,
        (
            descricao,
            unidade,
            custo_unitario,
            lead_time,
            estoque_seguranca,
            lote_minimo,
            codigo_centro_trabalho,
            tempo_unitario,
            codigo_limpo,
        ),
    )
    conexao.commit()
    conexao.close()

    return Item(
        codigo=codigo_limpo,
        descricao=descricao,
        tipo_item=tipo_item,
        unidade=unidade,
        custo_unitario=custo_unitario,
        lead_time=lead_time,
        estoque_seguranca=estoque_seguranca,
        lote_minimo=lote_minimo,
        estoque_atual=existente["estoque_atual"],
        codigo_centro_trabalho=codigo_centro_trabalho,
        tempo_unitario=tempo_unitario,
    )


def obter_item(codigo: str, caminho_bd=None) -> Item:
    limpo = codigo.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM itens WHERE codigo = ?", (limpo,))
    linha = cursor.fetchone()
    conexao.close()
    if not linha:
        raise ErroItemNaoEncontrado(f"Item '{limpo}' não encontrado.")
    return Item(
        codigo=linha["codigo"],
        descricao=linha["descricao"],
        tipo_item=linha["tipo_item"],
        unidade=linha["unidade"],
        custo_unitario=linha["custo_unitario"],
        lead_time=linha["lead_time"],
        estoque_seguranca=linha["estoque_seguranca"],
        lote_minimo=linha["lote_minimo"],
        estoque_atual=linha["estoque_atual"],
        codigo_centro_trabalho=linha["codigo_centro_trabalho"],
        tempo_unitario=linha["tempo_unitario"],
    )


def listar_itens(tipo_item: Optional[str] = None, caminho_bd=None) -> List[Item]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    if tipo_item:
        cursor.execute(
            "SELECT * FROM itens WHERE tipo_item = ? ORDER BY codigo",
            (tipo_item.strip().upper(),),
        )
    else:
        cursor.execute("SELECT * FROM itens ORDER BY codigo")
    linhas = cursor.fetchall()
    conexao.close()

    return [
        Item(
            codigo=linha["codigo"],
            descricao=linha["descricao"],
            tipo_item=linha["tipo_item"],
            unidade=linha["unidade"],
            custo_unitario=linha["custo_unitario"],
            lead_time=linha["lead_time"],
            estoque_seguranca=linha["estoque_seguranca"],
            lote_minimo=linha["lote_minimo"],
            estoque_atual=linha["estoque_atual"],
            codigo_centro_trabalho=linha["codigo_centro_trabalho"],
            tempo_unitario=linha["tempo_unitario"],
        )
        for linha in linhas
    ]


def excluir_item(codigo: str, caminho_bd=None) -> None:
    limpo = codigo.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo FROM itens WHERE codigo = ?", (limpo,))
    if not cursor.fetchone():
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item '{limpo}' não encontrado.")

    cursor.execute(
        "SELECT COUNT(*) as contagem FROM estrutura_produto WHERE codigo_componente = ?",
        (limpo,),
    )
    if cursor.fetchone()["contagem"] > 0:
        conexao.close()
        raise ErroValidacao(
            f"O item '{limpo}' não pode ser excluído pois é componente de outra estrutura."
        )

    cursor.execute(
        "SELECT COUNT(*) as contagem FROM ordens WHERE codigo_item = ? AND status != 'ENCERRADA'",
        (limpo,),
    )
    if cursor.fetchone()["contagem"] > 0:
        conexao.close()
        raise ErroValidacao(
            f"O item '{limpo}' possui ordens ativas e não pode ser excluído."
        )

    cursor.execute("DELETE FROM itens WHERE codigo = ?", (limpo,))
    conexao.commit()
    conexao.close()
