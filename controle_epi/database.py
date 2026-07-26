"""
database.py
Camada de acesso a dados do Sistema de Controle de EPI.
Usa SQLite (biblioteca padrão do Python, sem dependências externas).
"""

import sqlite3
from datetime import date, timedelta
from contextlib import contextmanager

DB_PATH = "epi_control.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Cria as tabelas caso não existam."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cargo TEXT,
                setor TEXT
            );

            CREATE TABLE IF NOT EXISTS tipos_epi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                validade_dias INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entregas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER NOT NULL,
                epi_id INTEGER NOT NULL,
                data_entrega TEXT NOT NULL,
                data_validade TEXT NOT NULL,
                devolvido INTEGER NOT NULL DEFAULT 0,
                data_devolucao TEXT,
                FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id),
                FOREIGN KEY (epi_id) REFERENCES tipos_epi (id)
            );
            """
        )


# ---------- FUNCIONÁRIOS ----------

def add_funcionario(nome, cargo, setor):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO funcionarios (nome, cargo, setor) VALUES (?, ?, ?)",
            (nome, cargo, setor),
        )


def get_funcionarios():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM funcionarios ORDER BY nome").fetchall()


def delete_funcionario(funcionario_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM funcionarios WHERE id = ?", (funcionario_id,))


# ---------- TIPOS DE EPI ----------

def add_tipo_epi(nome, validade_dias):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tipos_epi (nome, validade_dias) VALUES (?, ?)",
            (nome, validade_dias),
        )


def get_tipos_epi():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tipos_epi ORDER BY nome").fetchall()


def delete_tipo_epi(epi_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM tipos_epi WHERE id = ?", (epi_id,))


# ---------- ENTREGAS ----------

def add_entrega(funcionario_id, epi_id, data_entrega: date):
    with get_conn() as conn:
        epi = conn.execute(
            "SELECT validade_dias FROM tipos_epi WHERE id = ?", (epi_id,)
        ).fetchone()
        if epi is None:
            raise ValueError("Tipo de EPI não encontrado.")
        validade = data_entrega + timedelta(days=epi["validade_dias"])
        conn.execute(
            """INSERT INTO entregas (funcionario_id, epi_id, data_entrega, data_validade)
               VALUES (?, ?, ?, ?)""",
            (funcionario_id, epi_id, data_entrega.isoformat(), validade.isoformat()),
        )


def get_entregas(apenas_ativas=False):
    query = """
        SELECT
            e.id,
            f.nome AS funcionario,
            f.setor AS setor,
            t.nome AS epi,
            e.data_entrega,
            e.data_validade,
            e.devolvido,
            e.data_devolucao
        FROM entregas e
        JOIN funcionarios f ON f.id = e.funcionario_id
        JOIN tipos_epi t ON t.id = e.epi_id
    """
    if apenas_ativas:
        query += " WHERE e.devolvido = 0"
    query += " ORDER BY e.data_validade ASC"

    with get_conn() as conn:
        return conn.execute(query).fetchall()


def devolver_entrega(entrega_id, data_devolucao: date):
    with get_conn() as conn:
        conn.execute(
            "UPDATE entregas SET devolvido = 1, data_devolucao = ? WHERE id = ?",
            (data_devolucao.isoformat(), entrega_id),
        )


def status_entrega(data_validade_str: str, devolvido: int, dias_alerta=15):
    """Retorna o status textual de uma entrega com base na data de validade."""
    if devolvido:
        return "Devolvido"
    validade = date.fromisoformat(data_validade_str)
    hoje = date.today()
    if validade < hoje:
        return "Vencido"
    if (validade - hoje).days <= dias_alerta:
        return "Próximo do vencimento"
    return "Válido"
