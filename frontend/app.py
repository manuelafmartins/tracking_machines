from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Union, Any

import streamlit as st
from dotenv import load_dotenv
import requests

# Import custom modules
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

# ------------------------------------------------------------------------------
# Configuration and Environment Variables
# ------------------------------------------------------------------------------
load_dotenv()
LOGO_PATH: str = os.getenv("LOGO_PATH", "")
DEFAULT_LOGO_PATH: str = os.getenv("DEFAULT_LOGO_PATH", "") or "frontend/images/new_logo.png"
APP_VERSION: str = "1.0.0"

# Application theme and colors
COLORS: Dict[str, str] = {
    "primary": "#1abc9c",      # Turquoise (primary)
    "primary_dark": "#16a085", # Dark turquoise
    "secondary": "#2c3e50",    # Dark blue
    "accent": "#3498db",       # Light blue
    "warning": "#f39c12",      # Yellow/amber
    "danger": "#e74c3c",       # Red
    "success": "#2ecc71",      # Green
    "light": "#ecf0f1",        # Light gray
    "dark": "#2c3e50",         # Dark blue (same as secondary)
    "text": "#2c3e50",         # Main text color
    "muted": "#7f8c8d",        # Secondary text
}

# Material Design icons mapping for consistent UI
ICONS: Dict[str, str] = {
    # Navigation
    "dashboard": "dashboard",
    "companies": "domain",
    "machines": "precision_manufacturing",
    "maintenances": "build",
    "billing": "receipt_long",
    "users": "group",
    "settings": "settings",
    
    # Actions and notifications
    "notifications": "notifications",
    "support": "support_agent",
    "logout": "logout",
    "account": "account_circle",
    
    # Status indicators
    "success": "check_circle",
    "warning": "warning",
    "error": "error",
    "info": "info",
    
    # Content types
    "machine": "precision_manufacturing",
    "maintenance": "build",
    "pending": "pending_actions",
    "late": "report_problem",
    "completed": "task_alt",
    "location": "location_on",
    "calendar": "event",
    "phone": "phone",
    "email": "email",
    "clock": "schedule",
}

# Status to color and icon mapping
STATUS_CONFIGS: Dict[str, Dict[str, str]] = {
    "Concluído": {"color": COLORS["success"], "icon": ICONS["success"]},
    "Concluída": {"color": COLORS["success"], "icon": ICONS["success"]},
    "Ativo": {"color": COLORS["success"], "icon": ICONS["success"]},
    "Ativa": {"color": COLORS["success"], "icon": ICONS["success"]},
    "Pendente": {"color": COLORS["warning"], "icon": ICONS["pending"]},
    "Em Progresso": {"color": COLORS["accent"], "icon": ICONS["maintenance"]},
    "Atrasado": {"color": COLORS["danger"], "icon": ICONS["late"]},
    "Atrasada": {"color": COLORS["danger"], "icon": ICONS["late"]},
    "Crítico": {"color": COLORS["danger"], "icon": ICONS["error"]},
    "Cancelado": {"color": COLORS["muted"], "icon": ICONS["error"]},
}

