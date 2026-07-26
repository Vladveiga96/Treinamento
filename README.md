# 🦺 Sistema de Controle de EPI

Projeto de portfólio em Python para controle de entrega, validade e devolução de
Equipamentos de Proteção Individual (EPI), pensado para o contexto de uma planta
industrial/siderúrgica (capacete, luva, protetor auricular, botina, óculos, etc).

## Funcionalidades

- Cadastro de funcionários (nome, cargo, setor)
- Cadastro de tipos de EPI com prazo de validade em dias
- Registro de entrega de EPI a um funcionário (a validade é calculada automaticamente)
- Painel com status de cada entrega:
  - 🟢 **Válido**
  - 🟡 **Próximo do vencimento** (15 dias ou menos para vencer)
  - 🔴 **Vencido**
  - ⚪ **Devolvido**
- Registro de devolução/troca de EPI
- Dashboard com métricas gerais e alertas de EPIs vencidos

## Tecnologias

- **Python 3.10+**
- **SQLite** (`sqlite3`, biblioteca padrão — sem necessidade de instalar banco de dados)
- **Streamlit** (interface web)

## Estrutura do projeto

```
controle_epi/
├── app.py            # Interface Streamlit (telas e navegação)
├── database.py        # Camada de acesso a dados (SQLite)
├── requirements.txt    # Dependências
├── epi_control.db      # Banco de dados (criado automaticamente na 1ª execução)
└── README.md
```

## Como rodar

```bash
# 1. Crie e ative um ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode a aplicação
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

## Possíveis evoluções (ideias para continuar o projeto)

- Autenticação de usuários (login para RH/segurança do trabalho)
- Exportação de relatórios em PDF ou Excel
- Envio de e-mail/WhatsApp automático quando um EPI estiver próximo do vencimento
- Leitura de EPI por código de barras/QR Code (entrega mais rápida)
- Deploy em nuvem (Streamlit Community Cloud, Render, etc.) para acesso remoto
- Troca do SQLite por PostgreSQL para uso em produção com múltiplos usuários simultâneos

## Sobre o projeto

Este sistema foi desenvolvido como projeto de portfólio para demonstrar:
- Modelagem de banco de dados relacional (funcionários, EPIs, entregas)
- Separação de responsabilidades (camada de dados x camada de interface)
- Construção de dashboards interativos com Python
- Aplicação prática de um problema real de segurança do trabalho na indústria
