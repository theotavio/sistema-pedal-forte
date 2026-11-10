import datetime
from typing import List, Dict, Any, Optional
from backend.database import obter_conexao
from backend.exceptions import (
    ErroEstadoOrdem,
    ErroEstoqueComponenteInsuficiente,
    ErroValidacao,
)


def listar_ordens(
    status: Optional[str] = None,
    tipo_ordem: Optional[str] = None,
    caminho_bd=None,
) -> List[Dict[str, Any]]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    consulta = """
        SELECT o.id, o.tipo_ordem, o.codigo_item, o.quantidade,
               o.semana_liberacao, o.semana_entrega, o.status, o.atrasada,
               i.descricao, i.unidade, i.tipo_item
        FROM ordens o
        JOIN itens i ON o.codigo_item = i.codigo
        WHERE 1=1
    """
    parametros = []

    if status:
        consulta += " AND o.status = ?"
        parametros.append(status.strip().upper())

    if tipo_ordem:
        consulta += " AND o.tipo_ordem = ?"
        parametros.append(tipo_ordem.strip().upper())

    consulta += " ORDER BY o.semana_entrega ASC, o.semana_liberacao ASC, o.id ASC"

    cursor.execute(consulta, parametros)
    linhas = cursor.fetchall()
    conexao.close()

    return [dict(linha) for linha in linhas]


def obter_ordem(id_ordem: int, caminho_bd=None) -> Dict[str, Any]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT o.id, o.tipo_ordem, o.codigo_item, o.quantidade,
               o.semana_liberacao, o.semana_entrega, o.status, o.atrasada,
               i.descricao, i.unidade, i.tipo_item
        FROM ordens o
        JOIN itens i ON o.codigo_item = i.codigo
        WHERE o.id = ?
        """,
        (id_ordem,),
    )
    linha = cursor.fetchone()
    conexao.close()
    if not linha:
        raise ErroValidacao(f"Ordem de id {id_ordem} não encontrada.")
    return dict(linha)


def firmar_ordem(id_ordem: int, caminho_bd=None) -> None:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute("SELECT status FROM ordens WHERE id = ?", (id_ordem,))
    linha = cursor.fetchone()
    if not linha:
        conexao.close()
        raise ErroValidacao(f"Ordem {id_ordem} não encontrada.")

    status_atual = linha["status"]
    if status_atual not in ("PLANEJADA", "ATRASADA"):
        conexao.close()
        raise ErroEstadoOrdem(
            f"Apenas ordens PLANEJADAS ou ATRASADAS podem ser firmadas. Status atual: {status_atual}."
        )

    cursor.execute("UPDATE ordens SET status = 'FIRME' WHERE id = ?", (id_ordem,))
    conexao.commit()
    conexao.close()


def liberar_ordem(id_ordem: int, caminho_bd=None) -> None:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute("SELECT status FROM ordens WHERE id = ?", (id_ordem,))
    linha = cursor.fetchone()
    if not linha:
        conexao.close()
        raise ErroValidacao(f"Ordem {id_ordem} não encontrada.")

    status_atual = linha["status"]
    if status_atual != "FIRME":
        conexao.close()
        raise ErroEstadoOrdem(
            f"Apenas ordens FIRMES podem ser liberadas. Status atual: {status_atual}."
        )

    cursor.execute("UPDATE ordens SET status = 'LIBERADA' WHERE id = ?", (id_ordem,))
    conexao.commit()
    conexao.close()


def encerrar_ordem(id_ordem: int, caminho_bd=None) -> None:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()
    cursor.execute("SELECT status FROM ordens WHERE id = ?", (id_ordem,))
    linha = cursor.fetchone()
    if not linha:
        conexao.close()
        raise ErroValidacao(f"Ordem {id_ordem} não encontrada.")

    status_atual = linha["status"]
    if status_atual != "LIBERADA":
        conexao.close()
        raise ErroEstadoOrdem(
            f"Apenas ordens LIBERADAS podem ser encerradas diretamente. Status atual: {status_atual}."
        )

    cursor.execute("UPDATE ordens SET status = 'ENCERRADA' WHERE id = ?", (id_ordem,))
    conexao.commit()
    conexao.close()


def apontar_producao(id_ordem: int, caminho_bd=None) -> None:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT o.id, o.tipo_ordem, o.codigo_item, o.quantidade, o.status,
               i.descricao, i.estoque_atual
        FROM ordens o
        JOIN itens i ON o.codigo_item = i.codigo
        WHERE o.id = ?
        """,
        (id_ordem,),
    )
    ordem = cursor.fetchone()
    if not ordem:
        conexao.close()
        raise ErroValidacao(f"Ordem {id_ordem} não encontrada.")

    if ordem["tipo_ordem"] != "OP":
        conexao.close()
        raise ErroEstadoOrdem("Apenas Ordens de Produção (OP) podem receber apontamento de chão de fábrica.")

    if ordem["status"] != "LIBERADA":
        conexao.close()
        raise ErroEstadoOrdem(
            f"O apontamento só é permitido para ordens LIBERADAS. Status atual: {ordem['status']}."
        )

    codigo_pai = ordem["codigo_item"]
    quantidade_produzida = float(ordem["quantidade"])

    cursor.execute(
        """
        SELECT e.codigo_componente, e.quantidade, i.descricao, i.estoque_atual, i.unidade
        FROM estrutura_produto e
        JOIN itens i ON e.codigo_componente = i.codigo
        WHERE e.codigo_pai = ?
        """,
        (codigo_pai,),
    )
    componentes = cursor.fetchall()

    lista_faltantes = []
    plano_consumo = []

    for comp in componentes:
        comp_cod = comp["codigo_componente"]
        qtd_necessaria = float(comp["quantidade"]) * quantidade_produzida
        estoque_disp = float(comp["estoque_atual"])

        if estoque_disp < qtd_necessaria:
            msg_faltante = (
                f"- {comp_cod} ({comp['descricao']}): "
                f"necessário {qtd_necessaria} {comp['unidade']}, disponível {estoque_disp} {comp['unidade']}"
            )
            lista_faltantes.append(msg_faltante)
        else:
            plano_consumo.append(
                {
                    "codigo": comp_cod,
                    "necessario": qtd_necessaria,
                    "estoque_anterior": estoque_disp,
                    "novo_estoque": estoque_disp - qtd_necessaria,
                }
            )

    if lista_faltantes:
        conexao.close()
        detalhe_msg = "\n".join(lista_faltantes)
        raise ErroEstoqueComponenteInsuficiente(
            f"Apontamento rejeitado: Saldo insuficiente de componentes "
            f"para fabricar a OP #{id_ordem} ({codigo_pai}):\n{detalhe_msg}"
        )

    agora_texto = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item_plano in plano_consumo:
        cursor.execute(
            "UPDATE itens SET estoque_atual = ? WHERE codigo = ?",
            (item_plano["novo_estoque"], item_plano["codigo"]),
        )
        cursor.execute(
            """
            INSERT INTO kardex (
                codigo_item, data_movimentacao, tipo_movimentacao, quantidade,
                estoque_anterior, novo_estoque, documento_motivo
            ) VALUES (?, ?, 'SAIDA', ?, ?, ?, ?)
            """,
            (
                item_plano["codigo"],
                agora_texto,
                item_plano["necessario"],
                item_plano["estoque_anterior"],
                item_plano["novo_estoque"],
                f"Baixa p/ OP #{id_ordem} ({codigo_pai})",
            ),
        )

    estoque_alvo_anterior = float(ordem["estoque_atual"])
    estoque_alvo_novo = estoque_alvo_anterior + quantidade_produzida

    cursor.execute(
        "UPDATE itens SET estoque_atual = ? WHERE codigo = ?",
        (estoque_alvo_novo, codigo_pai),
    )
    cursor.execute(
        """
        INSERT INTO kardex (
            codigo_item, data_movimentacao, tipo_movimentacao, quantidade,
            estoque_anterior, novo_estoque, documento_motivo
        ) VALUES (?, ?, 'ENTRADA', ?, ?, ?, ?)
        """,
        (
            codigo_pai,
            agora_texto,
            quantidade_produzida,
            estoque_alvo_anterior,
            estoque_alvo_novo,
            f"Produção Concluída OP #{id_ordem}",
        ),
    )

    cursor.execute("UPDATE ordens SET status = 'ENCERRADA' WHERE id = ?", (id_ordem,))
    conexao.commit()
    conexao.close()


