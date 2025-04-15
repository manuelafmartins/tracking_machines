# frontend/pages/machines.py
import streamlit as st
import pandas as pd
from ..utils.api import get_api_data, post_api_data, put_api_data
from ..utils.ui import is_admin, show_delete_button

def show_machines():
    """Exibe a p�gina de gerenciamento de m�quinas."""
    # T�tulo e bot�o na mesma linha usando colunas
    title_col, btn_col = st.columns([9, 1])
    
    with title_col:
        st.title("Gerenciamento de M�quinas")
    
    with btn_col:
        # Inicializar o estado do formul�rio se n�o existir
        if "show_add_machine_form" not in st.session_state:
            st.session_state["show_add_machine_form"] = False
        
        # Adicionar espa�o para alinhar com o t�tulo
        st.write("")
        st.write("")
        
        # Bot�o compacto com + ou �
        button_text = "�" if st.session_state["show_add_machine_form"] else "+"
        if st.button(button_text, key="add_machine_button"):
            st.session_state["show_add_machine_form"] = not st.session_state["show_add_machine_form"]
            st.rerun()
    
    # Buscar empresas para o dropdown - admin v� todas, gerente de frota v� apenas a pr�pria
    if is_admin():
        companies = get_api_data("companies") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            company = get_api_data(f"companies/{company_id}")
            companies = [company] if company else []
        else:
            companies = []
    
    # Formul�rio de adi��o de m�quina (apenas mostrado quando necess�rio)
    if st.session_state["show_add_machine_form"]:
        with st.form("new_machine"):
            st.subheader("Adicionar Nova M�quina")
            machine_name = st.text_input("Nome da M�quina")
            # Com base no schema, os tipos poss�veis s�o "truck" ou "fixed"
            machine_type = st.selectbox("Tipo", ["truck", "fixed"])
            
            # O usu�rio selecionar� uma empresa por ID - para gerentes de frota, isso � preenchido automaticamente
            if is_admin():
                company_options = [c["id"] for c in companies]
                company_labels = [c["name"] for c in companies]
                
                if company_options:
                    selected_company_idx = st.selectbox(
                        "Empresa",
                        options=range(len(company_options)),
                        format_func=lambda idx: company_labels[idx]
                    )
                    selected_company_id = company_options[selected_company_idx]
                else:
                    st.warning("Nenhuma empresa dispon�vel. Adicione uma empresa primeiro.")
                    selected_company_id = None
            else:
                # Gerentes de frota s� podem adicionar m�quinas � sua empresa
                if companies:
                    selected_company_id = companies[0]["id"]
                    st.write(f"**Empresa:** {companies[0]['name']}")
                else:
                    st.warning("As informa��es da sua empresa n�o est�o dispon�veis.")
                    selected_company_id = None
            
            submitted = st.form_submit_button("Adicionar")
            
            if submitted and machine_name and selected_company_id:
                # De acordo com o schema: {"name": str, "type": str, "company_id": int}
                payload = {
                    "name": machine_name,
                    "type": machine_type,
                    "company_id": selected_company_id
                }
                if post_api_data("machines", payload):
                    st.success(f"M�quina '{machine_name}' adicionada com sucesso!")
                    # Esconder o formul�rio depois de adicionar com sucesso
                    st.session_state["show_add_machine_form"] = False
                    st.rerun()
    
    
    st.subheader("M�quinas Atuais:")
    
    # Buscar m�quinas - admins veem todas, gerentes de frota veem apenas as da sua empresa
    if is_admin():
        machines = get_api_data("machines") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            machines = get_api_data(f"machines/company/{company_id}") or []
        else:
            machines = []
    
    if machines:
        # Converter para um DataFrame
        df_machines = pd.DataFrame(machines)
        
        # Adicionar o nome da empresa para melhor legibilidade
        def get_company_name(cid):
            for c in companies:
                if c["id"] == cid:
                    return c["name"]
            return "Desconhecida"
        
        if "company_id" in df_machines.columns:
            df_machines["company_name"] = df_machines["company_id"].apply(get_company_name)
        
        # Exibir m�quinas em se��es expans�veis
        for idx, machine in df_machines.iterrows():
            with st.expander(f"{machine['name']} ({machine['type']}) - {machine.get('company_name', 'Empresa Desconhecida')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** {machine['id']}")
                    st.write(f"**Tipo:** {machine['type']}")
                    st.write(f"**Empresa:** {machine.get('company_name', 'Desconhecida')}")
                    
                    # Exibir um bot�o para visualizar manuten��es
                    if st.button("Ver Manuten��es", key=f"view_maint_{machine['id']}"):
                        maintenances = get_api_data(f"maintenances/machine/{machine['id']}") or []
                        if maintenances:
                            st.write("**Manuten��es Agendadas:**")
                            df_maint = pd.DataFrame(maintenances)
                            st.dataframe(df_maint[["scheduled_date", "type", "completed"]])
                        else:
                            st.info(f"Nenhuma manuten��o agendada para {machine['name']}")
                
                # Bot�es de Editar/Excluir
                with col2:
                    if st.button("Editar", key=f"edit_machine_{machine['id']}"):
                        st.session_state["edit_machine_id"] = machine["id"]
                        st.session_state["edit_machine_name"] = machine["name"]
                        st.session_state["edit_machine_type"] = machine["type"]
                        st.session_state["edit_machine_company_id"] = machine["company_id"]
                    
                    # Bot�o de excluir m�quina com confirma��o
                    show_delete_button("machine", machine["id"], 
                        confirm_text=f"Tem certeza que deseja excluir {machine['name']}? Isso excluir� todas as manuten��es relacionadas!")
            
            # O formul�rio de edi��o aparece se esta m�quina estiver sendo editada
            if st.session_state.get("edit_machine_id") == machine["id"]:
                with st.form(f"edit_machine_{machine['id']}"):
                    st.subheader(f"Editar M�quina: {machine['name']}")
                    new_name = st.text_input("Nome da M�quina", value=st.session_state["edit_machine_name"])
                    new_type = st.selectbox("Tipo", ["truck", "fixed"], 
                                          index=0 if st.session_state["edit_machine_type"] == "truck" else 1)
                    
                    # Sele��o de empresa - admin pode alterar, gerente de frota n�o
                    if is_admin():
                        company_options = [c["id"] for c in companies]
                        company_labels = [c["name"] for c in companies]
                        
                        if company_options:
                            current_company_idx = 0
                            for i, cid in enumerate(company_options):
                                if cid == st.session_state["edit_machine_company_id"]:
                                    current_company_idx = i
                                    break
                                    
                            new_company_idx = st.selectbox(
                                "Empresa",
                                options=range(len(company_options)),
                                format_func=lambda idx: company_labels[idx],
                                index=current_company_idx
                            )
                            new_company_id = company_options[new_company_idx]
                        else:
                            new_company_id = st.session_state["edit_machine_company_id"]
                    else:
                        # Gerentes de frota n�o podem alterar a empresa
                        new_company_id = st.session_state["edit_machine_company_id"]
                        company_name = get_company_name(new_company_id)
                        st.write(f"**Empresa:** {company_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Salvar Altera��es")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancelar")
                    
                    if submit_edit and new_name:
                        update_data = {
                            "name": new_name,
                            "type": new_type,
                            "company_id": new_company_id
                        }
                            
                        if put_api_data(f"machines/{machine['id']}", update_data):
                            st.success("M�quina atualizada com sucesso!")
                            # Limpar estado de edi��o
                            if "edit_machine_id" in st.session_state:
                                del st.session_state["edit_machine_id"]
                            st.rerun()
                    
                    if cancel_edit:
                        # Limpar estado de edi��o
                        if "edit_machine_id" in st.session_state:
                            del st.session_state["edit_machine_id"]
                        st.rerun()
    else:
        st.info("Nenhuma m�quina encontrada.")