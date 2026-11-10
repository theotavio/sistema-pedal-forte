from typing import Dict, Any, Optional, Set
from backend.database import obter_conexao
from backend.exceptions import ErroItemNaoEncontrado, ErroCicloBOM


def calcular_custo_padrao_item(
    codigo_item: str,
    visitados: Optional[Set[str]] = None,
    caminho_bd=None,
) -> Dict[str, Any]:
    if visitados is None:
        visitados = set()

    codigo_limpo = codigo_item.strip().upper()
    if codigo_limpo in visitados:
        raise ErroCicloBOM(f"Ciclo detectado no cálculo de custos para o item '{codigo_limpo}'.")

    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT i.codigo, i.descricao, i.tipo_item, i.unidade, i.custo_unitario,
               i.codigo_centro_trabalho, i.tempo_unitario,
               c.nome as nome_centro_trabalho, c.custo_hora
        FROM itens i
        LEFT JOIN centros_trabalho c ON i.codigo_centro_trabalho = c.codigo
        WHERE i.codigo = ?
        """,
        (codigo_limpo,),
    )
    item = cursor.fetchone()
    if not item:
        conexao.close()
        raise ErroItemNaoEncontrado(f"Item '{codigo_limpo}' não encontrado.")

    tipo_item = item["tipo_item"]

    if tipo_item == "MP":
        conexao.close()
        custo_val = float(item["custo_unitario"])
        return {
            "codigo_item": codigo_limpo,
            "descricao": item["descricao"],
            "tipo_item": tipo_item,
            "unidade": item["unidade"],
            "custo_materiais": round(custo_val, 2),
            "custo_mao_obra": 0.0,
            "custo_total": round(custo_val, 2),
            "codigo_centro_trabalho": None,
            "tempo_unitario": 0.0,
            "componentes": [],
        }

    cursor.execute(
        """
        SELECT e.codigo_componente, e.quantidade
        FROM estrutura_produto e
        WHERE e.codigo_pai = ?
        ORDER BY e.codigo_componente ASC
        """,
        (codigo_limpo,),
    )
    linhas_estrutura = cursor.fetchall()
    conexao.close()

    novos_visitados = set(visitados)
    novos_visitados.add(codigo_limpo)

    custo_materiais = 0.0
    desdobramento_componentes = []

    for e in linhas_estrutura:
        comp_cod = e["codigo_componente"]
        qtd_necessaria = float(e["quantidade"])
        dados_subcusto = calcular_custo_padrao_item(
            comp_cod,
            visitados=novos_visitados,
            caminho_bd=caminho_bd,
        )
        custo_unit_comp = dados_subcusto["custo_total"]
        subtotal_comp = qtd_necessaria * custo_unit_comp
        custo_materiais += subtotal_comp

        desdobramento_componentes.append(
            {
                "codigo_componente": comp_cod,
                "descricao": dados_subcusto["descricao"],
                "tipo_item": dados_subcusto["tipo_item"],
                "unidade": dados_subcusto["unidade"],
                "quantidade": qtd_necessaria,
                "custo_unitario": custo_unit_comp,
                "custo_total": round(subtotal_comp, 2),
            }
        )

    custo_hora = float(item["custo_hora"] or 0.0)
    tempo_unitario = float(item["tempo_unitario"] or 0.0)
    custo_mao_obra = tempo_unitario * custo_hora

    custo_total = custo_materiais + custo_mao_obra

    return {
        "codigo_item": codigo_limpo,
        "descricao": item["descricao"],
        "tipo_item": tipo_item,
        "unidade": item["unidade"],
        "custo_materiais": round(custo_materiais, 2),
        "custo_mao_obra": round(custo_mao_obra, 2),
        "custo_total": round(custo_total, 2),
        "codigo_centro_trabalho": item["codigo_centro_trabalho"],
        "nome_centro_trabalho": item["nome_centro_trabalho"],
        "tempo_unitario": tempo_unitario,
        "custo_hora": custo_hora,
        "componentes": desdobramento_componentes,
    }


def calcular_todos_custos_fabricados(caminho_bd=None) -> Dict[str, Dict[str, Any]]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT codigo FROM itens WHERE tipo_item IN ('PA', 'SA') ORDER BY tipo_item DESC, codigo ASC"
    )
    linhas = cursor.fetchall()
    conexao.close()

    resultado = {}
    for linha in linhas:
        cod = linha["codigo"]
        resultado[cod] = calcular_custo_padrao_item(cod, caminho_bd=caminho_bd)
    return resultado
