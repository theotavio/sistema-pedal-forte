from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Item:
    codigo: str
    descricao: str
    tipo_item: str
    unidade: str
    custo_unitario: float = 0.0
    lead_time: int = 1
    estoque_seguranca: float = 0.0
    lote_minimo: float = 1.0
    estoque_atual: float = 0.0
    codigo_centro_trabalho: Optional[str] = None
    tempo_unitario: float = 0.0


@dataclass
class ItemEstrutura:
    codigo_pai: str
    codigo_componente: str
    quantidade: float


@dataclass
class NoEstrutura:
    nivel: int
    codigo_item: str
    descricao: str
    tipo_item: str
    quantidade_por_pai: float
    quantidade_total: float
    unidade: str
    filhos: List['NoEstrutura'] = field(default_factory=list)


@dataclass
class CentroTrabalho:
    codigo: str
    nome: str
    capacidade_horas_semana: float
    custo_hora: float


@dataclass
class RegistroKardex:
    id: Optional[int]
    codigo_item: str
    data_movimentacao: str
    tipo_movimentacao: str
    quantidade: float
    estoque_anterior: float
    novo_estoque: float
    documento_motivo: str


@dataclass
class Ordem:
    id: Optional[int]
    tipo_ordem: str
    codigo_item: str
    quantidade: float
    semana_liberacao: int
    semana_entrega: int
    status: str
    atrasada: int = 0
    descricao: str = ""


@dataclass
class DadosSemanaisMRP:
    semana: int
    necessidade_bruta: float = 0.0
    recebimentos_programados: float = 0.0
    estoque_projetado: float = 0.0
    necessidade_liquida: float = 0.0
    recebimentos_planejados: float = 0.0
    liberacoes_planejadas: float = 0.0


@dataclass
class RegistroItemMRP:
    codigo_item: str
    descricao: str
    tipo_item: str
    unidade: str
    lead_time: int
    estoque_seguranca: float
    lote_minimo: float
    estoque_inicial: float
    semanas: List[DadosSemanaisMRP] = field(default_factory=list)


@dataclass
class DadosSemanaisCRP:
    semana: int
    horas_carga: float = 0.0
    horas_capacidade: float = 0.0
    horas_sobrecarga: float = 0.0
    tem_sobrecarga: bool = False
    detalhe_ordens: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RegistroCRP:
    codigo_centro_trabalho: str
    nome: str
    capacidade_horas_semana: float
    custo_hora: float
    semanas: List[DadosSemanaisCRP] = field(default_factory=list)
