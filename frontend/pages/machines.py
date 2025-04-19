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
import json
import re

def get_vehicle_info_by_plate(license_plate):
    """
    Função de exemplo para obter informações de um veículo pela matrícula.
    Em um ambiente de produção, isso conectaria com uma API externa de consulta veicular.
    """
    # Simulação de dados - em produção, isto seria uma chamada a uma API real
    # Formato simplificado da matrícula portuguesa: 00-AA-00
    if re.match(r'^\d{2}-[A-Z]{2}-\d{2}$', license_plate):
        vehicle_info = {
            "brand": "Modelo simulado",
            "model": "Baseado na matrícula " + license_plate,
            "year": 2020,
            "vin": "SAMPLE" + license_plate.replace("-", "")
        }
        return vehicle_info
    return None

def show_machines():
    title_col, btn_col = st.columns([9, 1])
    
    with title_col:
        st.title("Gestão de Máquinas")
    
    with btn_col:
        # Inicializar o estado do formulário se não existir
        if "show_add_machine_form" not in st.session_state:
            st.session_state["show_add_machine_form"] = False
        
        # Adicionar espaço para alinhar com o título
        st.write("")
        st.write("")
        
        # Usar um único botão Streamlit, mas garantir que tenha o texto certo
        if st.session_state["show_add_machine_form"]:
            button_symbol = "Fechar"
        else:
            button_symbol = "Adicionar"
        
        # Botão simples do Streamlit
        if st.button(button_symbol, key="add_machine_button"):
            st.session_state["show_add_machine_form"] = not st.session_state["show_add_machine_form"]
            st.rerun()
    
    # Fetch companies for the dropdown - admin sees all, fleet manager sees only their own
    if is_admin():
        companies = get_api_data("companies") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            company = get_api_data(f"companies/{company_id}")
            companies = [company] if company else []
        else:
            companies = []
    
    # Formulário de adição de máquina (apenas mostrado quando necessário)
    if st.session_state["show_add_machine_form"]:
        with st.form("new_machine"):
            st.subheader("Adicionar Nova Máquina")
            
            # Campos básicos
            machine_name = st.text_input("Nome da Máquina")
            
            # Seleção do tipo de máquina
            machine_type = st.selectbox("Tipo", ["truck", "fixed"], format_func=lambda x: "Camião" if x == "truck" else "Máquina Fixa")
            
            # Campos comuns para ambos os tipos
            col1, col2 = st.columns(2)
            with col1:
                brand = st.text_input("Marca")
                serial_number = st.text_input("Número de Série")
            with col2:
                model = st.text_input("Modelo")
                year = st.number_input("Ano", min_value=1900, max_value=datetime.now().year, value=datetime.now().year)
            
            purchase_date = st.date_input("Data de Aquisição", value=datetime.now().date())
            
            # Campos específicos baseados no tipo de máquina
            if machine_type == "truck":
                st.subheader("Detalhes do Camião")
                
                license_plate = st.text_input("Matrícula (formato: 00-AA-00)")
                
                # Botão para buscar informações do veículo
                if license_plate and st.button("Buscar Informações do Veículo", key="fetch_vehicle_info"):
                    vehicle_info = get_vehicle_info_by_plate(license_plate)
                    if vehicle_info:
                        st.session_state["vehicle_brand"] = vehicle_info["brand"]
                        st.session_state["vehicle_model"] = vehicle_info["model"]
                        st.session_state["vehicle_year"] = vehicle_info["year"]
                        st.session_state["vehicle_vin"] = vehicle_info["vin"]
                        st.success("Informações do veículo encontradas!")
                    else:
                        st.warning("Não foi possível encontrar informações para esta matrícula.")
                
                # Usar dados obtidos, se disponíveis
                if "vehicle_brand" in st.session_state and not brand:
                    brand = st.session_state["vehicle_brand"]
                if "vehicle_model" in st.session_state and not model:
                    model = st.session_state["vehicle_model"]
                if "vehicle_year" in st.session_state:
                    year = st.session_state["vehicle_year"]
                
                vin = st.text_input("VIN (Número de Identificação do Veículo)", 
                                     value=st.session_state.get("vehicle_vin", ""))
                
            elif machine_type == "fixed":
                st.subheader("Detalhes da Máquina Fixa")
                
                location = st.text_input("Localização")
                installation_date = st.date_input("Data de Instalação", value=purchase_date)
            
            # Seleção da empresa
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
                    st.warning("Não existem empresas disponíveis. Por favor, adicione uma empresa primeiro.")
                    selected_company_id = None
            else:
                # Fleet managers can only add machines to their company
                if companies:
                    selected_company_id = companies[0]["id"]
                    st.write(f"**Empresa:** {companies[0]['name']}")
                else:
                    st.warning("As informações da sua empresa não estão disponíveis.")
                    selected_company_id = None
            
            submitted = st.form_submit_button("Adicionar Máquina")
            
            if submitted and machine_name and selected_company_id:
                # Preparar dados para envio
                payload = {
                    "name": machine_name,
                    "type": machine_type,
                    "company_id": selected_company_id,
                    "brand": brand,
                    "model": model,
                    "year": year,
                    "serial_number": serial_number,
                    "purchase_date": purchase_date.isoformat()
                }
                
                # Adicionar campos específicos do tipo
                if machine_type == "truck":
                    payload["license_plate"] = license_plate
                    payload["vehicle_identification_number"] = vin
                elif machine_type == "fixed":
                    payload["location"] = location
                    payload["installation_date"] = installation_date.isoformat()
                
                if post_api_data("machines", payload):
                    st.success(f"Máquina '{machine_name}' adicionada com sucesso!")
                    # Esconder o formulário depois de adicionar com sucesso
                    st.session_state["show_add_machine_form"] = False
                    # Limpar informações do veículo em sessão
                    for key in ["vehicle_brand", "vehicle_model", "vehicle_year", "vehicle_vin"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
    
    
    st.subheader("Máquinas Atuais:")
    
    # Fetch machines - admins see all, fleet managers see only their company's
    if is_admin():
        machines = get_api_data("machines") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            machines = get_api_data(f"machines/company/{company_id}") or []
        else:
            machines = []
    
    if machines:
        # Convert to a DataFrame
        df_machines = pd.DataFrame(machines)
        
        # Add the company name for readability
        def get_company_name(cid):
            for c in companies:
                if c["id"] == cid:
                    return c["name"]
            return "Desconhecida"
        
        if "company_id" in df_machines.columns:
            df_machines["company_name"] = df_machines["company_id"].apply(get_company_name)
        
        # Display machines in expandable sections
        for idx, machine in df_machines.iterrows():
            machine_type_display = "Camião" if machine['type'] == "truck" else "Máquina Fixa"
            with st.expander(f"{machine['name']} ({machine_type_display}) - {machine.get('company_name', 'Empresa Desconhecida')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** {machine['id']}")
                    st.write(f"**Tipo:** {machine_type_display}")
                    st.write(f"**Empresa:** {machine.get('company_name', 'Desconhecida')}")
                    
                    # Exibir dados comuns
                    if machine.get('brand') or machine.get('model'):
                        brand_model = []
                        if machine.get('brand'):
                            brand_model.append(machine['brand'])
                        if machine.get('model'):
                            brand_model.append(machine['model'])
                        st.write(f"**Marca/Modelo:** {' '.join(brand_model)}")
                    
                    if machine.get('year'):
                        st.write(f"**Ano:** {machine['year']}")
                    
                    if machine.get('serial_number'):
                        st.write(f"**Número de Série:** {machine['serial_number']}")
                    
                    if machine.get('purchase_date'):
                        st.write(f"**Data de Aquisição:** {machine['purchase_date']}")
                    
                    # Exibir dados específicos do tipo
                    if machine['type'] == "truck":
                        st.subheader("Detalhes do Camião")
                        if machine.get('license_plate'):
                            st.write(f"**Matrícula:** {machine['license_plate']}")
                        if machine.get('vehicle_identification_number'):
                            st.write(f"**VIN:** {machine['vehicle_identification_number']}")
                    
                    elif machine['type'] == "fixed":
                        st.subheader("Detalhes da Máquina Fixa")
                        if machine.get('location'):
                            st.write(f"**Localização:** {machine['location']}")
                        if machine.get('installation_date'):
                            st.write(f"**Data de Instalação:** {machine['installation_date']}")
                    
                    # Display a button to view maintenances
                    if st.button("Ver Manutenções", key=f"view_maint_{machine['id']}"):
                        maintenances = get_api_data(f"maintenances/machine/{machine['id']}") or []
                        if maintenances:
                            st.write("**Manutenções Agendadas:**")
                            df_maint = pd.DataFrame(maintenances)
                            st.dataframe(df_maint[["scheduled_date", "type", "completed"]])
                        else:
                            st.info(f"Não existem manutenções agendadas para {machine['name']}")
                
                # Edit/Delete buttons
                with col2:
                    if st.button("Editar", key=f"edit_machine_{machine['id']}"):
                        st.session_state["edit_machine_id"] = machine["id"]
                        st.session_state["edit_machine_name"] = machine["name"]
                        st.session_state["edit_machine_type"] = machine["type"]
                        st.session_state["edit_machine_company_id"] = machine["company_id"]
                        # Adicionar campos expandidos
                        st.session_state["edit_machine_brand"] = machine.get("brand", "")
                        st.session_state["edit_machine_model"] = machine.get("model", "")
                        st.session_state["edit_machine_year"] = machine.get("year", datetime.now().year)
                        st.session_state["edit_machine_serial_number"] = machine.get("serial_number", "")
                        st.session_state["edit_machine_purchase_date"] = machine.get("purchase_date", datetime.now().date())
                        
                        # Campos específicos do tipo
                        if machine["type"] == "truck":
                            st.session_state["edit_machine_license_plate"] = machine.get("license_plate", "")
                            st.session_state["edit_machine_vin"] = machine.get("vehicle_identification_number", "")
                        elif machine["type"] == "fixed":
                            st.session_state["edit_machine_location"] = machine.get("location", "")
                            st.session_state["edit_machine_installation_date"] = machine.get("installation_date", datetime.now().date())
                    
                    # Delete machine button with confirmation
                    show_delete_button("machine", machine["id"], 
                        confirm_text=f"Tem certeza que deseja excluir {machine['name']}? Isto excluirá todas as manutenções relacionadas!")
            
            # Edit form appears if this machine is being edited
            if st.session_state.get("edit_machine_id") == machine["id"]:
                with st.form(f"edit_machine_{machine['id']}"):
                    st.subheader(f"Editar Máquina: {machine['name']}")
                    new_name = st.text_input("Nome da Máquina", value=st.session_state["edit_machine_name"])
                    new_type = st.selectbox("Tipo", ["truck", "fixed"], 
                                          index=0 if st.session_state["edit_machine_type"] == "truck" else 1,
                                          format_func=lambda x: "Camião" if x == "truck" else "Máquina Fixa")
                    
                    # Campos comuns
                    col1, col2 = st.columns(2)
                    with col1:
                        new_brand = st.text_input("Marca", value=st.session_state["edit_machine_brand"])
                        new_serial_number = st.text_input("Número de Série", value=st.session_state["edit_machine_serial_number"])
                    with col2:
                        new_model = st.text_input("Modelo", value=st.session_state["edit_machine_model"])
                        year_value = int(st.session_state["edit_machine_year"]) if st.session_state["edit_machine_year"] is not None else datetime.now().year

                        new_year = st.number_input(
                            "Ano", 
                            min_value=1900, 
                            max_value=int(datetime.now().year),
                            value=year_value
                        )
                    
                    # Data de aquisição
                    purchase_date_value = st.session_state["edit_machine_purchase_date"]
                    if isinstance(purchase_date_value, str):
                        purchase_date_value = datetime.strptime(purchase_date_value, "%Y-%m-%d").date()
                    new_purchase_date = st.date_input("Data de Aquisição", value=purchase_date_value)
                    
                    # Campos específicos do tipo
                    if new_type == "truck":
                        st.subheader("Detalhes do Camião")
                        new_license_plate = st.text_input("Matrícula", value=st.session_state.get("edit_machine_license_plate", ""))
                        new_vin = st.text_input("VIN", value=st.session_state.get("edit_machine_vin", ""))
                    elif new_type == "fixed":
                        st.subheader("Detalhes da Máquina Fixa")
                        new_location = st.text_input("Localização", value=st.session_state.get("edit_machine_location", ""))
                        
                        # Converter a data de instalação do formato string para date se necessário
                        installation_date_value = st.session_state.get("edit_machine_installation_date", new_purchase_date)
                        if isinstance(installation_date_value, str):
                            installation_date_value = datetime.strptime(installation_date_value, "%Y-%m-%d").date()
                        new_installation_date = st.date_input("Data de Instalação", value=installation_date_value)
                    
                    # Company selection - admin can change, fleet manager cannot
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
                        # Fleet managers can't change company
                        new_company_id = st.session_state["edit_machine_company_id"]
                        company_name = get_company_name(new_company_id)
                        st.write(f"**Empresa:** {company_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_edit = st.form_submit_button("Salvar Alterações")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancelar")
                    
                    if submit_edit and new_name:
                        # Construir os dados básicos de atualização
                        update_data = {
                            "name": new_name,
                            "type": new_type,
                            "company_id": new_company_id,
                            "brand": new_brand,
                            "model": new_model,
                            "year": new_year,
                            "serial_number": new_serial_number
                        }

                        # Adicionar a data de aquisição somente se não for None
                        if new_purchase_date is not None:
                            update_data["purchase_date"] = new_purchase_date.isoformat()
                                                
                        # Adicionar campos específicos do tipo
                        if new_type == "truck":
                            update_data["license_plate"] = new_license_plate
                            update_data["vehicle_identification_number"] = new_vin
                            # Remover campos da máquina fixa se mudar de tipo
                            update_data["location"] = None
                            update_data["installation_date"] = None
                        elif new_type == "fixed":
                            update_data["location"] = new_location
                            # Adicionar a data de instalação somente se não for None
                            if new_installation_date is not None:
                                update_data["installation_date"] = new_installation_date.isoformat()
                            # Remover campos do camião se mudar de tipo
                            update_data["license_plate"] = None
                            update_data["vehicle_identification_number"] = None
                                                    
                        # Enviar a atualização para a API
                        if put_api_data(f"machines/{machine['id']}", update_data):
                            st.success("Máquina atualizada com sucesso!")
                            # Limpar estado de edição
                            if "edit_machine_id" in st.session_state:
                                del st.session_state["edit_machine_id"]
                            st.rerun()
                    
                    if cancel_edit:
                        # Limpar estado de edição
                        if "edit_machine_id" in st.session_state:
                            del st.session_state["edit_machine_id"]
                        st.rerun()
    else:
        st.info("Nenhuma máquina encontrada.")
        
    # Adicionar filtros e visualizações 
    if machines:
        st.subheader("Análise da Frota")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.selectbox(
                "Filtrar por Tipo",
                ["Todos", "Camiões", "Máquinas Fixas"],
                key="machine_type_filter"
            )
        
        with col2:
            if is_admin() and len(companies) > 1:
                company_names = ["Todas"] + [c["name"] for c in companies]
                filter_company = st.selectbox(
                    "Filtrar por Empresa",
                    company_names,
                    key="machine_company_filter"
                )
            else:
                filter_company = "Todas"
        
        # Aplicar filtros
        filtered_machines = machines.copy()
        if filter_type == "Camiões":
            filtered_machines = [m for m in filtered_machines if m["type"] == "truck"]
        elif filter_type == "Máquinas Fixas":
            filtered_machines = [m for m in filtered_machines if m["type"] == "fixed"]
        
        if filter_company != "Todas" and is_admin():
            company_id = next((c["id"] for c in companies if c["name"] == filter_company), None)
            if company_id:
                filtered_machines = [m for m in filtered_machines if m["company_id"] == company_id]
        
        # Visualização
        if filtered_machines:
            # Converter para DataFrame para facilitar análise
            df = pd.DataFrame(filtered_machines)
            
            # Adicionar nomes das empresas
            if "company_id" in df.columns:
                df["company_name"] = df["company_id"].apply(get_company_name)
            
            # Adicionar nomes legíveis para tipos
            if "type" in df.columns:
                df["type_display"] = df["type"].apply(lambda x: "Camião" if x == "truck" else "Máquina Fixa")
            
            # Exibir estatísticas básicas
            st.subheader("Estatísticas da Frota")
            
            total_machines = len(filtered_machines)
            truck_count = len([m for m in filtered_machines if m["type"] == "truck"])
            fixed_count = len([m for m in filtered_machines if m["type"] == "fixed"])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Máquinas", total_machines)
            with col2:
                st.metric("Camiões", truck_count)
            with col3:
                st.metric("Máquinas Fixas", fixed_count)
            
            # Gráfico de distribuição por tipo
            st.subheader("Distribuição por Tipo")
            
            import plotly.express as px
            
            type_counts = {"Camiões": truck_count, "Máquinas Fixas": fixed_count}
            type_df = pd.DataFrame({
                "Tipo": list(type_counts.keys()),
                "Quantidade": list(type_counts.values())
            })
            
            fig = px.pie(
                type_df,
                values="Quantidade",
                names="Tipo",
                color="Tipo",
                color_discrete_map={
                    "Camiões": "#1F77B4",
                    "Máquinas Fixas": "#FF7F0E"
                },
                title="Distribuição de Máquinas por Tipo"
            )
            
            st.plotly_chart(fig)
            
            # Distribuição por idade (ano)
            if "year" in df.columns and not df["year"].isna().all():
                # Filtrar valores nulos
                year_df = df[df["year"].notna()].copy()
                
                # Agrupar por ano e contar
                year_counts = year_df.groupby("year").size().reset_index(name="count")
                year_counts = year_counts.sort_values("year")
                
                # Gráfico de barras por ano
                st.subheader("Distribuição por Ano")
                
                year_fig = px.bar(
                    year_counts,
                    x="year",
                    y="count",
                    labels={"year": "Ano", "count": "Quantidade"},
                    title="Distribuição de Máquinas por Ano"
                )
                
                st.plotly_chart(year_fig)
            
            # Se admin, mostrar distribuição por empresa
            if is_admin() and len(companies) > 1:
                # Agrupar por empresa e contar
                company_counts = df.groupby("company_name").size().reset_index(name="count")
                company_counts = company_counts.sort_values("count", ascending=False)
                
                st.subheader("Distribuição por Empresa")
                
                company_fig = px.bar(
                    company_counts,
                    x="company_name",
                    y="count",
                    labels={"company_name": "Empresa", "count": "Quantidade"},
                    title="Distribuição de Máquinas por Empresa"
                )
                
                st.plotly_chart(company_fig)
            
            # Tabela filtrada
            st.subheader("Tabela de Máquinas")
            
            # Selecionar e renomear colunas para exibição
            display_columns = ["name", "type_display", "brand", "model", "year"]
            if is_admin():
                display_columns.append("company_name")
            
            display_names = {
                "name": "Nome", 
                "type_display": "Tipo", 
                "brand": "Marca", 
                "model": "Modelo", 
                "year": "Ano",
                "company_name": "Empresa"
            }
            
            # Filtrar por colunas disponíveis
            valid_columns = [col for col in display_columns if col in df.columns]
            
            st.dataframe(
                df[valid_columns].rename(columns={col: display_names.get(col, col) for col in valid_columns}),
                use_container_width=True
            )
            
            # Opção para exportar
            if st.button("Exportar Lista de Máquinas (CSV)"):
                csv = df[valid_columns].to_csv(index=False)
                
                # Criar um link de download
                import base64
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="maquinas.csv">Download do arquivo CSV</a>'
                st.markdown(href, unsafe_allow_html=True)