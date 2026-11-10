from typing import List, Dict, Any, Tuple
from backend.database import obter_conexao
from backend.models import RegistroItemMRP, DadosSemanaisMRP
from backend.services.mps_service import obter_mps_item


def calcular_mrp(
    horizonte_semanas: int = 8,
    caminho_bd=None,
) -> Tuple[Dict[str, RegistroItemMRP], List[str], List[Dict[str, Any]]]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT codigo, descricao, tipo_item, unidade, custo_unitario,
               lead_time, estoque_seguranca, lote_minimo, estoque_atual
        FROM itens
        ORDER BY
            CASE tipo_item
                WHEN 'PA' THEN 1
                WHEN 'SA' THEN 2
                WHEN 'MP' THEN 3
                ELSE 4
            END,
            codigo ASC
        """
    )
    linhas_itens = cursor.fetchall()
    itens_por_codigo = {linha["codigo"]: dict(linha) for linha in linhas_itens}

    cursor.execute("SELECT codigo_pai, codigo_componente, quantidade FROM estrutura_produto")
    linhas_estrutura = cursor.fetchall()
    estrutura_por_pai: Dict[str, List[Dict[str, Any]]] = {}
    for e in linhas_estrutura:
        estrutura_por_pai.setdefault(e["codigo_pai"], []).append(dict(e))

    cursor.execute(
        """
        SELECT codigo_item, quantidade, semana_entrega
        FROM ordens
        WHERE status IN ('FIRME', 'LIBERADA')
        """
    )
    linhas_programadas = cursor.fetchall()
    programadas_por_item_semana: Dict[str, Dict[int, float]] = {}
    for lp in linhas_programadas:
        ci = lp["codigo_item"]
        se = int(lp["semana_entrega"])
        qtd = float(lp["quantidade"])
        if ci not in programadas_por_item_semana:
            programadas_por_item_semana[ci] = {s: 0.0 for s in range(1, 9)}
        if 1 <= se <= 8:
            programadas_por_item_semana[ci][se] += qtd

    cursor.execute("DELETE FROM ordens WHERE status = 'PLANEJADA'")
    cursor.execute("DELETE FROM ordens WHERE status = 'ATRASADA'")
    conexao.commit()

    necessidades_brutas: Dict[str, Dict[int, float]] = {
        codigo: {s: 0.0 for s in range(1, 9)} for codigo in itens_por_codigo
    }

    for codigo, itm in itens_por_codigo.items():
        if itm["tipo_item"] == "PA":
            demandas = obter_mps_item(codigo, caminho_bd=caminho_bd)
            for sem_idx, dem in enumerate(demandas):
                necessidades_brutas[codigo][sem_idx + 1] = float(dem)

    registros: Dict[str, RegistroItemMRP] = {}
    lista_excecoes: List[str] = []
    ordens_criadas: List[Dict[str, Any]] = []

    for codigo, itm in itens_por_codigo.items():
        lt = int(itm["lead_time"])
        es = float(itm["estoque_seguranca"])
        lote_minimo = float(itm["lote_minimo"])
        estoque_inicial = float(itm["estoque_atual"])
        tipo_item = itm["tipo_item"]

        registro_item = RegistroItemMRP(
            codigo_item=codigo,
            descricao=itm["descricao"],
            tipo_item=tipo_item,
            unidade=itm["unidade"],
            lead_time=lt,
            estoque_seguranca=es,
            lote_minimo=lote_minimo,
            estoque_inicial=estoque_inicial,
            semanas=[],
        )

        ep_anterior = estoque_inicial
        dicionario_programados = programadas_por_item_semana.get(codigo, {})

        recebimentos_planejados_semana = {s: 0.0 for s in range(1, 9)}
        liberacoes_planejadas_semana = {s: 0.0 for s in range(1, 9)}

        for t in range(1, 9):
            nb_t = necessidades_brutas[codigo].get(t, 0.0)
            rp_t = dicionario_programados.get(t, 0.0)

            nl_candidata = nb_t + es - (ep_anterior + rp_t)
            nl_t = max(0.0, nl_candidata)

            if nl_t > 0.0:
                rec_p_t = max(nl_t, lote_minimo)
            else:
                rec_p_t = 0.0

            ep_t = ep_anterior + rp_t + rec_p_t - nb_t
            recebimentos_planejados_semana[t] = rec_p_t

            dados_semana = DadosSemanaisMRP(
                semana=t,
                necessidade_bruta=nb_t,
                recebimentos_programados=rp_t,
                estoque_projetado=ep_t,
                necessidade_liquida=nl_t,
                recebimentos_planejados=rec_p_t,
                liberacoes_planejadas=0.0,
            )
            registro_item.semanas.append(dados_semana)
            ep_anterior = ep_t

        for t in range(1, 9):
            rec_p_t = recebimentos_planejados_semana[t]
            if rec_p_t > 0.0:
                semana_liberacao = t - lt
                tipo_ordem = "OP" if tipo_item in ("PA", "SA") else "OC"

                if semana_liberacao < 1:
                    status = "ATRASADA"
                    atrasada = 1
                    msg = (
                        f"Atenção: Ordem {tipo_ordem} para o item '{codigo}' com entrega na semana {t} "
                        f"possui semana de liberação {semana_liberacao} (< 1). Marcada como ATRASADA."
                    )
                    lista_excecoes.append(msg)
                    semana_alvo_liberacao = 1
                else:
                    status = "PLANEJADA"
                    atrasada = 0
                    semana_alvo_liberacao = semana_liberacao

                liberacoes_planejadas_semana[semana_alvo_liberacao] += rec_p_t

                if 1 <= semana_liberacao <= 8:
                    registro_item.semanas[semana_liberacao - 1].liberacoes_planejadas += rec_p_t
                elif semana_liberacao < 1:
                    registro_item.semanas[0].liberacoes_planejadas += rec_p_t

                cursor.execute(
                    """
                    INSERT INTO ordens (
                        tipo_ordem, codigo_item, quantidade, semana_liberacao,
                        semana_entrega, status, atrasada
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (tipo_ordem, codigo, rec_p_t, semana_liberacao, t, status, atrasada),
                )
                id_ordem = cursor.lastrowid
                ordens_criadas.append(
                    {
                        "id": id_ordem,
                        "tipo_ordem": tipo_ordem,
                        "codigo_item": codigo,
                        "descricao": itm["descricao"],
                        "quantidade": rec_p_t,
                        "semana_liberacao": semana_liberacao,
                        "semana_entrega": t,
                        "status": status,
                        "atrasada": atrasada,
                    }
                )

        if codigo in estrutura_por_pai:
            for comp in estrutura_por_pai[codigo]:
                comp_codigo = comp["codigo_componente"]
                qtd_unitaria = float(comp["quantidade"])
                for sem in range(1, 9):
                    qtd_lib_pai = liberacoes_planejadas_semana.get(sem, 0.0)
                    if qtd_lib_pai > 0.0:
                        necessidades_brutas[comp_codigo][sem] += qtd_lib_pai * qtd_unitaria

        registros[codigo] = registro_item

    conexao.commit()
    conexao.close()

    return registros, lista_excecoes, ordens_criadas


def obter_ultimo_mrp_item(codigo_item: str, caminho_bd=None) -> RegistroItemMRP:
    registros, _, _ = calcular_mrp(caminho_bd=caminho_bd)
    codigo_limpo = codigo_item.strip().upper()
    return registros.get(codigo_limpo)
