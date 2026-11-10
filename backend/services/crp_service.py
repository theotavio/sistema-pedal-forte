from typing import List, Dict, Any
from backend.database import obter_conexao
from backend.models import RegistroCRP, DadosSemanaisCRP


def calcular_crp(horizonte_semanas: int = 8, caminho_bd=None) -> List[RegistroCRP]:
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT codigo, nome, capacidade_horas_semana, custo_hora FROM centros_trabalho ORDER BY codigo ASC"
    )
    linhas_centros = cursor.fetchall()

    cursor.execute(
        """
        SELECT o.id, o.tipo_ordem, o.codigo_item, o.quantidade, o.semana_liberacao,
               o.semana_entrega, o.status, i.codigo_centro_trabalho, i.tempo_unitario,
               i.descricao
        FROM ordens o
        JOIN itens i ON o.codigo_item = i.codigo
        WHERE o.tipo_ordem = 'OP'
          AND o.status IN ('PLANEJADA', 'FIRME', 'LIBERADA', 'ATRASADA')
        """
    )
    linhas_ordens = cursor.fetchall()
    conexao.close()

    ordens_por_ct: Dict[str, List[Dict[str, Any]]] = {
        linha["codigo"]: [] for linha in linhas_centros
    }

    for linha_ordem in linhas_ordens:
        ct_codigo = linha_ordem["codigo_centro_trabalho"]
        if ct_codigo and ct_codigo in ordens_por_ct:
            ordens_por_ct[ct_codigo].append(dict(linha_ordem))

    resultado: List[RegistroCRP] = []

    for ct in linhas_centros:
        ct_codigo = ct["codigo"]
        capacidade = float(ct["capacidade_horas_semana"])
        custo_hora = float(ct["custo_hora"])

        registro_crp = RegistroCRP(
            codigo_centro_trabalho=ct_codigo,
            nome=ct["nome"],
            capacidade_horas_semana=capacidade,
            custo_hora=custo_hora,
            semanas=[],
        )

        for sem_idx in range(1, horizonte_semanas + 1):
            carga = 0.0
            ops_detalhadas = []

            for op in ordens_por_ct.get(ct_codigo, []):
                sem_lib = int(op["semana_liberacao"])
                semana_efetiva = 1 if sem_lib < 1 else sem_lib

                if semana_efetiva == sem_idx:
                    qtd = float(op["quantidade"])
                    tempo_un = float(op["tempo_unitario"])
                    carga_op = qtd * tempo_un
                    carga += carga_op
                    ops_detalhadas.append(
                        {
                            "id_ordem": op["id"],
                            "codigo_item": op["codigo_item"],
                            "descricao": op["descricao"],
                            "quantidade": qtd,
                            "tempo_unitario": tempo_un,
                            "carga_op": carga_op,
                            "status": op["status"],
                        }
                    )

            tem_sobrecarga = carga > capacidade
            horas_sobrecarga = max(0.0, carga - capacidade)

            registro_crp.semanas.append(
                DadosSemanaisCRP(
                    semana=sem_idx,
                    horas_carga=round(carga, 2),
                    horas_capacidade=round(capacidade, 2),
                    horas_sobrecarga=round(horas_sobrecarga, 2),
                    tem_sobrecarga=tem_sobrecarga,
                    detalhe_ordens=ops_detalhadas,
                )
            )

        resultado.append(registro_crp)

    return resultado
