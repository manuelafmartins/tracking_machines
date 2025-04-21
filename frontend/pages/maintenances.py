import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
from frontend.utils.api import get_api_data
from frontend.utils.auth import is_admin
from utils.ui import display_menu, show_delete_button
from utils.auth import login_user, logout_user, is_admin
from utils.image import get_image_base64, save_company_logo
from utils.api import get_api_data, post_api_data, put_api_data, delete_api_data
import os
from dotenv import load_dotenv

def show_maintenances():
    st.title("Agendamento de Manutenções")
    
    # Buscar dados com base no papel do usuário
    if is_admin():
        companies = get_api_data("companies") or []
        # Buscar todas as máquinas inicialmente
        all_machines = get_api_data("machines") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            companies = [get_api_data(f"companies/{company_id}")] if get_api_data(f"companies/{company_id}") else []
            all_machines = get_api_data(f"machines/company/{company_id}") or []
        else:
            companies = []
            all_machines = []
    
    # Criar um dicionário para busca rápida de nomes de empresas
    company_dict = {c["id"]: c["name"] for c in companies}
    
    # Criar um formulário para agendar nova manutenção
    with st.form("new_maintenance"):
        st.subheader("Agendar Nova Manutenção")
        
        # Filtro de empresa (apenas para admin)
        if is_admin() and companies:
            company_options = [c["id"] for c in companies]
            company_labels = [c["name"] for c in companies]
            
            selected_company_idx = st.selectbox(
                "Filtrar por Empresa",
                options=range(len(company_options)),
                format_func=lambda idx: company_labels[idx],
                key="company_filter"
            )
            selected_company_id = company_options[selected_company_idx]
            
            # Filtrar máquinas pela empresa selecionada
            machines = [m for m in all_machines if m["company_id"] == selected_company_id]
        else:
            # Gestores de frota veem apenas as máquinas de sua empresa
            machines = all_machines
        
        # Deixar o usuário escolher uma máquina
        if machines:
            machine_options = [m["id"] for m in machines]
            machine_labels = [f"{m['name']} ({m['type']})" for m in machines]
            
            selected_machine_idx = st.selectbox(
                "Máquina",
                options=range(len(machine_options)),
                format_func=lambda idx: machine_labels[idx]
            )
            chosen_machine_id = machine_options[selected_machine_idx]
        else:
            st.warning("Não há máquinas disponíveis. Por favor, adicione uma máquina primeiro.")
            chosen_machine_id = None
        
        # Tipos de manutenção
        maintenance_type = st.selectbox(
            "Tipo de Manutenção",
            ["Troca de Óleo", "Revisão Completa", "Filtros", "Pneus", "Manutenção Preventiva", "Manutenção Corretiva", "Outro"]
        )
        
        final_type = maintenance_type
        if maintenance_type == "Outro":
            user_type = st.text_input("Especifique o tipo de manutenção")
            if user_type:
                final_type = user_type
        
        # Seleção de data
        scheduled_date = st.date_input(
            "Data Agendada",
            min_value=datetime.now().date(),
            value=datetime.now().date() + timedelta(days=7)
        )
        
        # Notas opcionais
        notes = st.text_area("Observações (Opcional)")
        
        submitted = st.form_submit_button("Agendar")
        
        if submitted and chosen_machine_id:
            # De acordo com MaintenanceCreate, enviamos: {"machine_id", "type", "scheduled_date", "notes"}
            data = {
                "machine_id": chosen_machine_id,
                "type": final_type,
                "scheduled_date": scheduled_date.isoformat()
            }
            if notes:
                data["notes"] = notes
                
            if post_api_data("maintenances", data):
                st.success(f"Manutenção agendada para {scheduled_date}!")
                st.rerun()
    
    st.subheader("Manutenções Agendadas")
    
    # Buscar manutenções com base no papel do usuário
    if is_admin():
        maintenances = get_api_data("maintenances") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            maintenances = get_api_data(f"maintenances/company/{company_id}") or []
        else:
            maintenances = []
    
    if maintenances:
        # Adicionar nome da máquina para melhor exibição
        for m in maintenances:
            machine = next((mac for mac in all_machines if mac["id"] == m["machine_id"]), None)
            if machine:
                m["machine_name"] = machine["name"]
                m["machine_type"] = machine["type"]
                
                # Adicionar nome da empresa
                company_id = machine.get("company_id")
                if company_id in company_dict:
                    m["company_name"] = company_dict[company_id]
        
        # Converter para DataFrame para exibição
        df_maint = pd.DataFrame(maintenances)
        
        # Converter "scheduled_date" para datetime
        if "scheduled_date" in df_maint.columns:
            df_maint["scheduled_date"] = pd.to_datetime(df_maint["scheduled_date"])
        
        # Ordenar por data
        if "scheduled_date" in df_maint.columns:
            df_maint = df_maint.sort_values("scheduled_date")
        
        # Destaque simples para atrasadas / em breve
        today = datetime.now().date()
        
        # Exibir manutenções em abas: Pendentes e Concluídas
        tab1, tab2 = st.tabs(["Pendentes", "Concluídas"])
        
        with tab1:
            # Filtrar para manutenções pendentes
            pending = df_maint[df_maint["completed"] == False] if "completed" in df_maint.columns else df_maint
            
            if not pending.empty:
                for idx, maint in pending.iterrows():
                    # Determinar urgência para codificação de cores
                    date_val = maint["scheduled_date"].date() if "scheduled_date" in maint else today
                    days_remaining = (date_val - today).days
                    
                    if days_remaining <= 0:
                        status = "⚠️ Atrasada"
                    elif days_remaining <= 2:
                        status = "🔴 Urgente"
                    elif days_remaining <= 7:
                        status = "⚡ Em Breve"
                    else:
                        status = "✓ Agendada"
                    
                    # Criar um expansor com detalhes da manutenção
                    with st.expander(f"{status} - {maint.get('type', 'Manutenção')} em {maint.get('machine_name', 'Máquina Desconhecida')} ({date_val})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Máquina:** {maint.get('machine_name', 'Desconhecida')}")
                            st.write(f"**Empresa:** {maint.get('company_name', 'Desconhecida')}")
                            st.write(f"**Tipo:** {maint.get('type', 'Desconhecido')}")
                            st.write(f"**Data Agendada:** {date_val}")
                            
                            if "notes" in maint and maint["notes"]:
                                st.write(f"**Observações:** {maint['notes']}")
                        
                        with col2:
                            # Botão para marcar como concluída
                            if st.button("Marcar como Concluída", key=f"complete_{maint['id']}"):
                                if put_api_data(f"maintenances/{maint['id']}", {"completed": True}):
                                    st.success("Manutenção marcada como concluída!")
                                    st.rerun()
                            
                            # Botão de edição
                            if st.button("Editar", key=f"edit_maint_{maint['id']}"):
                                st.session_state["edit_maint_id"] = maint["id"]
                                st.session_state["edit_maint_type"] = maint["type"]
                                st.session_state["edit_maint_date"] = maint["scheduled_date"]
                                st.session_state["edit_maint_notes"] = maint.get("notes", "")
                            
                            # Botão de exclusão
                            show_delete_button("maintenance", maint["id"], label="Excluir", 
                                              confirm_text=f"Tem certeza que deseja excluir esta manutenção?")
                    
                    # Formulário de edição aparece se esta manutenção estiver sendo editada
                    if st.session_state.get("edit_maint_id") == maint["id"]:
                        with st.form(f"edit_maint_{maint['id']}"):
                            st.subheader(f"Editar Manutenção")
                            
                            edit_type = st.text_input("Tipo de Manutenção", value=st.session_state["edit_maint_type"])
                            
                            edit_date = st.date_input(
                                "Data Agendada",
                                value=st.session_state["edit_maint_date"].date() 
                                    if isinstance(st.session_state["edit_maint_date"], datetime) 
                                    else datetime.strptime(st.session_state["edit_maint_date"], "%Y-%m-%d").date(),
                                min_value=datetime.now().date()
                            )
                            
                            edit_notes = st.text_area("Observações", value=st.session_state["edit_maint_notes"])
                            
                            # Criar novas colunas dentro do formulário
                            col1, col2 = st.columns(2)
                            with col1:
                                submit_edit = st.form_submit_button("Salvar Alterações")
                            with col2:
                                cancel_edit = st.form_submit_button("Cancelar")
                            
                            if submit_edit and edit_type:
                                update_data = {
                                    "type": edit_type,
                                    "scheduled_date": edit_date.isoformat(),
                                    "notes": edit_notes
                                }
                                
                                if put_api_data(f"maintenances/{maint['id']}", update_data):
                                    st.success("Manutenção atualizada com sucesso!")
                                    # Limpar estado de edição
                                    if "edit_maint_id" in st.session_state:
                                        del st.session_state["edit_maint_id"]
                                    st.rerun()
                            
                            if cancel_edit:
                                # Limpar estado de edição
                                if "edit_maint_id" in st.session_state:
                                    del st.session_state["edit_maint_id"]
                                st.rerun()
            else:
                st.info("Não há manutenções pendentes.")
        
        with tab2:
            # Filtrar para manutenções concluídas
            completed = df_maint[df_maint["completed"] == True] if "completed" in df_maint.columns else pd.DataFrame()
            
            if not completed.empty:
                # Renomear colunas para exibição em português
                column_mapping = {
                    "scheduled_date": "Data Agendada",
                    "type": "Tipo",
                    "machine_name": "Máquina",
                    "company_name": "Empresa"
                }
                
                display_df = completed[["scheduled_date", "type", "machine_name", "company_name"]].rename(columns=column_mapping)
                st.dataframe(display_df)
            else:
                st.info("Não há manutenções concluídas.")
    else:
        st.info("Não há manutenções agendadas.")