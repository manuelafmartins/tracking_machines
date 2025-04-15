# frontend/app.py
import streamlit as st
from utils.auth import check_authentication, login_screen
from utils.ui import setup_page_config
from pages.dashboard import show_dashboard
from pages.companies import show_companies
from pages.machines import show_machines
from pages.maintenances import show_maintenances
from pages.users import show_users
from pages.settings import show_settings
import os

# Configuração da página
setup_page_config()

# Inicializar Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Verificar autenticação
if not check_authentication():
    # Mostrar tela de login
    login_screen()
    st.stop()

# Sidebar com informações do usuário e navegação
def sidebar_navigation():
    from utils.api import get_api_data
    from utils.ui import get_company_logo_path
    import os
    
    # Obter logo da empresa ou logo padrão
    user_role = st.session_state.get("role", "unknown")
    company_logo_path = "frontend/images/logo.png"  # Logo padrão
    
    if user_role == "fleet_manager" and st.session_state.get("company_id"):
        company_id = st.session_state.get("company_id")
        
        # Verificar se existe um arquivo de logo para esta empresa
        possible_extensions = ['.png', '.jpg', '.jpeg']
        for ext in possible_extensions:
            potential_logo_path = os.path.join("frontend/images/company_logos", f"company_{company_id}{ext}")
            if os.path.exists(potential_logo_path):
                company_logo_path = potential_logo_path
                break
    
    st.sidebar.image(company_logo_path)
    st.sidebar.title("FleetPilot")
    
    # Informações do usuário
    with st.sidebar.container():
        username = st.session_state.get("username", "unknown")
        full_name = st.session_state.get("full_name", username)
        st.write(f"**Nome:** {full_name}")
        st.write(f"**Função:** {user_role.replace('_', ' ').title()}")
        
        if user_role == "fleet_manager" and st.session_state.get("company_id"):
            # Buscar nome da empresa
            company = get_api_data(f"companies/{st.session_state['company_id']}")
            if company:
                st.write(f"**Empresa:** {company['name']}")
    
    # Estilos para os botões
    st.markdown("""
    <style>
        div.stButton > button {
            background-color: #2c3e50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            margin: 0px 5px;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #34495e;
        }
        div.stButton > button:focus {
            background-color: #3498db;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Criar uma linha de botões para o menu
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        dashboard_btn = st.button("Dashboard")
    with col2:
        companies_btn = st.button("Empresas")
    with col3:
        machines_btn = st.button("Máquinas")
    with col4:
        maintenances_btn = st.button("Manutenções")

    # Adicionar o botão "Usuários" apenas para admins
    is_admin = st.session_state.get("role") == "admin"
    if is_admin:
        with col5:
            users_btn = st.button("Usuários")
        with col6:
            settings_btn = st.button("Configurações")
    else:
        with col5:
            settings_btn = st.button("Configurações")
        with col6:
            users_btn = False

    # Botão de logout
    logout_btn = st.button("Sair")
    
    # Controlar qual página está sendo exibida
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"

    # Atualizar a página atual com base nos botões clicados
    if dashboard_btn:
        st.session_state["current_page"] = "Dashboard"
        st.rerun()
    elif companies_btn:
        st.session_state["current_page"] = "Companies"
        st.rerun()
    elif machines_btn:
        st.session_state["current_page"] = "Machines"
        st.rerun()
    elif maintenances_btn:
        st.session_state["current_page"] = "Maintenances"
        st.rerun()
    elif users_btn:
        st.session_state["current_page"] = "Users"
        st.rerun()
    elif settings_btn:
        st.session_state["current_page"] = "Settings"
        st.rerun()
    elif logout_btn:
        # Limpar todas as variáveis de sessão
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        
    return st.session_state["current_page"]

# Exibir a navegação da sidebar
menu = sidebar_navigation()

# Exibir a página apropriada com base na seleção
if menu == "Dashboard":
    show_dashboard()
elif menu == "Companies":
    show_companies()
elif menu == "Machines":
    show_machines()
elif menu == "Maintenances":
    show_maintenances()
elif menu == "Users" and st.session_state.get("role") == "admin":
    show_users()
elif menu == "Settings":
    show_settings()