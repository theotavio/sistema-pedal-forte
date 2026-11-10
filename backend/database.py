import sqlite3
from pathlib import Path


DIRETORIO_BASE = Path(__file__).resolve().parent.parent
DIRETORIO_DADOS = DIRETORIO_BASE / "data"
CAMINHO_BD = DIRETORIO_DADOS / "pedal_forte.db"


def obter_conexao(caminho_bd=None):
    if caminho_bd is None:
        caminho_bd = CAMINHO_BD
    Path(caminho_bd).parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(str(caminho_bd), timeout=30.0)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON;")
    conexao.execute("PRAGMA journal_mode = WAL;")
    return conexao


def inicializar_bd(caminho_bd=None):
    conexao = obter_conexao(caminho_bd)
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS centros_trabalho (
        codigo TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        capacidade_horas_semana REAL NOT NULL,
        custo_hora REAL NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens (
        codigo TEXT PRIMARY KEY,
        descricao TEXT NOT NULL,
        tipo_item TEXT NOT NULL CHECK(tipo_item IN ('PA', 'SA', 'MP')),
        unidade TEXT NOT NULL,
        custo_unitario REAL NOT NULL DEFAULT 0.0,
        lead_time INTEGER NOT NULL DEFAULT 1,
        estoque_seguranca REAL NOT NULL DEFAULT 0.0,
        lote_minimo REAL NOT NULL DEFAULT 1.0,
        estoque_atual REAL NOT NULL DEFAULT 0.0,
        codigo_centro_trabalho TEXT,
        tempo_unitario REAL DEFAULT 0.0,
        FOREIGN KEY (codigo_centro_trabalho) REFERENCES centros_trabalho(codigo) ON DELETE SET NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estrutura_produto (
        codigo_pai TEXT NOT NULL,
        codigo_componente TEXT NOT NULL,
        quantidade REAL NOT NULL,
        PRIMARY KEY (codigo_pai, codigo_componente),
        FOREIGN KEY (codigo_pai) REFERENCES itens(codigo) ON DELETE CASCADE,
        FOREIGN KEY (codigo_componente) REFERENCES itens(codigo) ON DELETE RESTRICT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kardex (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_item TEXT NOT NULL,
        data_movimentacao TEXT NOT NULL,
        tipo_movimentacao TEXT NOT NULL CHECK(tipo_movimentacao IN ('ENTRADA', 'SAIDA', 'AJUSTE')),
        quantidade REAL NOT NULL,
        estoque_anterior REAL NOT NULL,
        novo_estoque REAL NOT NULL,
        documento_motivo TEXT NOT NULL,
        FOREIGN KEY (codigo_item) REFERENCES itens(codigo) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mps (
        codigo_item TEXT NOT NULL,
        semana INTEGER NOT NULL CHECK(semana BETWEEN 1 AND 8),
        demanda REAL NOT NULL DEFAULT 0.0,
        PRIMARY KEY (codigo_item, semana),
        FOREIGN KEY (codigo_item) REFERENCES itens(codigo) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_ordem TEXT NOT NULL CHECK(tipo_ordem IN ('OP', 'OC')),
        codigo_item TEXT NOT NULL,
        quantidade REAL NOT NULL,
        semana_liberacao INTEGER NOT NULL,
        semana_entrega INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('PLANEJADA', 'FIRME', 'LIBERADA', 'ENCERRADA', 'ATRASADA')),
        atrasada INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (codigo_item) REFERENCES itens(codigo) ON DELETE CASCADE
    );
    """)

    conexao.commit()
    conexao.close()
