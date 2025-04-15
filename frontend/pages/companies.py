# frontend/pages/companies.py
import streamlit as st
import os
import requests
from ..utils.api import get_api_data, post_api_data, put_api_data
from ..utils.ui import is_admin, show_delete_button, save_company_logo
from ..config import API_URL

def show_companies():
    """Exibe a página de gerenciamento de empresas."""
    st.title("Gerenciamento de Empresas")
    
    # Apenas administradores podem adicionar novas empresas
    if is_admin():
        with st.form("new_company"):
            st.subheader("Adicionar Nova Empresa")
            company_name = st.text_input("Nome da Empresa")
            company_address = st.text_input("Endereço (Opcional)")
            company_logo = st.file_uploader("Logo da Empresa (opcional)", type=["png", "jpg", "jpeg"])
            submitted = st.form_submit_button("Adicionar")
            
            if submitted and company_name:
                company_data = {"name": company_name}
                if company_address:
                    company_data["address"] = company_address
                
                # Criar empresa
                new_company_response = requests.post(
                    f"{API_URL}/companies", 
                    headers={"Authorization": f"Bearer {st.session_state['token']}"},
                    json=company_data
                )
                
                if new_company_response.status_code in [200, 201]:
                    new_company = new_company_response.json()
                    company_id = new_company["id"]
                    
                    # Se um logo foi enviado, salvar e atualizar caminho
                    if company_logo:
                        logo_relative_path = save_company_logo(company_id, company_logo)
                        
                        if logo_relative_path:
                            # Atualizar o caminho do logo no banco de dados
                            update_data = {"logo_path": logo_relative_path}
                            put_api_data(f"companies/{company_id}", update_data)
                    
                    st.success(f"Empresa '{company_name}' adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro ao criar empresa: {new_company_response.text}")
    
    st.subheader("Empresas Existentes")
    
    # Buscar empresas - administradores veem todas, gerentes de frota veem apenas a sua própria
    if is_admin():
        companies = get_api_data("companies") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            company = get_api_data(f"companies/{company_id}")
            companies = [company] if company else []
        else:
            companies = []
    
    if companies:
        # Criar abas para cada empresa
        for comp in companies:
            with st.expander(f"{comp['name']} (ID: {comp['id']})"):
                if comp.get("logo_path"):
                    logo_path = os.path.join("frontend/images", comp.get("logo_path"))
                    if os.path.exists(logo_path):
                        st.image(logo_path, width=150, caption="Logo atual da empresa")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Endereço:** {comp.get('address', 'N/A')}")
                    
                    # Obter máquinas para esta empresa
                    machines = get_api_data(f"machines/company/{comp['id']}") or []
                    st.write(f"**Total de Máquinas:** {len(machines)}")
                    
                    # Obter usuários para esta empresa (somente admin)
                    if is_admin():
                        # Isso exigiria um novo endpoint para obter usuários por empresa
                        # st.write(f"**Usuários:** ...")
                        pass
                
                # Botões de Editar/Excluir (somente admin)
                if is_admin():
                    with col2:
                        if st.button("Editar", key=f"edit_company_{comp['id']}"):
                            st.session_state["edit_company_id"] = comp["id"]
                            st.session_state["edit_company_name"] = comp["name"]
                            st.session_state["edit_company_address"] = comp.get("address", "")
                        
                        # Botão de excluir empresa com confirmação
                        show_delete_button("company", comp["id"], 
                            confirm_text=f"Tem certeza que deseja excluir {comp['name']}? Isso excluirá todas as máquinas e manutenções relacionadas!")

            
            # O formulário de edição aparece se esta empresa estiver sendo editada
            if is_admin() and st.session_state.get("edit_company_id") == comp["id"]:
                with st.form(f"edit_company_{comp['id']}"):
                    st.subheader(f"Editar Empresa: {comp['name']}")
                    new_name = st.text_input("Nome da Empresa", value=st.session_state["edit_company_name"])
                    new_address = st.text_input("Endereço", value=st.session_state["edit_company_address"])
                    new_logo = st.file_uploader("Atualizar Logo (opcional)", type=["png", "jpg", "jpeg"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Salvar Alterações")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancelar")
                    
                    if submit_edit and new_name:
                        if submit_edit and new_name and new_logo:
                            # Nova implementação
                            logo_relative_path = save_company_logo(comp['id'], new_logo)
                            
                            if logo_relative_path:
                                # Atualizar apenas o caminho do logo no banco de dados
                                update_data = {
                                    "name": new_name,
                                    "address": new_address,
                                    "logo_path": logo_relative_path
                                }
                                
                                if put_api_data(f"companies/{comp['id']}", update_data):
                                    st.success("Empresa e logo atualizados com sucesso!")
                                    if "edit_company_id" in st.session_state:
                                        del st.session_state["edit_company_id"]
                                    st.rerun()
                        
                        update_data = {"name": new_name}
                        if new_address:
                            update_data["address"] = new_address
                            
                        if put_api_data(f"companies/{comp['id']}", update_data):
                            st.success("Empresa atualizada com sucesso!")
                            # Limpar estado de edição
                            if "edit_company_id" in st.session_state:
                                del st.session_state["edit_company_id"]
                            st.rerun()
                    
                    if cancel_edit:
                        # Limpar estado de edição
                        if "edit_company_id" in st.session_state:
                            del st.session_state["edit_company_id"]
                        st.rerun()
    else:
        st.info("Nenhuma empresa encontrada.")