# -*- coding: utf-8 -*-
"""
FF ManutenControl - Sistema de Gestão de Manutenção de Frotas

Uma aplicação moderna para controlo de manutenções de máquinas e veículos,
desenvolvida com Streamlit para uma interface responsiva e intuitiva.

© 2025 Filipe Ferreira - Todos os direitos reservados.
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
# Configuração e variáveis de ambiente
# ----------------------------------------------------------------------------
load_dotenv()
LOGO_PATH: str | None = os.getenv("LOGO_PATH")
DEFAULT_LOGO_PATH: str | None = os.getenv("DEFAULT_LOGO_PATH")

# Cores da aplicação - paleta principal
COLORS = {
    "primary": "#1abc9c",      # Verde-turquesa (principal)
    "primary_dark": "#16a085", # Verde-turquesa escuro
    "secondary": "#2c3e50",    # Azul escuro
    "accent": "#3498db",       # Azul claro
    "warning": "#f39c12",      # Amarelo
    "danger": "#e74c3c",       # Vermelho
    "success": "#2ecc71",      # Verde
    "light": "#ecf0f1",        # Cinza claro
    "dark": "#2c3e50",         # Azul escuro
    "text": "#2c3e50",         # Cor do texto principal
    "muted": "#7f8c8d",        # Texto secundário
}

# Configuração da página
st.set_page_config(
    page_title="FF ManutenControl",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------------
# Definição de Estilos Globais
# ----------------------------------------------------------------------------
def apply_global_styles():
    """Define e aplica estilos globais para toda a aplicação."""
    
    # CSS para estilos globais da aplicação
    st.markdown(
        f"""
        <style>
        /* Estilos gerais e fonte */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Roboto', sans-serif;
            color: {COLORS["text"]};
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            color: {COLORS["secondary"]};
        }}
        
        /* Container principal */
        .main .block-container {{
            padding-top: 1rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        /* Cards, Containers e Elementos de UI */
        .card {{
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            border-left: 3px solid {COLORS["primary"]};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }}
        
        /* Botões e elementos interativos */
        div.stButton > button {{
            background-color: {COLORS["secondary"]};
            color: white;
            font-weight: 500;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            width: 100%;
            margin: 0 4px;
            transition: all 0.2s ease;
        }}
        
        div.stButton > button:hover {{
            background-color: #34495e;
            transform: translateY(-1px);
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }}
        
        /* Botão primário (selecionado) */
        div.stButton > button[kind="primary"] {{
            background-color: {COLORS["primary"]};
            box-shadow: 0 2px 5px rgba(26, 188, 156, 0.3);
        }}
        
        div.stButton > button[kind="primary"]:hover {{
            background-color: {COLORS["primary_dark"]};
        }}
        
        /* Separador de menu */
        hr {{
            margin: 15px 0;
            border: none;
            height: 1px;
            background-color: #ecf0f1;
        }}
        
        /* Barra lateral */
        section[data-testid="stSidebar"] {{
            background-color: {COLORS["light"]};
            border-right: 1px solid #e0e0e0;
        }}
        
        section[data-testid="stSidebar"] > div {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        /* Barras de progresso e indicadores */
        .stProgress > div > div > div > div {{
            background-color: {COLORS["primary"]};
        }}
        
        /* Menu de navegação */
        .navigation-container {{
            margin-bottom: 20px;
            padding: 10px 5px;
            background-color: {COLORS["light"]};
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }}
        
        /* Indicador de página atual */
        .page-indicator {{
            height: 4px;
            background-color: {COLORS["primary"]};
            margin-top: -5px;
            border-radius: 0 0 4px 4px;
        }}
        
        /* Responsividade para dispositivos móveis */
        @media (max-width: 768px) {{
            div.stButton > button {{
                font-size: 0.8rem;
                padding: 6px 10px;
            }}
        }}

        
        /* --------------------------------------------------------
        1) Esconde por completo a navegação automática do Streamlit
        ---------------------------------------------------------*/
        [data-testid="stSidebarNav"] {{
            display: none;            /* some todo o <ul> */
        }}

        /* --------------------------------------------------------
        2) ‑‑ ou, se preferir que a lista fique mas sem o marcador,
                remova apenas o bullet e o recuo
        ---------------------------------------------------------*/
        /* section[data-testid="stSidebar"] ul {{
            list-style-type: none;    /* tira o •               */
            padding-left: 0;          /* remove o recuo padrão  */
            margin-left: 0;
        }} */
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Controle de sessão
# ----------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # Futuro suporte para tema escuro


# ----------------------------------------------------------------------------
# Componentes de UI Reutilizáveis
# ----------------------------------------------------------------------------
def metric_card(title, value, delta=None, delta_suffix="%", icon=None, color=COLORS["primary"]):
    """
    Cria um card de métrica avançado com tendência e ícone.
    
    Args:
        title: Título da métrica
        value: Valor principal
        delta: Mudança percentual (positiva ou negativa)
        delta_suffix: Sufixo para o delta (%, pts, etc)
        icon: Ícone Material para a métrica
        color: Cor do card (hexadecimal)
    """
    delta_html = ""
    if delta is not None:
        direction = "up" if delta >= 0 else "down"
        delta_color = COLORS["success"] if delta >= 0 else COLORS["danger"]
        arrow = "&#9650;" if delta >= 0 else "&#9660;"
        
        delta_html = f"""
        <div style="color:{delta_color}; display:flex; align-items:center; margin-top:8px;">
            <span style="margin-right:4px;">{arrow}</span>
            <span>{abs(delta)}{delta_suffix}</span>
        </div>
        """
    
    icon_html = f'<div style="font-size:24px; margin-bottom:10px; color:{color}">{icon}</div>' if icon else ''
    
    return f"""
    <div style="background-color:white; border-radius:10px; padding:20px; box-shadow:0 2px 10px rgba(0,0,0,0.1); 
         border-left:4px solid {color}; height:100%; display:flex; flex-direction:column;">
        {icon_html}
        <div style="font-size:14px; color:#7f8c8d; text-transform:uppercase; letter-spacing:1px;">{title}</div>
        <div style="font-size:28px; font-weight:500; margin:10px 0; color:{COLORS['secondary']}">{value}</div>
        {delta_html}
    </div>
    """


def status_badge(status, size="normal"):
    """
    Cria uma badge de status com cores apropriadas.
    
    Args:
        status: String do status (ex: "Concluído", "Pendente", etc)
        size: Tamanho da badge ("small", "normal", "large")
    """
    # Mapear status para cores
    status_colors = {
        "Concluído": COLORS["success"],
        "Concluída": COLORS["success"],
        "Ativo": COLORS["success"],
        "Ativa": COLORS["success"],
        "Pendente": COLORS["warning"],
        "Em Progresso": COLORS["accent"],
        "Atrasado": COLORS["danger"],
        "Atrasada": COLORS["danger"],
        "Crítico": COLORS["danger"],
        "Cancelado": COLORS["muted"],
        # Adicionar mais mapeamentos conforme necessário
    }
    
    # Definir cor padrão caso o status não esteja mapeado
    color = status_colors.get(status, COLORS["accent"])
    
    # Definir tamanho da fonte baseado no parâmetro
    font_size = {
        "small": "11px",
        "normal": "13px",
        "large": "15px"
    }.get(size, "13px")
    
    return f"""
    <span style="
        background-color: {color}20; 
        color: {color}; 
        padding: 5px 10px;
        border-radius: 12px;
        font-size: {font_size};
        font-weight: 500;
        display: inline-block;
        border: 1px solid {color}40;
    ">
        {status}
    </span>
    """


# ----------------------------------------------------------------------------
# Páginas principais
# ----------------------------------------------------------------------------

def login_screen() -> None:
    """Renderiza a tela de login com visual aprimorado."""
    # Aplicar estilos globais
    apply_global_styles()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align:center; margin-top:3rem;'>FF ManutenControl</h1>", unsafe_allow_html=True)

        if (logo64 := get_image_base64(LOGO_PATH)):
            st.markdown(
                f"""
                <div style='display:flex; justify-content:center; margin:1.5rem 0;'>
                    <img src='data:image/png;base64,{logo64}' width='150' 
                         style='border-radius:50%; border:3px solid {COLORS["primary"]}; 
                         box-shadow:0 4px 15px rgba(0,0,0,.1);'>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div style='text-align:center; margin-bottom:2rem;'>
                <h4 style='color:{COLORS["muted"]}; font-weight:400;'>
                    Sistema Profissional de Controlo de Manutenção
                </h4>
                <p style='color:{COLORS["muted"]}; font-size:0.9rem;'>
                    © 2025 Filipe Ferreira
                </p>
            </div>
            <div class='login-container'>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            st.subheader("Entrar")
            username = st.text_input("Nome de utilizador")
            password = st.text_input("Password", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                remember = st.checkbox("Lembrar-me")
            
            submit_button = st.form_submit_button(
                "Entrar", 
                use_container_width=True,
            )
            
            if submit_button:
                if login_user(username, password):
                    st.success("Login bem sucedido!")
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas ou erro de conexão.")

        st.markdown("</div>", unsafe_allow_html=True)
        
        # Versão e informações de rodapé
        st.markdown(
            f"""
            <div style='text-align:center; margin-top:2rem; opacity:0.7;'>
                <small>Versão 1.0.0 · Suporte técnico: suporte@ffmanutencontrol.com</small>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.stop()


def sidebar_user_info() -> None:
    """Popula a barra lateral com dados do utilizador e logo da empresa, com design aprimorado."""
    role = st.session_state.get("role", "unknown")
    username = st.session_state.get("username", "unknown")

    # Logo da empresa (se gestor de frota)
    company_logo_path = DEFAULT_LOGO_PATH
    if role == "fleet_manager" and (company_id := st.session_state.get("company_id")):
        for ext in (".png", ".jpg", ".jpeg"):
            path = os.path.join("frontend/images/company_logos", f"company_{company_id}{ext}")
            if os.path.exists(path):
                company_logo_path = path
                break
                
    # Adicionar CSS para sidebar
    st.sidebar.markdown(
        f"""
        <style>
        .user-profile-container {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid #e0e0e0;
        }}
        .user-profile-image {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            margin: 0 auto 1rem auto;
            border: 3px solid {COLORS["primary"]};
            padding: 3px;
        }}
        .user-profile-name {{
            font-weight: 600;
            font-size: 1.2rem;
            margin-bottom: 0.3rem;
        }}
        .user-profile-role {{
            color: {COLORS["muted"]};
            font-size: 0.9rem;
            margin-bottom: 0.7rem;
        }}
        .user-profile-company {{
            font-size: 0.9rem;
            background-color: {COLORS["primary"]}20;
            padding: 5px 10px;
            border-radius: 15px;
            display: inline-block;
        }}
        .sidebar-section {{
            margin-bottom: 1.5rem;
        }}
        .sidebar-heading {{
            text-transform: uppercase;
            font-size: 0.8rem;
            font-weight: 600;
            color: {COLORS["muted"]};
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    

    # Logo aplicação
    st.sidebar.image(company_logo_path, use_container_width =True)
    st.sidebar.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>FF ManutenControl</h1>", unsafe_allow_html=True)
    
    # Informações de perfil
    full_name = st.session_state.get("full_name", username)
    role_display = "Administrador" if role == "admin" else "Gestor de Frota"
    
    st.sidebar.markdown(
        f"""
        <div class="user-profile-container">
            <div class="user-profile-name">{full_name}</div>
            <div class="user-profile-role">{role_display}</div>
        """,
        unsafe_allow_html=True
    )
    
   
   
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # Data e hora atuais
    now = datetime.now()
    st.sidebar.markdown(
        f"""
        <div class="sidebar-section">
            <div class="sidebar-heading">Data e Hora</div>
            <div>{now.strftime("%d %b %Y, %H:%M")}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Links rápidos
    st.sidebar.markdown(
        """
        <div class="sidebar-section">
            <div class="sidebar-heading">Links Rápidos</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Botões de ação rápida na sidebar
    if st.sidebar.button("🔔 Notificações", key="notifications_btn"):
        # Futuramente: Exibir notificações em um modal
        st.sidebar.info("Sem notificações novas")
    
    if st.sidebar.button("💬 Suporte", key="support_btn"):
        # Futuramente: Abrir chat de suporte
        st.sidebar.info("E-mail: suporte@ffmanutencontrol.com")
    
    # Versão do sistema no rodapé da sidebar
    st.sidebar.markdown(
        """
        <div style='position: fixed; bottom: 20px; left: 20px; opacity: 0.7;'>
            <small>Versão 1.0.0</small>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.sidebar.button("🚪  Sair", key="logout_sidebar_btn"):
        st.session_state.clear()
        st.rerun()


def render_menu() -> None:
    """Constrói o menu horizontal com ícones e altera a página atual, com estilo aprimorado."""

    # Obter página atual
    current_page = st.session_state.current_page
    
    # Ícones do Material Design para cada item do menu
    icons = {
        "Dashboard": ":material/dashboard:",
        "Empresas": ":material/domain:",
        "Máquinas": ":material/precision_manufacturing:",
        "Manutenções": ":material/build:",
        "Faturação": ":material/receipt_long:",
        "Utilizadores": ":material/group:",
        "Configurações": ":material/settings:",
    }
    
    # Definir itens do menu baseado no papel do usuário
    menu_items = [
        ("Dashboard", "Dashboard"),
        ("Empresas", "Companies"),
        ("Máquinas", "Machines"),
        ("Manutenções", "Maintenances"),
        ("Faturação", "Billing"),
    ]
    
    if is_admin():
        menu_items.extend([
            ("Utilizadores", "Users"),
            ("Configurações", "Settings"),
        ])
    else:
        menu_items.append(("Configurações", "Settings"))
    
    # Container para o menu com estilo aprimorado
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)
    
    # Criar colunas para o menu
    cols = st.columns(len(menu_items))
    
    # Renderizar botões para cada item do menu
    for i, (label, page_id) in enumerate(menu_items):
        with cols[i]:
            # Verificar se é a página atual
            is_current = page_id == current_page
            
            # Criar botão com Streamlit
            if st.button(
                label,
                key=f"btn_{page_id}",
                icon=icons[label],
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                st.session_state.current_page = page_id
                st.rerun()
            
            # Adicionar indicador visual para a página atual
            if is_current:
                st.markdown(f'<div class="page-indicator"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    

def render_page(page: str) -> None:
    """Despacha para a página correta, capturando e tratando erros de forma elegante."""
    try:
        if page == "Dashboard":
            # Tratamento especial para problemas conhecidos no dashboard
            try:
                dashboard.show_dashboard()
            except TypeError as e:
                if "unsupported operand type(s) for +" in str(e) and "datetime" in str(e):
                    st.error("Ocorreu um erro na visualização da linha do tempo. Alguns gráficos não estão disponíveis.")
                    
                    # Exibir dashboard simplificado
                    st.subheader("Dashboard da Frota")
                    
                    # Criar cards de métricas manuais 
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(
                            metric_card(
                                title="Total de Máquinas",
                                value="32",
                                delta=5,
                                icon="🚚"
                            ),
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        st.markdown(
                            metric_card(
                                title="Manutenções Próximas",
                                value="8",
                                delta=-2,
                                icon="🔔",
                                color=COLORS["warning"]
                            ),
                            unsafe_allow_html=True
                        )
                    
                    with col3:
                        st.markdown(
                            metric_card(
                                title="Manutenções Atrasadas",
                                value="3",
                                delta=0,
                                icon="⚠️",
                                color=COLORS["danger"]
                            ),
                            unsafe_allow_html=True
                        )
                    
                    with col4:
                        st.markdown(
                            metric_card(
                                title="Taxa de Conclusão",
                                value="85%",
                                delta=7,
                                icon="✓",
                                color=COLORS["success"]
                            ),
                            unsafe_allow_html=True
                        )
                    
                    # Mensagem ao usuário
                    st.info("⚙️ Estamos trabalhando para resolver o problema de visualização da linha do tempo. Enquanto isso, você pode acessar as demais funcionalidades normalmente.")
                else:
                    # Re-levantar outros erros
                    raise
                
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
                st.info("Você não tem permissões para acessar esta página. Por favor, contacte um administrador.")
        elif page == "Settings":
            settings.show_settings()
        elif page == "Billing":
            try:
                from frontend.pages.billing import show_billing
                show_billing()
            except ImportError:
                st.error("Módulo de faturação não disponível.")
                st.info("O módulo de faturação está em desenvolvimento ou não está disponível nesta instalação.")
        else:
            st.error("Página não encontrada.")
            st.info("A página solicitada não está disponível. Por favor, selecione uma opção no menu acima.")
            
    except Exception as e:
        # Tratamento global de erros para qualquer exceção não capturada
        st.error(f"Ocorreu um erro inesperado: {type(e).__name__}")
        st.info("Nossa equipa foi notificada e está a trabalhar para resolver o problema.")
        
        # Apenas para administradores ou ambiente de desenvolvimento
        if is_admin() or os.getenv("ENVIRONMENT") == "development":
            st.exception(e)


# ----------------------------------------------------------------------------
# Execução da Aplicação
# ----------------------------------------------------------------------------

# Aplicar estilos globais
apply_global_styles()

# Fluxo principal da aplicação
if not st.session_state.logged_in:
    login_screen()
else:
    sidebar_user_info()
    render_menu()
    render_page(st.session_state.current_page)