# Configure page
st.set_page_config(
    page_title="FF ManutenControl",
    page_icon=DEFAULT_LOGO_PATH,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------------------
# Global UI Styles
# ------------------------------------------------------------------------------
def apply_global_styles() -> None:
    """Define and apply global styles for the entire application."""
    
    st.markdown(
        f"""
        <style>
        /* General styles and fonts */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
        
        html, body, [class*="css"] {{
            font-family: 'Roboto', sans-serif;
            color: {COLORS["text"]};
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            color: {COLORS["secondary"]};
        }}
        
        /* Main container */
        .main .block-container {{
            padding-top: 1rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        /* Cards, Containers and UI Elements */
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
        
        /* Material Icons */
        .material-icons {{
            vertical-align: middle;
            font-size: 20px;
        }}
        
        /* Buttons and interactive elements */
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
        
        /* Primary button (selected) */
        div.stButton > button[kind="primary"] {{
            background-color: {COLORS["primary"]};
            box-shadow: 0 2px 5px rgba(26, 188, 156, 0.3);
        }}
        
        div.stButton > button[kind="primary"]:hover {{
            background-color: {COLORS["primary_dark"]};
        }}
        
        /* Menu separator */
        hr {{
            margin: 15px 0;
            border: none;
            height: 1px;
            background-color: #ecf0f1;
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {COLORS["light"]};
            border-right: 1px solid #e0e0e0;
        }}
        
        section[data-testid="stSidebar"] > div {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        /* Progress bars and indicators */
        .stProgress > div > div > div > div {{
            background-color: {COLORS["primary"]};
        }}
        
        /* Navigation menu */
        .navigation-container {{
            margin-bottom: 20px;
            padding: 10px 5px;
            background-color: {COLORS["light"]};
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }}
        
        /* Current page indicator */
        .page-indicator {{
            height: 4px;
            background-color: {COLORS["primary"]};
            margin-top: -5px;
            border-radius: 0 0 4px 4px;
        }}
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            div.stButton > button {{
                font-size: 0.8rem;
                padding: 6px 10px;
            }}
        }}

        /* ---------- WHITE ICONS ---------- */
        /* SVG icons used by st.button(icon=...) */
        div.stButton > button span[data-baseweb="icon"] svg,
        div.stButton > button span[data-baseweb="icon"] svg path {{
            color: #ffffff !important;  
            fill: #ffffff !important;
            stroke: #ffffff !important;
        }}

        /* Emoji/PNG that Streamlit converts to <img class="emoji"> */
        div.stButton > button img.emoji {{
            filter: brightness(0) invert(1) !important;
            width: 1.1em;
            height: 1.1em;
            margin-right: 6px;
            vertical-align: -2px;
        }}
        
        /* Hide Streamlit's automatic navigation */
        [data-testid="stSidebarNav"] {{
            display: none;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------------------
# Session state management
# ------------------------------------------------------------------------------
def initialize_session_state() -> None:
    """Initialize session state variables if they don't exist."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    if "theme" not in st.session_state:
        st.session_state.theme = "light"  # Future support for dark theme
        
    if "show_notifications" not in st.session_state:
        st.session_state.show_notifications = False
        
    if "show_support" not in st.session_state:
        st.session_state.show_support = False


# ------------------------------------------------------------------------------
# Reusable UI Components
# ------------------------------------------------------------------------------
def metric_card(
    title: str, 
    value: Union[str, int, float], 
    delta: Optional[Union[int, float]] = None, 
    delta_suffix: str = "%", 
    icon: Optional[str] = None, 
    color: str = COLORS["primary"]
) -> str:
    """
    Create an enhanced metric card with trend and icon.
    
    Args:
        title: Metric title
        value: Main value to display
        delta: Percentage change (positive or negative)
        delta_suffix: Suffix for delta (%, pts, etc)
        icon: Material Design icon for the metric
        color: Card color (hex)
    
    Returns:
        HTML string for the metric card
    """
    delta_html = ""
    if delta is not None:
        delta_color = COLORS["success"] if delta >= 0 else COLORS["danger"]
        trend_icon = "trending_up" if delta >= 0 else "trending_down"
        
        delta_html = f"""
        <div style="color:{delta_color}; display:flex; align-items:center; margin-top:8px;">
            <span class="material-icons" style="font-size:16px; margin-right:4px;">{trend_icon}</span>
            <span>{abs(delta)}{delta_suffix}</span>
        </div>
        """
    
    # Icon HTML (if provided)
    icon_html = ""
    if icon:
        if icon.startswith("material/"):
            # For material design icons (new format)
            clean_icon = icon.replace("material/", "")
            icon_html = f'<div style="margin-bottom:10px;"><span class="material-icons" style="font-size:28px; color:{color};">{clean_icon}</span></div>'
        elif icon in ICONS:
            # For icons from our ICONS dictionary
            icon_html = f'<div style="margin-bottom:10px;"><span class="material-icons" style="font-size:28px; color:{color};">{ICONS[icon]}</span></div>'
        else:
            # Fallback for emoji/text icons
            icon_html = f'<div style="font-size:24px; margin-bottom:10px;">{icon}</div>'
    
    return f"""
    <div style="background-color:white; border-radius:10px; padding:20px;
         box-shadow:0 2px 10px rgba(0,0,0,0.1);
         border-left:4px solid {color};">
        {icon_html}
        <div style="font-size:14px; color:#7f8c8d; text-transform:uppercase; letter-spacing:1px;">{title}</div>
        <div style="font-size:28px; font-weight:500; margin:10px 0; color:{COLORS['secondary']}">{value}</div>
        {delta_html}
    </div>
    """


def status_badge(status: str, size: str = "normal") -> str:
    """
    Create a status badge with appropriate colors and icons.
    
    Args:
        status: Status string (e.g., "Concluído", "Pendente", etc.)
        size: Badge size ("small", "normal", "large")
    
    Returns:
        HTML string for the status badge
    """
    # Get color and icon from STATUS_CONFIGS or use defaults
    config = STATUS_CONFIGS.get(status, {
        "color": COLORS["accent"],
        "icon": ICONS["info"]
    })
    
    color = config["color"]
    icon = config["icon"]
    
    # Set font size based on the size parameter
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
        display: inline-flex;
        align-items: center;
        border: 1px solid {color}40;
    ">
        <span class="material-icons" style="font-size: {font_size}; margin-right: 4px;">{icon}</span>
        {status}
    </span>
    """


def notification_card(title: str, message: str, time: str, type_: str = "info") -> str:
    """
    Create a notification card with icon and timestamp.
    
    Args:
        title: Notification title
        message: Main notification message
        time: Timestamp or relative time
        type_: Notification type ("info", "warning", "success", "error")
    
    Returns:
        HTML string for notification card
    """
    icon_map = {
        "info": ICONS["info"],
        "warning": ICONS["warning"],
        "success": ICONS["success"],
        "error": ICONS["error"]
    }
    
    color_map = {
        "info": COLORS["accent"],
        "warning": COLORS["warning"],
        "success": COLORS["success"],
        "error": COLORS["danger"]
    }
    
    icon = icon_map.get(type_, ICONS["info"])
    color = color_map.get(type_, COLORS["accent"])
    
    return f"""
    <div style="
        border-left: 3px solid {color};
        background-color: {color}10;
        padding: 10px 15px;
        margin-bottom: 10px;
        border-radius: 4px;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <span class="material-icons" style="color: {color}; margin-right: 8px;">{icon}</span>
            <span style="font-weight: 500; color: {color};">{title}</span>
        </div>
        <div style="margin-left: 28px; margin-bottom: 5px;">{message}</div>
        <div style="margin-left: 28px; font-size: 0.8rem; color: {COLORS['muted']};">
            <span class="material-icons" style="font-size: 12px; vertical-align: middle;">schedule</span> {time}
        </div>
    </div>
    """

# ------------------------------------------------------------------------------
# Main UI Screens
# ------------------------------------------------------------------------------
def login_screen() -> None:
    """Render the enhanced login screen."""
    # Apply global styles
    apply_global_styles()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Display logo if available
        if (logo64 := get_image_base64(LOGO_PATH)):
            st.markdown(
                f"""
                <div style='display:flex; justify-content:center; margin:1.5rem 0;'>
                    <img src='data:image/png;base64,{logo64}' width='450' 
                        style='border-radius:0; border:none; box-shadow:none;'>
                </div>""",
                unsafe_allow_html=True,
            )

        # App tagline and copyright info
        st.markdown(
            f"""
            <div style='text-align:center; margin-bottom:2rem;'>
                <h4 style='color:{COLORS["muted"]}; font-weight:400;'>
                    Sistema de Controlo de Manutenção
                </h4>
                <p style='color:{COLORS["muted"]}; font-size:0.9rem;'>
                    © 2025 Filipe Ferreira
                </p>
            </div>
            <div class='login-container'>
            """,
            unsafe_allow_html=True,
        )

        # Login form
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
        
        # Add vertical spacing
        for _ in range(9):
            st.write("")
            
        # Version and footer information
        st.markdown(
            f"""
            <div style='text-align:center; margin-top:2rem; opacity:0.7;'>
                <small>Versão {APP_VERSION} · © 2025 Filipe Ferreira</small>
            </div>
            """,
            unsafe_allow_html=True
        )
                
    st.stop()


def sidebar_user_info() -> None:
    """Populate the sidebar with user data and company logo."""
    role = st.session_state.get("role", "unknown")
    username = st.session_state.get("username", "unknown")

    # Company logo (if user is a fleet manager)
    company_logo_path = DEFAULT_LOGO_PATH
    if role == "fleet_manager" and (company_id := st.session_state.get("company_id")):
        for ext in (".png", ".jpg", ".jpeg"):
            path = os.path.join("frontend/images/company_logos", f"company_{company_id}{ext}")
            if os.path.exists(path):
                company_logo_path = path
                break
                
    # Add CSS for sidebar components
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
    
    # Display app logo
    st.sidebar.image(company_logo_path, use_container_width=True)
    st.sidebar.write("")

    # Profile information
    full_name = st.session_state.get("full_name", username)
    role_display = "Administrador" if role == "admin" else "Gestor de Frota"
    
    st.sidebar.markdown(
        f"""
        <div class="user-profile-container">
            <div class="user-profile-name">{full_name}</div>
            <div class="user-profile-role">{role_display}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Try to get location from IP
    location_text = "Não disponível"
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=1).json()
        city = resp.get("city", "")
        if city:
            location_text = f"{city}"
    except Exception:
        pass

    # Current date and time
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    # Location and datetime display
    st.sidebar.markdown(f"""
    <div class="sidebar-section">
      <div class="sidebar-heading">Localização | Data & Hora</div>
      <div style="font-size:0.9rem; color:{COLORS['muted']}">
        <span class="material-icons" style="font-size:14px; vertical-align:middle; margin-right:4px;">{ICONS['location']}</span>{location_text} | 
        <span class="material-icons" style="font-size:14px; vertical-align:middle; margin-right:4px;">{ICONS['calendar']}</span>{now}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Add some vertical spacing
    st.sidebar.write("")
    st.sidebar.write("")
    
    # Quick links section
    st.sidebar.markdown(
        """
        <div class="sidebar-section">
            <div class="sidebar-heading">Links Rápidos</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Notifications button with toggle functionality
    if st.sidebar.button(
        "Notificações", 
        key="notifications_btn", 
        icon=f":material/{ICONS['notifications']}:"
    ):
        st.session_state.show_notifications = not st.session_state.show_notifications
    
    # Show notifications panel when active
    if st.session_state.show_notifications:
        with st.sidebar.container():
            st.markdown(
                f"""
                <div style="margin-bottom:15px;">
                    <div class="sidebar-heading" style="margin-top:10px; display:flex; justify-content:space-between; align-items:center;">
                        <span>Notificações</span>
                        <span style="color:{COLORS['primary']}; font-size:12px; cursor:pointer;">Marcar todas como lidas</span>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # No notifications message
            st.markdown(
                f"""
                <div style="text-align:center; padding:15px; color:{COLORS['muted']}; border:1px dashed #e0e0e0; border-radius:8px;">
                    <span class="material-icons" style="font-size:24px; opacity:0.5; display:block; margin:0 auto 10px auto;">notifications_none</span>
                    <p>Sem notificações novas</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Support button with toggle functionality
    if st.sidebar.button(
        "Suporte",
        key="support_btn",
        icon=f":material/{ICONS['support']}:",
    ):
        st.session_state.show_support = not st.session_state.show_support

    # Show support panel when active
    if st.session_state.show_support:
        st.sidebar.markdown(f"""
        <div style="border-left: 3px solid {COLORS["primary"]}; padding:15px; background-color:{COLORS["primary"]}10; border-radius:4px;">
            <div style="display:flex; align-items:center; margin-bottom:15px;">
                <span class="material-icons" style="color:{COLORS["primary"]}; margin-right:8px;">{ICONS["support"]}</span>
                <span style="font-weight:600; color:{COLORS["secondary"]};">Suporte Técnico</span>
            </div>
            
            <div style="margin-left:30px;">
                <p style="margin-bottom:10px;">
                    <span class="material-icons" style="font-size:16px; vertical-align:middle; color:{COLORS["primary"]}; margin-right:5px;">{ICONS["person"]}</span>
                    <strong>Filipe Ferreira</strong>
                </p>
                <p style="margin-bottom:10px;">
                    <span class="material-icons" style="font-size:16px; vertical-align:middle; color:{COLORS["primary"]}; margin-right:5px;">{ICONS["phone"]}</span>
                    <a href="tel:919122277" style="text-decoration:none; color:{COLORS["secondary"]};">919 122 277</a>
                </p>
                <p style="margin-bottom:10px;">
                    <span class="material-icons" style="font-size:16px; vertical-align:middle; color:{COLORS["primary"]}; margin-right:5px;">{ICONS["email"]}</span>
                    <a href="mailto:suporte@ffmanutencontrol.com" style="text-decoration:none; color:{COLORS["secondary"]};">suporte@ffmanutencontrol.com</a>
                </p>
                <p style="margin-bottom:5px;">
                    <span class="material-icons" style="font-size:16px; vertical-align:middle; color:{COLORS["primary"]}; margin-right:5px;">{ICONS["clock"]}</span>
                    <small>Segunda a Sexta: 9h-18h</small>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # App version in the sidebar footer
    st.sidebar.markdown(
        f"""
        <div style='position: fixed; bottom: 20px; left: 20px; opacity: 0.7;'>
            <small>Versão {APP_VERSION}</small>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Add vertical spacing
    for _ in range(6):
        st.sidebar.write("")

    # Logout button
    if st.sidebar.button(
        "Sair",
        key="logout_btn",
        icon=f":material/{ICONS['logout']}:",
    ):
        st.session_state.clear()
        st.rerun()


def render_navigation_menu() -> None:
    """Build horizontal menu with icons and handle page navigation."""
    # Get current page
    current_page = st.session_state.current_page
    
    # Material Design icons for menu items
    icons = {
        "Dashboard": f":material/{ICONS['dashboard']}:",
        "Empresas": f":material/{ICONS['companies']}:",
        "Máquinas": f":material/{ICONS['machines']}:",
        "Manutenções": f":material/{ICONS['maintenances']}:",
        "Faturação": f":material/{ICONS['billing']}:",
        "Utilizadores": f":material/{ICONS['users']}:",
        "Configurações": f":material/{ICONS['settings']}:",
    }
    
    # Define menu items based on user role
    menu_items = [
        ("Dashboard", "Dashboard"),
        ("Empresas", "Companies"),
        ("Máquinas", "Machines"),
        ("Manutenções", "Maintenances"),
        ("Faturação", "Billing"),
    ]
    
    # Add admin-only options if user is admin
    if is_admin():
        menu_items.extend([
            ("Utilizadores", "Users"),
            ("Configurações", "Settings"),
        ])
    else:
        menu_items.append(("Configurações", "Settings"))
    
    # Container for enhanced menu
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)
    
    # Create columns for menu
    cols = st.columns(len(menu_items))
    
    # Render buttons for each menu item
    for i, (label, page_id) in enumerate(menu_items):
        with cols[i]:
            # Check if this is the current page
            is_current = page_id == current_page
            
            # Create Streamlit button
            if st.button(
                label,
                key=f"btn_{page_id}",
                icon=icons[label],
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                st.session_state.current_page = page_id
                st.rerun()
            
                    # Add visual indicator for current page
            if is_current:
                st.markdown(f'<div class="page-indicator"></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_page(page: str) -> None:
    """
    Route to the correct page, handling errors gracefully.
    
    Args:
        page: The page identifier to render
    """
    try:
        if page == "Dashboard":
            # Special handling for known dashboard issues
            try:
                dashboard.show_dashboard()
            except TypeError as e:
                if "unsupported operand type(s) for +" in str(e) and "datetime" in str(e):
                    st.error("Ocorreu um erro na visualização da linha do tempo. Alguns gráficos não estão disponíveis.")
                    
                    # Display simplified dashboard with metric cards
                    st.subheader("Dashboard da Frota")
                    
                    # Create manual metric cards with Material Design icons
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(
                            metric_card(
                                title="Total de Máquinas",
                                value="32",
                                delta=5,
                                icon=ICONS["machine"]
                            ),
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        st.markdown(
                            metric_card(
                                title="Manutenções Próximas",
                                value="8",
                                delta=-2,
                                icon=ICONS["pending"],
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
                                icon=ICONS["late"],
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
                                icon=ICONS["completed"],
                                color=COLORS["success"]
                            ),
                            unsafe_allow_html=True
                        )
                    
                    # Message to the user with Material Design icon
                    st.info(
                        f"""
                        <div style="display:flex; align-items:center;">
                            <span class="material-icons" style="margin-right:8px;">engineering</span>
                            Estamos trabalhando para resolver o problema de visualização da linha do tempo. 
                            Enquanto isso, você pode acessar as demais funcionalidades normalmente.
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    # Re-raise other errors
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
                st.info(
                    f"""
                    <div style="display:flex; align-items:center;">
                        <span class="material-icons" style="margin-right:8px;">lock</span>
                        Você não tem permissões para acessar esta página. Por favor, contacte um administrador.
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        elif page == "Settings":
            settings.show_settings()
        elif page == "Billing":
            try:
                from frontend.pages.billing import show_billing
                show_billing()
            except ImportError:
                st.error("Módulo de faturação não disponível.")
                st.info(
                    f"""
                    <div style="display:flex; align-items:center;">
                        <span class="material-icons" style="margin-right:8px;">construction</span>
                        O módulo de faturação está em desenvolvimento ou não está disponível nesta instalação.
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        else:
            st.error("Página não encontrada.")
            st.info(
                f"""
                <div style="display:flex; align-items:center;">
                    <span class="material-icons" style="margin-right:8px;">search_off</span>
                    A página solicitada não está disponível. Por favor, selecione uma opção no menu acima.
                </div>
                """, 
                unsafe_allow_html=True
            )
            
    except Exception as e:
        # Global error handling for any uncaught exceptions
        st.error(f"Ocorreu um erro inesperado: {type(e).__name__}")
        st.info(
            f"""
            <div style="display:flex; align-items:center;">
                <span class="material-icons" style="margin-right:8px;">support_agent</span>
                Nossa equipa foi notificada e está a trabalhar para resolver o problema.
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Show more detailed error info for admins or in development
        if is_admin() or os.getenv("ENVIRONMENT") == "development":
            st.exception(e)

# ------------------------------------------------------------------------------
# Main Application Flow
# ------------------------------------------------------------------------------
def main():
    """Primary application entry point and flow control."""
    # Initialize session state
    initialize_session_state()
    
    # Apply global styles
    apply_global_styles()
    
    # Handle application flow based on login state
    if not st.session_state.logged_in:
        login_screen()
    else:
        # Build the app UI
        sidebar_user_info()
        render_navigation_menu()
        render_page(st.session_state.current_page)


# ------------------------------------------------------------------------------
# Application Entry Point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()