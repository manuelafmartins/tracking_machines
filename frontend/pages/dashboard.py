# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from frontend.utils.api import get_api_data
from frontend.utils.auth import is_admin

def show_dashboard():
    """Exibe o dashboard principal com métricas e gráficos"""
    st.title("Fleet Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Fetch data from the API - different behavior based on user role
    if is_admin():
        # Admin sees all data
        machines = get_api_data("machines") or []
        maintenances = get_api_data("maintenances") or []
        companies = get_api_data("companies") or []
    else:
        # Fleet manager sees only their company's data
        company_id = st.session_state.get("company_id")
        if company_id:
            machines = get_api_data(f"machines/company/{company_id}") or []
            maintenances = get_api_data(f"maintenances/company/{company_id}") or []
            companies = [get_api_data(f"companies/{company_id}")] if get_api_data(f"companies/{company_id}") else []
        else:
            machines = []
            maintenances = []
            companies = []
    
    # Calculate upcoming maintenances within 7 days
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    # Filter upcoming maintenances
    upcoming_maintenances = []
    for m in maintenances:
        # Convert "scheduled_date" from string to date
        sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
        if today <= sched_date <= next_week and not m.get("completed", False):
            upcoming_maintenances.append(m)
    
    col1.metric("Total Machines", len(machines))
    col2.metric("Upcoming Maintenances", len(upcoming_maintenances))
    col3.metric("Companies", len(companies))
    
    # Pie chart for machine types
    if machines:
        type_counts = {}
        for m in machines:
            machine_type = m["type"]
            type_counts[machine_type] = type_counts.get(machine_type, 0) + 1
        
        df_types = pd.DataFrame({
            "Machine Type": list(type_counts.keys()),
            "Count": list(type_counts.values())
        })
        
        fig = px.pie(df_types, values="Count", names="Machine Type", title="Distribution by Machine Type")
        st.plotly_chart(fig)
    
    # Display upcoming maintenances
    if upcoming_maintenances:
        st.subheader("Upcoming Maintenances (next 7 days)")
        
        # Add machine name and company name for better readability
        for m in upcoming_maintenances:
            # Get machine details
            machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
            if machine:
                m["machine_name"] = machine["name"]
                
                # Get company details
                company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                if company:
                    m["company_name"] = company["name"]
        
        # Convert to DataFrame for nice display
        df_upcoming = pd.DataFrame(upcoming_maintenances)
        if not df_upcoming.empty:
            # Reorder and select columns for display
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
            
            # Show DataFrame with selected columns
            if columns_to_show:
                st.dataframe(df_upcoming[columns_to_show])
            else:
                st.dataframe(df_upcoming)
        else:
            st.info("No maintenances scheduled in the next 7 days.")
    else:
        st.info("No maintenances scheduled in the next 7 days.")