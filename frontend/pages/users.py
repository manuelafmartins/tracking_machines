# frontend/pages/users.py
import streamlit as st
from ..utils.api import get_api_data, post_api_data, put_api_data
from ..utils.ui import show_delete_button

def show_users():
    """Exibe a p�gina de gerenciamento de usu�rios (somente admin)."""
    st.title("Gerenciamento de Usu�rios")
    
    # Buscar todas as empresas para dropdown
    companies = get_api_data("companies") or []
    
    # Criar um formul�rio para novo usu�rio
    with st.form("new_user"):
        st.subheader("Criar Novo Usu�rio")
        
        username = st.text_input("Nome de Usu�rio")
        password = st.text_input("Senha", type="password")
        confirm_password = st.text_input("Confirmar Senha", type="password")
        full_name = st.text_input("Nome Completo")
        email = st.text_input("Email")
        
        # Sele��o de fun��o
        role = st.selectbox("Fun��o", ["admin", "fleet_manager"])
        
        # Sele��o de empresa (para gerentes de frota)
        company_id = None
        if role == "fleet_manager":
            if companies:
                company_options = [c["id"] for c in companies]
                company_labels = [c["name"] for c in companies]
                
                selected_company_idx = st.selectbox(
                    "Atribuir � Empresa",
                    options=range(len(company_options)),
                    format_func=lambda idx: company_labels[idx]
                )
                company_id = company_options[selected_company_idx]
            else:
                st.warning("Nenhuma empresa dispon�vel. Crie uma empresa primeiro.")
        
        submitted = st.form_submit_button("Criar Usu�rio")
        
        if submitted:
            if not username or not password:
                st.error("Nome de usu�rio e senha s�o obrigat�rios")
            elif password != confirm_password:
                st.error("As senhas n�o coincidem")
            else:
                # Criar dados do usu�rio
                user_data = {
                    "username": username,
                    "password": password,
                    "full_name": full_name,
                    "email": email,
                    "role": role
                }
                
                # Adicionar company_id para gerentes de frota
                if role == "fleet_manager" and company_id:
                    user_data["company_id"] = company_id
                
                if post_api_data("auth/users", user_data):
                    st.success(f"Usu�rio '{username}' criado com sucesso!")
                    st.rerun()
    
    # Listar usu�rios existentes
    st.subheader("Usu�rios Existentes")
    
    # Buscar todos os usu�rios
    users = get_api_data("auth/users") or []
    
    if users:
        # Adicionar nome da empresa para exibi��o
        for user in users:
            if user.get("company_id"):
                company = next((c for c in companies if c["id"] == user["company_id"]), None)
                if company:
                    user["company_name"] = company["name"]
        
        # Exibir usu�rios em se��es expans�veis
        for user in users:
            status = "?? Ativo" if user.get("is_active", True) else "?? Inativo"
            with st.expander(f"{user['username']} - {user.get('role', 'Desconhecido').replace('_', ' ').title()} ({status})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** {user['id']}")
                    st.write(f"**Nome Completo:** {user.get('full_name', 'N/A')}")
                    st.write(f"**Email:** {user.get('email', 'N/A')}")
                    st.write(f"**Fun��o:** {user.get('role', 'Desconhecido').replace('_', ' ').title()}")
                    if "company_name" in user:
                        st.write(f"**Empresa:** {user['company_name']}")
                
                with col2:
                    # Bot�o de editar
                    if st.button("Editar", key=f"edit_user_{user['id']}"):
                        st.session_state["edit_user_id"] = user["id"]
                        st.session_state["edit_user_username"] = user["username"]
                        st.session_state["edit_user_full_name"] = user.get("full_name", "")
                        st.session_state["edit_user_email"] = user.get("email", "")
                        st.session_state["edit_user_role"] = user.get("role", "fleet_manager")
                        st.session_state["edit_user_company_id"] = user.get("company_id")
                        st.session_state["edit_user_is_active"] = user.get("is_active", True)
                    
                    # N�o permitir excluir o usu�rio atual
                    if user["id"] != st.session_state.get("user_id"):
                        # Bot�o de excluir usu�rio com confirma��o
                        show_delete_button("user", user["id"], 
                            confirm_text=f"Tem certeza que deseja excluir o usu�rio {user['username']}?")

            
            # O formul�rio de edi��o aparece se este usu�rio estiver sendo editado
            if st.session_state.get("edit_user_id") == user["id"]:
                with st.form(f"edit_user_{user['id']}"):
                    st.subheader(f"Editar Usu�rio: {user['username']}")
                    
                    edit_username = st.text_input("Nome de Usu�rio", value=st.session_state["edit_user_username"])
                    edit_password = st.text_input("Nova Senha (deixe em branco para manter a atual)", type="password")
                    edit_full_name = st.text_input("Nome Completo", value=st.session_state["edit_user_full_name"])
                    edit_email = st.text_input("Email", value=st.session_state["edit_user_email"])
                    
                    # Sele��o de fun��o (n�o pode alterar a fun��o do Filipe Ferreira)
                    if user["username"] == "filipe.ferreira":
                        edit_role = "admin"
                        st.write("**Fun��o:** Administrador (n�o pode ser alterada)")
                    else:
                        edit_role = st.selectbox(
                            "Fun��o", 
                            ["admin", "fleet_manager"],
                            index=0 if st.session_state["edit_user_role"] == "admin" else 1
                        )
                    
                    # Sele��o de empresa (para gerentes de frota)
                    edit_company_id = None
                    if edit_role == "fleet_manager":
                        if companies:
                            company_options = [c["id"] for c in companies]
                            company_labels = [c["name"] for c in companies]
                            
                            # Encontrar �ndice da empresa atual
                            current_company_idx = 0
                            current_company_id = st.session_state["edit_user_company_id"]
                            if current_company_id:
                                for i, cid in enumerate(company_options):
                                    if cid == current_company_id:
                                        current_company_idx = i
                                        break
                            
                            selected_company_idx = st.selectbox(
                                "Atribuir � Empresa",
                                options=range(len(company_options)),
                                format_func=lambda idx: company_labels[idx],
                                index=current_company_idx
                            )
                            edit_company_id = company_options[selected_company_idx]
                        else:
                            st.warning("Nenhuma empresa dispon�vel.")
                    
                    # Status ativo
                    edit_is_active = st.checkbox("Ativo", value=st.session_state["edit_user_is_active"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Salvar Altera��es")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancelar")
                    
                    if submit_edit:
                        # Construir dados de atualiza��o
                        update_data = {
                            "username": edit_username,
                            "full_name": edit_full_name,
                            "email": edit_email,
                            "is_active": edit_is_active
                        }
                        
                        # Incluir senha apenas se fornecida
                        if edit_password:
                            update_data["password"] = edit_password
                        
                        # Incluir fun��o se n�o for Filipe Ferreira
                        if user["username"] != "filipe.ferreira":
                            update_data["role"] = edit_role
                        
                        # Incluir company_id para gerentes de frota
                        if edit_role == "fleet_manager" and edit_company_id:
                            update_data["company_id"] = edit_company_id
                        elif edit_role == "admin":
                            update_data["company_id"] = None
                        
                        if put_api_data(f"auth/users/{user['id']}", update_data):
                            st.success("Usu�rio atualizado com sucesso!")
                            # Limpar estado de edi��o
                            if "edit_user_id" in st.session_state:
                                del st.session_state["edit_user_id"]
                            st.rerun()
                    
                    if cancel_edit:
                        # Limpar estado de edi��o
                        if "edit_user_id" in st.session_state:
                            del st.session_state["edit_user_id"]
                        st.rerun()
    else:
        st.info("Nenhum usu�rio encontrado.")