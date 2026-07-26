"""
app.py
Sistema de Controle de EPI - Interface Streamlit
Projeto de portfólio: controle de entrega, validade e devolução de
Equipamentos de Proteção Individual (EPI) em uma planta industrial/siderúrgica.

Para rodar:
    pip install streamlit
    streamlit run app.py
"""

import streamlit as st
from datetime import date

import database as db

st.set_page_config(page_title="Controle de EPI", page_icon="🦺", layout="wide")

db.init_db()

STATUS_COLOR = {
    "Válido": "🟢",
    "Próximo do vencimento": "🟡",
    "Vencido": "🔴",
    "Devolvido": "⚪",
}


# ---------------------------------------------------------------------------
# AUTENTICAÇÃO
# ---------------------------------------------------------------------------
def tela_login():
    st.title("🦺 Sistema de Controle de EPI")
    st.subheader("🔐 Login")

    st.info(
        "Primeiro acesso? Use o usuário padrão **admin** / senha **admin123** "
        "e depois crie os usuários da sua equipe em '🔑 Usuários'."
    )

    with st.form("form_login"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        usuario = db.verificar_login(username, password)
        if usuario:
            st.session_state["usuario"] = {
                "id": usuario["id"],
                "username": usuario["username"],
                "perfil": usuario["perfil"],
                "nome_completo": usuario["nome_completo"],
            }
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


if "usuario" not in st.session_state:
    tela_login()
    st.stop()

usuario_logado = st.session_state["usuario"]

# ---------------------------------------------------------------------------
# APP PRINCIPAL (usuário autenticado)
# ---------------------------------------------------------------------------
st.title("🦺 Sistema de Controle de EPI")
st.caption("Controle de entrega, validade e devolução de Equipamentos de Proteção Individual")

st.sidebar.success(f"👤 {usuario_logado['nome_completo'] or usuario_logado['username']}")
st.sidebar.caption(f"Perfil: {usuario_logado['perfil']}")
if st.sidebar.button("Sair"):
    del st.session_state["usuario"]
    st.rerun()
st.sidebar.divider()

opcoes_menu = ["📊 Dashboard", "👷 Funcionários", "🧰 Tipos de EPI", "📦 Registrar Entrega", "📋 Entregas"]
if usuario_logado["perfil"] == "Administrador":
    opcoes_menu.append("🔑 Usuários")

menu = st.sidebar.radio("Menu", opcoes_menu)

# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------
if menu == "📊 Dashboard":
    entregas = db.get_entregas()
    total = len(entregas)
    vencidos = sum(1 for e in entregas if db.status_entrega(e["data_validade"], e["devolvido"]) == "Vencido")
    proximos = sum(
        1 for e in entregas if db.status_entrega(e["data_validade"], e["devolvido"]) == "Próximo do vencimento"
    )
    validos = sum(1 for e in entregas if db.status_entrega(e["data_validade"], e["devolvido"]) == "Válido")
    devolvidos = sum(1 for e in entregas if e["devolvido"] == 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de entregas", total)
    c2.metric("🟢 Válidos", validos)
    c3.metric("🟡 Próx. do vencimento", proximos)
    c4.metric("🔴 Vencidos", vencidos)
    c5.metric("⚪ Devolvidos", devolvidos)

    if vencidos > 0:
        st.error(f"⚠️ Existem {vencidos} EPI(s) vencido(s) em uso! Providencie a troca imediatamente.")
    if proximos > 0:
        st.warning(f"Atenção: {proximos} EPI(s) estão próximos do vencimento.")

    st.subheader("Funcionários por setor")
    funcionarios = db.get_funcionarios()
    if funcionarios:
        setores = {}
        for f in funcionarios:
            setores[f["setor"] or "Sem setor"] = setores.get(f["setor"] or "Sem setor", 0) + 1
        st.bar_chart(setores)
    else:
        st.info("Nenhum funcionário cadastrado ainda.")

# ---------------------------------------------------------------------------
# FUNCIONÁRIOS
# ---------------------------------------------------------------------------
elif menu == "👷 Funcionários":
    st.subheader("Cadastrar novo funcionário")
    with st.form("form_funcionario", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        nome = col1.text_input("Nome")
        cargo = col2.text_input("Cargo")
        setor = col3.text_input("Setor")
        submitted = st.form_submit_button("Cadastrar")
        if submitted:
            if nome.strip():
                db.add_funcionario(nome.strip(), cargo.strip(), setor.strip())
                st.success(f"Funcionário '{nome}' cadastrado com sucesso!")
            else:
                st.error("O nome é obrigatório.")

    st.subheader("Funcionários cadastrados")
    funcionarios = db.get_funcionarios()
    if funcionarios:
        st.dataframe(
            [{"ID": f["id"], "Nome": f["nome"], "Cargo": f["cargo"], "Setor": f["setor"]} for f in funcionarios],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum funcionário cadastrado ainda.")

# ---------------------------------------------------------------------------
# TIPOS DE EPI
# ---------------------------------------------------------------------------
elif menu == "🧰 Tipos de EPI":
    st.subheader("Cadastrar novo tipo de EPI")
    with st.form("form_epi", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome do EPI (ex: Capacete, Luva de Raspa)")
        validade = col2.number_input("Validade (dias)", min_value=1, value=180, step=1)
        submitted = st.form_submit_button("Cadastrar")
        if submitted:
            if nome.strip():
                db.add_tipo_epi(nome.strip(), int(validade))
                st.success(f"EPI '{nome}' cadastrado com sucesso!")
            else:
                st.error("O nome do EPI é obrigatório.")

    st.subheader("Tipos de EPI cadastrados")
    epis = db.get_tipos_epi()
    if epis:
        st.dataframe(
            [{"ID": e["id"], "Nome": e["nome"], "Validade (dias)": e["validade_dias"]} for e in epis],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum tipo de EPI cadastrado ainda.")

# ---------------------------------------------------------------------------
# REGISTRAR ENTREGA
# ---------------------------------------------------------------------------
elif menu == "📦 Registrar Entrega":
    funcionarios = db.get_funcionarios()
    epis = db.get_tipos_epi()

    if not funcionarios or not epis:
        st.warning("Cadastre ao menos um funcionário e um tipo de EPI antes de registrar uma entrega.")
    else:
        st.subheader("Registrar entrega de EPI")
        with st.form("form_entrega", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            func_opcao = col1.selectbox(
                "Funcionário", options=funcionarios, format_func=lambda f: f["nome"]
            )
            epi_opcao = col2.selectbox(
                "Tipo de EPI", options=epis, format_func=lambda e: f'{e["nome"]} ({e["validade_dias"]} dias)'
            )
            data_entrega = col3.date_input("Data da entrega", value=date.today())
            submitted = st.form_submit_button("Registrar entrega")
            if submitted:
                db.add_entrega(func_opcao["id"], epi_opcao["id"], data_entrega)
                st.success("Entrega registrada com sucesso!")

# ---------------------------------------------------------------------------
# ENTREGAS
# ---------------------------------------------------------------------------
elif menu == "📋 Entregas":
    st.subheader("Entregas registradas")
    apenas_ativas = st.checkbox("Mostrar apenas entregas ativas (não devolvidas)", value=True)
    entregas = db.get_entregas(apenas_ativas=apenas_ativas)

    if not entregas:
        st.info("Nenhuma entrega encontrada.")
    else:
        for e in entregas:
            status = db.status_entrega(e["data_validade"], e["devolvido"])
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                col1.write(f"**{e['funcionario']}**  \n{e['setor'] or '-'}")
                col2.write(f"**EPI:** {e['epi']}")
                col3.write(f"Entrega: {e['data_entrega']}  \nValidade: {e['data_validade']}")
                col4.write(f"{STATUS_COLOR.get(status, '')} {status}")
                if not e["devolvido"]:
                    if col5.button("Devolver", key=f"dev_{e['id']}"):
                        db.devolver_entrega(e["id"], date.today())
                        st.rerun()
                else:
                    col5.write(f"✅ {e['data_devolucao']}")

# ---------------------------------------------------------------------------
# USUÁRIOS (apenas Administrador)
# ---------------------------------------------------------------------------
elif menu == "🔑 Usuários":
    st.subheader("Criar novo usuário")
    with st.form("form_usuario", clear_on_submit=True):
        col1, col2 = st.columns(2)
        novo_username = col1.text_input("Usuário (login)")
        nova_senha = col2.text_input("Senha", type="password")
        col3, col4 = st.columns(2)
        nome_completo = col3.text_input("Nome completo")
        perfil = col4.selectbox("Perfil", ["RH", "Segurança do Trabalho", "Administrador"])
        submitted = st.form_submit_button("Criar usuário")
        if submitted:
            if not novo_username.strip() or not nova_senha:
                st.error("Usuário e senha são obrigatórios.")
            elif len(nova_senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    db.criar_usuario(novo_username, nova_senha, perfil=perfil, nome_completo=nome_completo)
                    st.success(f"Usuário '{novo_username}' criado com sucesso!")
                except ValueError as e:
                    st.error(str(e))

    st.subheader("Usuários cadastrados")
    usuarios = db.listar_usuarios()
    for u in usuarios:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"**{u['nome_completo'] or u['username']}**  \n@{u['username']}")
            col2.write(f"Perfil: {u['perfil']}")
            eh_o_proprio = u["id"] == usuario_logado["id"]
            if col4.button("Excluir", key=f"del_user_{u['id']}", disabled=eh_o_proprio):
                db.excluir_usuario(u["id"])
                st.rerun()
            if eh_o_proprio:
                col3.caption("(você)")
