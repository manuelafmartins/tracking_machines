# frontend/pages/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from ..utils.api import get_api_data
from ..utils.ui import is_admin

def show_dashboard():
    """Exibe o dashboard com as estatísticas e gráficos."""
    st.title("Fleet Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Buscar dados da API - comportamento diferente com base na função do usuário
    if is_admin():
        # Admin vê todos os dados
        machines = get_api_data("machines") or []
        maintenances = get_api_data("maintenances") or []
        companies = get_api_data("companies") or []
    else:
        # Gerente de frota vê apenas os dados de sua empresa
        company_id = st.session_state.get("company_id")
        if company_id:
            machines = get_api_data(f"machines/company/{company_id}") or []
            maintenances = get_api_data(f"maintenances/company/{company_id}") or []
            companies = [get_api_data(f"companies/{company_id}")] if get_api_data(f"companies/{company_id}") else []
        else:
            machines = []
            maintenances = []
            companies = []
    
    # Calcular manutenções próximas dentro de 7 dias
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    # Filtrar manutenções próximas
    upcoming_maintenances = []
    for m in maintenances:
        # Converter "scheduled_date" de string para data
        sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
        if today <= sched_date <= next_week and not m.get("completed", False):
            upcoming_maintenances.append(m)
    
    col1.metric("Total de Máquinas", len(machines))
    col2.metric("Manutenções Próximas", len(upcoming_maintenances))
    col3.metric("Empresas", len(companies))
    
    # Gráfico de pizza para tipos de máquinas
    if machines:
        type_counts = {}
        for m in machines:
            machine_type = m["type"]
            type_counts[machine_type] = type_counts.get(machine_type, 0) + 1
        
        df_types = pd.DataFrame({
            "Tipo de Máquina": list(type_counts.keys()),
            "Quantidade": list(type_counts.values())
        })
        
        fig = px.pie(df_types, values="Quantidade", names="Tipo de Máquina", title="Distribuição por Tipo de Máquina")
        st.plotly_chart(fig)
    
    # Exibir manutenções próximas
    if upcoming_maintenances:
        st.subheader("Manutenções Próximas (próximos 7 dias)")
        
        # Adicionar nome da máquina e nome da empresa para melhor legibilidade
        for m in upcoming_maintenances:
            # Obter detalhes da máquina
            machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
            if machine:
                m["machine_name"] = machine["name"]
                
                # Obter detalhes da empresa
                company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                if company:
                    m["company_name"] = company["name"]
        
        # Converter para DataFrame para exibição agradável
        df_upcoming = pd.DataFrame(upcoming_maintenances)
        if not df_upcoming.empty:
            # Reordenar e selecionar colunas para exibição
            columns_to_show = []
            if "scheduled_date" in df_upcoming.columns:
                columns_to_show.append("scheduled_date")
            if "type" in df_upcoming.columns:
                columns_to_show.append("type")
            if "machine_name" in df_upcoming.columns:
                columns_to_show.append("machine_name")
            if "company_name" in df_upcoming.columns:
                columns_to_show.append("company_name")
            if "notes" in df_upcoming.columns:
                columns_to_show.append("notes")
            
            # Mostrar DataFrame com colunas selecionadas
            if columns_to_show:
                st.dataframe(df_upcoming[columns_to_show])
            else:
                st.dataframe(df_upcoming)
        else:
            st.info("Nenhuma manutenção agendada nos próximos 7 dias.")
    else:
        st.info("Nenhuma manutenção agendada nos próximos 7 dias.")