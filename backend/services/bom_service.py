from typing import List, Dict, Any, Optional
from backend.database import obter_conexao
from backend.models import NoEstrutura, ItemEstrutura
from backend.exceptions import (
    ErroNivelBOMInvalido,
    ErroCicloBOM,
    ErroItemNaoEncontrado,
    ErroValidacao,
)


def adicionar_componente_estrutura(
    codigo_pai: str,
    codigo_componente: str,
    quantidade: float,
    caminho_bd=None,
) -> ItemEstrutura:
    pai_limpo = codigo_pai.strip().upper()
    comp_limpo = codigo_componente.strip().upper()

    if pai_limpo == comp_limpo:
        raise ErroCicloBOM("Um item não pode ser componente de si mesmo.")

    if quantidade <= 0:
        raise ErroValidacao("A quantidade do componente deve ser maior que zero.")

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("SELECT codigo, tipo_item FROM itens WHERE codigo = ?", (pai_limpo,))
    pai = cursor.fetchone()
    if not pai:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item pai '{pai_limpo}' não encontrado.")

    cursor.execute("SELECT codigo, tipo_item FROM itens WHERE codigo = ?", (comp_limpo,))
    componente = cursor.fetchone()
    if not componente:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Componente '{comp_limpo}' não encontrado.")

    tipo_pai = pai["tipo_item"]
    tipo_comp = componente["tipo_item"]

    if tipo_pai == "MP":
        conexao.close()
        raise ErroNivelBOMInvalido(
            f"O item '{pai_limpo}' é do tipo MP (matéria-prima) e não pode possuir estrutura de produto."
        )

    if tipo_pai == "SA":
        if tipo_comp != "MP":
            conexao.close()
            raise ErroNivelBOMInvalido(
                f"O item '{pai_limpo}' é SA e só pode conter componentes MP. Componente '{comp_limpo}' é {tipo_comp}."
            )

    if tipo_pai == "PA":
        if tipo_comp not in ("SA", "MP"):
            conexao.close()
            raise ErroNivelBOMInvalido(
                f"O item '{pai_limpo}' é PA e só pode conter componentes SA ou MP. "
                f"Componente '{comp_limpo}' é {tipo_comp}."
            )

    cursor.execute(
        """
        INSERT INTO estrutura_produto (codigo_pai, codigo_componente, quantidade)
        VALUES (?, ?, ?)
        ON CONFLICT(codigo_pai, codigo_componente) DO UPDATE SET quantidade = excluded.quantidade
        """,
        (pai_limpo, comp_limpo, quantidade),
    )
    conexao.commit()
    conexao.close()

    return ItemEstrutura(codigo_pai=pai_limpo, codigo_componente=comp_limpo, quantidade=quantidade)


def remover_componente_estrutura(codigo_pai: str, codigo_componente: str, caminho_bd=None) -> None:
    pai_limpo = codigo_pai.strip().upper()
    comp_limpo = codigo_componente.strip().upper()

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        "DELETE FROM estrutura_produto WHERE codigo_pai = ? AND codigo_componente = ?",
        (pai_limpo, comp_limpo),
    )
    conexao.commit()
    conexao.close()


def obter_componentes_diretos(codigo_pai: str, caminho_bd=None) -> List[Dict[str, Any]]:
    pai_limpo = codigo_pai.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT e.codigo_pai, e.codigo_componente, e.quantidade,
               i.descricao, i.tipo_item, i.unidade, i.custo_unitario, i.lead_time
        FROM estrutura_produto e
        JOIN itens i ON e.codigo_componente = i.codigo
        WHERE e.codigo_pai = ?
        ORDER BY i.tipo_item DESC, e.codigo_componente ASC
        """,
        (pai_limpo,),
    )
    linhas = cursor.fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def obter_pais(codigo_componente: str, caminho_bd=None) -> List[Dict[str, Any]]:
    comp_limpo = codigo_componente.strip().upper()
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT e.codigo_pai, e.codigo_componente, e.quantidade,
               i.descricao, i.tipo_item, i.unidade
        FROM estrutura_produto e
        JOIN itens i ON e.codigo_componente = i.codigo
        WHERE e.codigo_componente = ?
        ORDER BY e.codigo_pai ASC
        """,
        (comp_limpo,),
    )
    linhas = cursor.fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def explodir_arvore_estrutura(
    codigo_item: str,
    multiplicador: float = 1.0,
    nivel_atual: int = 0,
    visitados: Optional[set] = None,
    caminho_bd=None,
) -> NoEstrutura:
    if visitados is None:
        visitados = set()

    codigo_limpo = codigo_item.strip().upper()
    if codigo_limpo in visitados:
        raise ErroCicloBOM(f"Ciclo detectado na estrutura ao processar o item '{codigo_limpo}'.")

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT codigo, descricao, tipo_item, unidade FROM itens WHERE codigo = ?",
        (codigo_limpo,),
    )
    item = cursor.fetchone()
    if not item:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item '{codigo_limpo}' não encontrado.")

    cursor.execute(
        """
        SELECT e.codigo_componente, e.quantidade, i.descricao, i.tipo_item, i.unidade
        FROM estrutura_produto e
        JOIN itens i ON e.codigo_componente = i.codigo
        WHERE e.codigo_pai = ?
        ORDER BY i.tipo_item DESC, e.codigo_componente ASC
        """,
        (codigo_limpo,),
    )
    linhas_filhos = cursor.fetchall()
    conexao.close()

    novos_visitados = set(visitados)
    novos_visitados.add(codigo_limpo)

    no = NoEstrutura(
        nivel=nivel_atual,
        codigo_item=codigo_limpo,
        descricao=item["descricao"],
        tipo_item=item["tipo_item"],
        quantidade_por_pai=multiplicador if nivel_atual == 0 else 1.0,
        quantidade_total=multiplicador,
        unidade=item["unidade"],
        filhos=[],
    )

    for linha in linhas_filhos:
        comp_cod = linha["codigo_componente"]
        qtd_unitaria = float(linha["quantidade"])
        sub_total = multiplicador * qtd_unitaria
        no_filho = explodir_arvore_estrutura(
            comp_cod,
            multiplicador=sub_total,
            nivel_atual=nivel_atual + 1,
            visitados=novos_visitados,
            caminho_bd=caminho_bd,
        )
        no_filho.quantidade_por_pai = qtd_unitaria
        no.filhos.append(no_filho)

    return no


def obter_estrutura_achatada(
    codigo_item: str,
    multiplicador: float = 1.0,
    caminho_bd=None,
) -> List[Dict[str, Any]]:
    arvore = explodir_arvore_estrutura(codigo_item, multiplicador=multiplicador, caminho_bd=caminho_bd)
    resultado = []

    def _achatar(no: NoEstrutura):
        resultado.append(
            {
                "nivel": no.nivel,
                "indentacao": "    " * no.nivel,
                "codigo": no.codigo_item,
                "descricao": no.descricao,
                "tipo_item": no.tipo_item,
                "quantidade_por_pai": no.quantidade_por_pai,
                "quantidade_total": no.quantidade_total,
                "unidade": no.unidade,
            }
        )
        for filho in no.filhos:
            _achatar(filho)

    _achatar(arvore)
    return resultado
