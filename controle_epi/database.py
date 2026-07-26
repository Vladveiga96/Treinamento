"""
database.py
Camada de acesso a dados do Sistema de Controle de EPI.
Usa SQLite (biblioteca padrão do Python, sem dependências externas).
"""

import sqlite3
import hashlib
import secrets
from datetime import date, timedelta
from contextlib import contextmanager

DB_PATH = "epi_control.db"


def _to_dicts(rows):
    """Converte uma lista de sqlite3.Row em dicts comuns.
    Necessário porque o Streamlit tenta copiar (deepcopy) os objetos usados em
    widgets como selectbox, e sqlite3.Row não suporta isso."""
    return [dict(r) for r in rows]


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

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                perfil TEXT NOT NULL DEFAULT 'RH',
                nome_completo TEXT
            );
            """
        )
    _seed_admin_padrao()


def _seed_admin_padrao():
    """Cria um usuário admin padrão na primeira execução, caso não exista nenhum usuário."""
    if not listar_usuarios():
        criar_usuario("admin", "admin123", perfil="Administrador", nome_completo="Administrador")


# ---------- FUNCIONÁRIOS ----------

def add_funcionario(nome, cargo, setor):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO funcionarios (nome, cargo, setor) VALUES (?, ?, ?)",
            (nome, cargo, setor),
        )


def get_funcionarios():
    with get_conn() as conn:
        return _to_dicts(conn.execute("SELECT * FROM funcionarios ORDER BY nome").fetchall())


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
        return _to_dicts(conn.execute("SELECT * FROM tipos_epi ORDER BY nome").fetchall())


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
        return _to_dicts(conn.execute(query).fetchall())


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


# ---------- AUTENTICAÇÃO DE USUÁRIOS ----------
# Observação: para um sistema real em produção, o ideal é usar uma biblioteca
# especializada como `passlib` ou `bcrypt`. Aqui usamos hashlib + salt (PBKDF2)
# para manter o projeto sem dependências externas além do Streamlit.

def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()


def criar_usuario(username, password, perfil="RH", nome_completo=""):
    """Cria um novo usuário. Lança ValueError se o username já existir."""
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO usuarios (username, password_hash, salt, perfil, nome_completo)
                   VALUES (?, ?, ?, ?, ?)""",
                (username.strip().lower(), password_hash, salt, perfil, nome_completo),
            )
    except sqlite3.IntegrityError:
        raise ValueError(f"Já existe um usuário com o username '{username}'.")


def listar_usuarios():
    with get_conn() as conn:
        return _to_dicts(conn.execute(
            "SELECT id, username, perfil, nome_completo FROM usuarios ORDER BY username"
        ).fetchall())


def excluir_usuario(usuario_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def verificar_login(username, password):
    """Retorna a linha do usuário se username/senha forem válidos, senão None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE username = ?", (username.strip().lower(),)
        ).fetchone()
    if row is None:
        return None
    if _hash_password(password, row["salt"]) == row["password_hash"]:
        return row
    return None


def alterar_senha(usuario_id, nova_senha):
    salt = secrets.token_hex(16)
    password_hash = _hash_password(nova_senha, salt)
    with get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET password_hash = ?, salt = ? WHERE id = ?",
            (password_hash, salt, usuario_id),
        )
