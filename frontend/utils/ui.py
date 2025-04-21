# -*- coding: utf-8 -*-
import streamlit as st
from .api import delete_api_data

def show_delete_button(item_type, item_id, label="Eliminar", confirm_text=None):
    """
    Display a delete button with confirmation.
    
    Args:
        item_type: Type of item (singular form: 'user', 'company', 'machine', 'maintenance')
        item_id: ID of the item to delete
        label: Button label
        confirm_text: Confirmation message
    """
    if confirm_text is None:
        confirm_text = f"Tem certeza que deseja excluir este {item_type}?"
    
    # Chave para rastrear o estado de confirmação no session_state
    confirm_key = f"confirm_delete_{item_type}_{item_id}"
    
    # Se já estamos em modo de confirmação
    if st.session_state.get(confirm_key, False):
        st.warning(confirm_text)
        
        # Criar dois botões lado a lado: Confirmar e Cancelar
        col1, col2 = st.columns(2)
        
        with col1:
            # Botão de confirmação
            if st.button("Confirmar Eliminar", key=f"confirm_delete_btn_{item_type}_{item_id}", use_container_width=True, icon=":material/delete:"):
                # Mapear tipos de itens para seus endpoints correspondentes
                endpoint_map = {
                    "user": f"auth/users/{item_id}",
                    "company": f"companies/{item_id}",
                    "machine": f"machines/{item_id}",
                    "maintenance": f"maintenances/{item_id}"
                }
                
                # Obter o endpoint adequado para o tipo de item
                if item_type in endpoint_map:
                    endpoint = endpoint_map[item_type]
                else:
                    # Caso padrão para outros tipos não especificados
                    endpoint = f"{item_type}s/{item_id}"
                
                if delete_api_data(endpoint):
                    st.success(f"{item_type.capitalize()} eliminado com sucesso!")
                    # Reset confirmation status
                    st.session_state[confirm_key] = False
                    st.rerun()
                return True
        
        with col2:
            # Botão de cancelar
            if st.button("Cancelar", key=f"cancel_delete_{item_type}_{item_id}"):
                # Reset confirmation status
                st.session_state[confirm_key] = False
                st.rerun()
            return False
    else:
        # Mostrar o botão de delete inicial
        if st.button(label, key=f"delete_{item_type}_{item_id}"):
            # Ativar modo de confirmação
            st.session_state[confirm_key] = True
            st.rerun()
        return False

def display_menu():
    """Exibe o menu principal da aplicação"""
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        dashboard_btn = st.button("Dashboard")
    with col2:
        companies_btn = st.button("Empresas")
    with col3:
        machines_btn = st.button("Máquinas")
    with col4:
        maintenances_btn = st.button("Manutenções")
    
    # Adicione o botão "Usuários" apenas para admins
    from .auth import is_admin
    if is_admin():
        with col5:
            users_btn = st.button("Utilizadores")
        with col6:
            settings_btn = st.button("Configurações")
    else:
        with col5:
            settings_btn = st.button("Configurações")
        with col6:
            users_btn = False
    
    # Botão de logout pode ficar separado
    logout_btn = st.button("Sair")
    
    # Controle qual página está sendo exibida
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
        st.session_state["current_page"] = "Logout"
        st.rerun()
        
    return st.session_state["current_page"]