def receber_ordem_compra(id_ordem: int, caminho_bd=None) -> None:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT o.id, o.tipo_ordem, o.codigo_item, o.quantidade, o.status,
               i.descricao, i.estoque_atual
        FROM ordens o
        JOIN itens i ON o.codigo_item = i.codigo
        WHERE o.id = ?
        """,
        (id_ordem,),
    )
    ordem = cursor.fetchone()
    if not ordem:
        conexao.close()
        raise ErroValidacao(f"Ordem {id_ordem} não encontrada.")

    if ordem["tipo_ordem"] != "OC":
        conexao.close()
        raise ErroEstadoOrdem("Apenas Ordens de Compra (OC) podem ser recebidas no almoxarifado.")

    if ordem["status"] != "LIBERADA":
        conexao.close()
        raise ErroEstadoOrdem(
            f"O recebimento só é permitido para ordens LIBERADAS. Status atual: {ordem['status']}."
        )

    codigo_item = ordem["codigo_item"]
    quantidade_recebida = float(ordem["quantidade"])
    estoque_anterior = float(ordem["estoque_atual"])
    novo_estoque = estoque_anterior + quantidade_recebida
    agora_texto = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "UPDATE itens SET estoque_atual = ? WHERE codigo = ?",
        (novo_estoque, codigo_item),
    )
    cursor.execute(
        """
        INSERT INTO kardex (
            codigo_item, data_movimentacao, tipo_movimentacao, quantidade,
            estoque_anterior, novo_estoque, documento_motivo
        ) VALUES (?, ?, 'ENTRADA', ?, ?, ?, ?)
        """,
        (
            codigo_item,
            agora_texto,
            quantidade_recebida,
            estoque_anterior,
            novo_estoque,
            f"Recebimento de Compra OC #{id_ordem}",
        ),
    )
    cursor.execute("UPDATE ordens SET status = 'ENCERRADA' WHERE id = ?", (id_ordem,))
    conexao.commit()
    conexao.close()
