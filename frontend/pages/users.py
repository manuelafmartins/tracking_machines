import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from frontend.utils.api import get_api_data
from frontend.utils.auth import is_admin
from utils.ui import display_menu, show_delete_button
from utils.auth import login_user, logout_user, is_admin
from utils.image import get_image_base64, save_company_logo, get_company_logo_path
from utils.api import get_api_data, post_api_data, put_api_data, delete_api_data
import os
from dotenv import load_dotenv
import base64

def show_users():
    st.title("Gestão de Utilizadores")
    
    st.markdown("""
        <style>
        

        /* Botões dentro de formulários */
        div[data-testid="stForm"] button {
            background-color: #2c3e50 !important;
            color: white !important;
            border: none !important;
        }
        div[data-testid="stForm"] button:hover {
            background-color: #34495e !important;
            color: white !important;
            border: none !important;
        }

        /* Botões dentro de colunas horizontais */
        div[data-testid="stHorizontalBlock"] div[data-testid="column"] button {
            background-color: #2c3e50 !important;
            color: white !important;
            border: none !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="column"] button:hover {
            background-color: #34495e !important;
            color: white !important;
            border: none !important;
        }
                
        /* Evitar estilizar o botão hide/unhide do input de password */
        button[title="View password text"] {
            background-color: transparent !important;
            color: inherit !important;
            border: none !important;
        }
        button[title="View password text"]:hover {
            background-color: transparent !important;
            color: inherit !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Buscar todas as empresas para dropdown
    companies = get_api_data("companies") or []
    
    # Criar um dicionário para armazenar os caminhos dos logos das empresas
    company_logos = {}
    for company in companies:
        company_id = company["id"]
        logo_path = company.get("logo_path")
        
        # Verificar diretamente se há logo para esta empresa
        for ext in [".png", ".jpg", ".jpeg"]:
            custom_path = f"frontend/images/company_logos/company_{company_id}{ext}"
            if os.path.exists(custom_path):
                company_logos[company_id] = custom_path
                break
        
        # Se não encontrou pelo ID, tente pelo caminho salvo no banco
        if company_id not in company_logos and logo_path:
            full_path = f"frontend/images/{logo_path}"
            if os.path.exists(full_path):
                company_logos[company_id] = full_path
    
    # Buscar todos os utilizadores
    users = get_api_data("auth/users") or []
    
    # Adicionar nome da empresa para exibição
    if users:
        for user in users:
            if user.get("company_id"):
                company = next((c for c in companies if c["id"] == user["company_id"]), None)
                if company:
                    user["company_name"] = company["name"]
                    user["company_id"] = company["id"]
                else:
                    user["company_name"] = "Empresa não encontrada"
            else:
                # Para administradores ou usuários sem empresa atribuída
                user["company_name"] = None
    
    # Criação das abas
    tab_existentes, tab_novo = st.tabs(["Utilizadores Atuais", "Criar Novo Utilizador"])
    
    # Tab 1: Utilizadores Existentes
    with tab_existentes:
        if users:
            # Adicionar campo de pesquisa
            search_query = st.text_input("Pesquisar utilizador", placeholder="Escreva para procurar...")
            
            # Filtrar usuários se houver termo de pesquisa
            filtered_users = users
            if search_query:
                search_lower = search_query.lower()
                filtered_users = [
                    user for user in users if 
                    search_lower in user.get('username', '').lower() or 
                    search_lower in user.get('full_name', '').lower() or
                    search_lower in user.get('email', '').lower() or
                    (user.get('company_name') and search_lower in user.get('company_name', '').lower())
                ]
            
            # Contador de usuários
            if search_query:
                st.write(f"Resultados: {len(filtered_users)} de {len(users)} utilizadores")
            else:
                st.write(f"Total de utilizadores: {len(users)}")
                
            # Exibir utilizadores em seções expansíveis
            for user in filtered_users:
                # Preparar informações para exibição
                full_name = user.get('full_name', user.get('username', 'Usuário'))
                is_active = user.get("is_active", True)
                
                # Formatar o título do expander conforme solicitado
                if user.get('role') == "admin":
                    # Caso de administrador
                    expander_title = f"{full_name} (Administrador)"
                else:
                    # Caso de gestor de frota
                    company_name = user.get('company_name', 'Sem empresa')
                    expander_title = f"{full_name} ({company_name} - Gestor de Frota)"
                
                with st.expander(expander_title):
                    # Layout em duas colunas - uma para logo/info principal e outra para botões
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Se for gestor de frota e tiver empresa, mostrar logo
                        if user.get('role') == "fleet_manager" and user.get('company_id') in company_logos:
                            # Obter o logo da empresa
                            logo_path = company_logos[user['company_id']]
                            
                            try:
                                with open(logo_path, "rb") as img_file:
                                    encoded_logo = base64.b64encode(img_file.read()).decode()
                                
                                # Exibir o logo em tamanho reduzido
                                st.markdown(
                                    f"<img src='data:image/png;base64,{encoded_logo}' width='100px' style='float:left; margin-right:15px;'>",
                                    unsafe_allow_html=True
                                )
                            except Exception as e:
                                pass  # Se não conseguir carregar o logo, apenas continue sem erro
                        
                        # Informações do usuário
                        st.write(f"**Nome de Utilizador:** {user.get('username', 'N/A')}")
                        st.write(f"**Email:** {user.get('email', 'N/A')}")
                        
                        # Mostrar função de forma apropriada
                        role_display = "Administrador" if user.get('role') == "admin" else "Gestor de Frota"
                        st.write(f"**Função:** {role_display}")
                        
                        # Mostrar empresa para gestores de frota
                        if user.get('role') == "fleet_manager":
                            st.write(f"**Empresa:** {user.get('company_name', 'Sem empresa atribuída')}")
                        
                        phone = user.get('phone_number', 'N/A')
                        st.write(f"**Telefone:** {phone}")
                        
                        notif_status = "Ativadas" if user.get('notifications_enabled', False) else "Desativadas"
                        st.write(f"**Notificações:** {notif_status}")
                    
                    with col2:
                        # Botão de edição com fundo azul escuro e ícone branco
                        if st.button("Editar", key=f"edit_user_{user['id']}", 
                                    use_container_width=True,
                                    icon=":material/edit:"):
                            st.session_state["edit_user_id"] = user["id"]
                            st.session_state["edit_user_username"] = user["username"]
                            st.session_state["edit_user_full_name"] = user.get("full_name", "")
                            st.session_state["edit_user_email"] = user.get("email", "")
                            st.session_state["edit_user_role"] = user.get("role", "fleet_manager")
                            st.session_state["edit_user_company_id"] = user.get("company_id")
                            st.session_state["edit_user_is_active"] = user.get("is_active", True)
                            st.session_state["edit_user_phone_number"] = user.get("phone_number", "")
                            st.session_state["edit_user_notifications_enabled"] = user.get("notifications_enabled", True)
                        
                       
                        
                        # Não permitir excluir o utilizador atual
                        if user["id"] != st.session_state.get("user_id"):
                            # Botão para excluir com fundo azul escuro e ícone branco
                            if st.button("Excluir", key=f"delete_user_{user['id']}", 
                                        use_container_width=True,
                                        icon=":material/delete:"):
                                show_delete_button(
                                    "user", user["id"], 
                                    confirm_text=f"Tem certeza que deseja excluir o utilizador {user['username']}?")

                
                # Formulário de edição aparece se este utilizador estiver sendo editado
                if st.session_state.get("edit_user_id") == user["id"]:
                    with st.form(f"edit_user_{user['id']}"):
                        st.subheader(f"Editar Utilizador: {st.session_state.get('edit_user_full_name')}")
                        
                        edit_username = st.text_input("Nome de Utilizador", value=st.session_state["edit_user_username"])
                        edit_password = st.text_input("Nova Palavra-passe (deixe em branco para manter a atual)", type="password")
                        edit_full_name = st.text_input("Nome Completo", value=st.session_state["edit_user_full_name"])
                        edit_email = st.text_input("Email", value=st.session_state["edit_user_email"])
                        
                        # Adicionar campos de telefone e notificações
                        phone_value = user.get("phone_number", "+351")
                        edit_phone_number = st.text_input("Número de Telefone (com código do país)", value=phone_value)
                        
                        # Obter valor atual das notificações, com padrão True
                        notifications_enabled = user.get("notifications_enabled", True)
                        edit_notifications_enabled = st.checkbox("Ativar notificações por SMS", value=notifications_enabled)
                        
                        # Seleção de função (não pode alterar a função do Filipe Ferreira)
                        if user["username"] == "filipe.ferreira":
                            edit_role = "admin"
                            st.write("**Função:** Administrador (não pode ser alterado)")
                        else:
                            role_options = ["admin", "fleet_manager"]
                            role_labels = ["Administrador", "Gestor de Frota"]
                            current_role_idx = 0 if st.session_state["edit_user_role"] == "admin" else 1
                            
                            edit_role_idx = st.selectbox(
                                "Função", 
                                options=range(len(role_options)),
                                format_func=lambda idx: role_labels[idx],
                                index=current_role_idx
                            )
                            edit_role = role_options[edit_role_idx]
                        
                        # Seleção de empresa (para gestores de frota)
                        edit_company_id = None
                        if edit_role == "fleet_manager":
                            if companies:
                                company_options = [c["id"] for c in companies]
                                company_labels = [c["name"] for c in companies]
                                
                                # Encontrar índice da empresa atual
                                current_company_idx = 0
                                current_company_id = st.session_state["edit_user_company_id"]
                                if current_company_id:
                                    for i, cid in enumerate(company_options):
                                        if cid == current_company_id:
                                            current_company_idx = i
                                            break
                                
                                selected_company_idx = st.selectbox(
                                    "Atribuir à Empresa",
                                    options=range(len(company_options)),
                                    format_func=lambda idx: company_labels[idx],
                                    index=current_company_idx
                                )
                                edit_company_id = company_options[selected_company_idx]
                            else:
                                st.warning("Não existem empresas disponíveis.")
                        else:
                            # Para administradores, mostrar que a empresa não é aplicável
                            st.write("**Empresa:** Não aplicável para Administradores")
                        
                        # Status ativo
                        edit_is_active = st.checkbox("Ativo", value=st.session_state["edit_user_is_active"])
                        
                        # Declarar as colunas aqui para evitar o erro "Missing Submit Button"
                        form_cols = st.columns(2)
                        with form_cols[0]:
                            submit_edit = st.form_submit_button("Salvar Alterações",
                                                                type="primary",
                                                                use_container_width=True,
                                                                icon=":material/save:")

                        with form_cols[1]:
                            cancel_edit = st.form_submit_button("Cancelar",
                                                                type="secondary",
                                                                use_container_width=True,
                                                                icon=":material/cancel:")
                        
                        if submit_edit:
                            # Construir dados de atualização
                            update_data = {
                                "username": edit_username,
                                "full_name": edit_full_name,
                                "email": edit_email,
                                "is_active": edit_is_active,
                                "phone_number": edit_phone_number,
                                "notifications_enabled": edit_notifications_enabled
                            }
                            
                            # Incluir senha apenas se fornecida
                            if edit_password:
                                update_data["password"] = edit_password
                            
                            # Incluir função se não for o Filipe Ferreira
                            if user["username"] != "filipe.ferreira":
                                update_data["role"] = edit_role
                            
                            # Incluir company_id para gestores de frota
                            if edit_role == "fleet_manager" and edit_company_id:
                                update_data["company_id"] = edit_company_id
                            elif edit_role == "admin":
                                update_data["company_id"] = None
                            
                            if put_api_data(f"auth/users/{user['id']}", update_data):
                                st.success("Utilizador atualizado com sucesso!")
                                # Limpar estado de edição
                                if "edit_user_id" in st.session_state:
                                    del st.session_state["edit_user_id"]
                                st.rerun()
                        
                        if cancel_edit:
                            # Limpar estado de edição
                            if "edit_user_id" in st.session_state:
                                del st.session_state["edit_user_id"]
                            st.rerun()
        else:
            st.info("Nenhum utilizador encontrado.")

    # Tab 2: Criar Novo Utilizador
    with tab_novo:
        st.subheader("Criar Novo Utilizador")
        
        # Passo 1: Seleção de função (fora do formulário)
        role = st.selectbox(
            "1. Selecione a função para o novo utilizador", 
            ["admin", "fleet_manager"], 
            format_func=lambda x: "Administrador" if x == "admin" else "Gestor de Frota",
            key="new_user_role"
        )
        
        # Passo 2: Formulário com os campos apropriados
        with st.form("new_user"):
            st.subheader("Dados do Utilizador")
            
            username = st.text_input("Nome de Utilizador")
            password = st.text_input("Palavra-passe", type="password")
            confirm_password = st.text_input("Confirmar Palavra-passe", type="password")
            full_name = st.text_input("Nome Completo")
            email = st.text_input("Email")
            phone_number = st.text_input("Número de Telefone (com código do país)", value="+351")
            notifications_enabled = st.checkbox("Ativar notificações por SMS", value=True)
            
            # Seleção de empresa (apenas para gestores de frota)
            company_id = None
            if role == "fleet_manager":
                if companies:
                    company_options = [c["id"] for c in companies]
                    company_labels = [c["name"] for c in companies]
                    
                    selected_company_idx = st.selectbox(
                        "Atribuir à Empresa",
                        options=range(len(company_options)),
                        format_func=lambda idx: company_labels[idx]
                    )
                    company_id = company_options[selected_company_idx]
                else:
                    st.warning("Não existem empresas disponíveis. Por favor, crie uma empresa primeiro.")
            else:
                st.markdown("")
            
            # Botões com estilo consistente
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Criar Utilizador", 
                                                 use_container_width=True,
                                                 icon=":material/person_add:")
            with col2:
                cancel = st.form_submit_button("Cancelar", 
                                              use_container_width=True,
                                              icon=":material/cancel:")
            
           
            
            if submitted:
                if not username or not password:
                    st.error("Nome de utilizador e palavra-passe são obrigatórios")
                elif password != confirm_password:
                    st.error("As palavras-passe não coincidem")
                else:
                    # Criar dados do utilizador
                    user_data = {
                        "username": username,
                        "password": password,
                        "full_name": full_name,
                        "email": email,
                        "role": role,
                        "phone_number": phone_number,
                        "notifications_enabled": notifications_enabled
                    }
                    
                    # Adicionar company_id para gestores de frota
                    if role == "fleet_manager" and company_id:
                        user_data["company_id"] = company_id
                    
                    if post_api_data("auth/users", user_data):
                        st.success(f"Utilizador '{username}' criado com sucesso!")
                        st.rerun()
            
            if cancel:
                # Limpar campos do formulário e voltar para a lista
                st.rerun()