# -*- coding: utf-8 -*-
"""FF ManutenControl – aplicação Streamlit.

Versão compatível com Python 3.8+ (sem `match‑case`).

Estrutura:
• Funções pequenas e reutilizáveis
• Menu dinâmico com ícones Material Symbols
• Sem blocos if‑elif redundantes nem sintaxe exclusiva de Python >=3.10
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

from utils.auth import login_user, is_admin
from utils.image import get_image_base64
from utils.api import get_api_data
from pages import (
    dashboard,
    companies,
    machines,
    maintenances,
    users,
    settings,
)

# ----------------------------------------------------------------------------
# Configuração e utilitários
# ----------------------------------------------------------------------------
load_dotenv()
LOGO_PATH: str | None = os.getenv("LOGO_PATH")
DEFAULT_LOGO_PATH: str | None = os.getenv("DEFAULT_LOGO_PATH")

st.set_page_config(page_title="FF ManutenControl", layout="wide")

# ----------------------------------------------------------------------------
# Sessão
# ----------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# ----------------------------------------------------------------------------
# Páginas auxiliares
# ----------------------------------------------------------------------------

def login_screen() -> None:
    """Renderiza o ecrã de login e pára a execução se o utilizador não estiver autenticado."""
    st.markdown("<h1 style='text-align:center'>FF ManutenControl</h1>", unsafe_allow_html=True)

    if (logo64 := get_image_base64(LOGO_PATH)):
        st.markdown(
            f"""
            <div style='display:flex;justify-content:center'>
                <img src='data:image/png;base64,{logo64}' width='150' style='border-radius:50%;border:2px solid #ddd;box-shadow:2px 2px 10px rgba(0,0,0,.1)'>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<h4 style='text-align:center;color:gray'>Intelligent Fleet Management</h4>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if login_user(username, password):
                st.success("Login successful!")
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials or connection error.")
    st.stop()


def sidebar_user_info() -> None:
    """Preenche a sidebar com dados do utilizador e logotipo."""
    role = st.session_state.get("role", "unknown")
    username = st.session_state.get("username", "unknown")

    # Logótipo da empresa (se gestor de frota)
    company_logo_path = DEFAULT_LOGO_PATH
    if role == "fleet_manager" and (company_id := st.session_state.get("company_id")):
        for ext in (".png", ".jpg", ".jpeg"):
            path = os.path.join("frontend/images/company_logos", f"company_{company_id}{ext}")
            if os.path.exists(path):
                company_logo_path = path
                break
    st.sidebar.image(company_logo_path)
    st.sidebar.title("FleetPilot")

    full_name = st.session_state.get("full_name", username)
    st.sidebar.write(f"**Nome:** {full_name}")
    st.sidebar.write(f"**Função:** {role.replace('_', ' ').title()}")

    if role == "fleet_manager" and (company_id := st.session_state.get("company_id")):
        if company := get_api_data(f"companies/{company_id}"):
            st.sidebar.write(f"**Empresa:** {company['name']}")


def render_menu() -> None:
    """Constrói o menu horizontal com ícones e altera a página actual."""

    # CSS mínimo para estilizar botões
    st.markdown(
        """
        <style>
        div.stButton>button{background-color:#2c3e50;color:#fff;font-weight:bold;border:none;border-radius:6px;padding:8px 16px;width:100%;margin:0 4px}
        div.stButton>button:hover{background-color:#34495e}
        </style>
        """,
        unsafe_allow_html=True,
    )

    icons = {
        "Dashboard": ":material/stacked_bar_chart:",
        "Empresas": ":material/apartment:",
        "Máquinas": ":material/local_shipping:",
        "Manutenções": ":material/build:",
        "Faturação": ":material/receipt_long:",
        "Utilizadores": ":material/groups:",
        "Configurações": ":material/settings:",
    }

    cols = st.columns(7)
    layout = [
        ("Dashboard", "Dashboard", cols[0]),
        ("Empresas", "Companies", cols[1]),
        ("Máquinas", "Machines", cols[2]),
        ("Manutenções", "Maintenances", cols[3]),
        ("Faturação", "Billing", cols[4]),
    ]
    if is_admin():
        layout.extend(
            [
                ("Utilizadores", "Users", cols[5]),
                ("Configurações", "Settings", cols[6]),
            ]
        )
    else:
        layout.append(("Configurações", "Settings", cols[5]))

    for label, page_id, col in layout:
        with col:
            if st.button(
                label,
                key=f"btn_{page_id}",
                icon=icons[label],
                use_container_width=True,
            ):
                st.session_state.current_page = page_id
                st.rerun()

    # Botão de logout (fica abaixo do menu)
    if st.button("Sair", key="logout_btn", icon=":material/logout:"):
        st.session_state.clear()
        st.rerun()


def render_page(page: str) -> None:
    """Despacha para a página correta usando if/elif (compatível 3.8+)."""
    if page == "Dashboard":
        dashboard.show_dashboard()
    elif page == "Companies":
        companies.show_companies()
    elif page == "Machines":
        machines.show_machines()
    elif page == "Maintenances":
        maintenances.show_maintenances()
    elif page == "Users":
        if is_admin():
            users.show_users()
        else:
            st.error("Acesso restrito.")
    elif page == "Settings":
        settings.show_settings()
    elif page == "Billing":
        from frontend.pages.billing import show_billing
        show_billing()
    else:
        st.error("Página não encontrada.")


# ----------------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------------
if not st.session_state.logged_in:
    login_screen()

sidebar_user_info()
render_menu()
render_page(st.session_state.current_page)
