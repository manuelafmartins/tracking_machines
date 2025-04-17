import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import calendar
from frontend.utils.api import get_api_data
from frontend.utils.auth import is_admin
import locale

try:
    locale.setlocale(locale.LC_TIME, "pt_PT.UTF-8")
except locale.Error:
    # Fall back silently if the locale is unavailable on the host system
    pass

def show_dashboard():
    """Display the main fleet dashboard with metrics and advanced charts.

    All UI labels are shown in Portuguese; the code (variables, comments and
    doc‑strings) remains in English.
    """

    # Title -----------------------------------------------------------------
    st.title("Dashboard da Frota")

    
    # ----------------------------------------------------------------------
    # Data fetching
    # ----------------------------------------------------------------------
    if is_admin():
        machines = get_api_data("machines") or []
        maintenances = get_api_data("maintenances") or []
        companies = get_api_data("companies") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            machines = get_api_data(f"machines/company/{company_id}") or []
            maintenances = get_api_data(f"maintenances/company/{company_id}") or []
            company_data = get_api_data(f"companies/{company_id}")
            companies = [company_data] if company_data else []
        else:
            machines, maintenances, companies = [], [], []
    
    # ----------------------------------------------------------------------
    # Helpers and filters
    # ----------------------------------------------------------------------
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    next_month = today + timedelta(days=30)

    upcoming_maintenances: list[dict] = []
    completed_maintenances: list[dict] = []
    overdue_maintenances: list[dict] = []

    for m in maintenances:
        scheduled_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
        if m.get("completed", False):
            completed_maintenances.append(m)
        elif scheduled_date < today:
            m["days_overdue"] = (today - scheduled_date).days
            overdue_maintenances.append(m)
        elif today <= scheduled_date <= next_week:
            m["days_remaining"] = (scheduled_date - today).days
            upcoming_maintenances.append(m)
    
    # ----------------------------------------------------------------------
    # TABS ------------------------------------------------------------------
    # ----------------------------------------------------------------------
    tab_overview, tab_status, tab_analysis = st.tabs([
        "Visão Geral",
        "Estado da Manutenção",
        "Análise da Frota",
    ])

    # ----------------------------------------------------------------------
    # TAB 1 – OVERVIEW ------------------------------------------------------
    # ----------------------------------------------------------------------
    with tab_overview:
        st.subheader("Visão Geral da Frota")

        # METRIC CARDS ------------------------------------------------------
        card_col1, card_col2, card_col3, card_col4 = st.columns(4)

        # Total machines
        with card_col1:
            st.markdown(
                f"""
                <div style='background-color:#1E88E5;padding:10px;border-radius:10px;text-align:center'>
                    <h1 style='color:white;font-size:36px'>{len(machines)}</h1>
                    <p style='color:white;font-size:16px'>Total de Máquinas</p>
                </div>""",
                unsafe_allow_html=True,
            )

        # Upcoming maintenances
        with card_col2:
            st.markdown(
                f"""
                <div style='background-color:#FFC107;padding:10px;border-radius:10px;text-align:center'>
                    <h1 style='color:white;font-size:36px'>{len(upcoming_maintenances)}</h1>
                    <p style='color:white;font-size:16px'>Manutenções Próximas</p>
                </div>""",
                unsafe_allow_html=True,
            )

        # Overdue maintenances
        with card_col3:
            st.markdown(
                f"""
                <div style='background-color:#F44336;padding:10px;border-radius:10px;text-align:center'>
                    <h1 style='color:white;font-size:36px'>{len(overdue_maintenances)}</h1>
                    <p style='color:white;font-size:16px'>Manutenções Atrasadas</p>
                </div>""",
                unsafe_allow_html=True,
            )

        # Companies
        with card_col4:
            st.markdown(
                f"""
                <div style='background-color:#4CAF50;padding:10px;border-radius:10px;text-align:center'>
                    <h1 style='color:white;font-size:36px'>{len(companies)}</h1>
                    <p style='color:white;font-size:16px'>Empresas</p>
                </div>""",
                unsafe_allow_html=True,
            )

        # DISTRIBUTION CHARTS ----------------------------------------------
        st.markdown("### Distribuição da Frota")
        dist_col1, dist_col2 = st.columns(2)

        # Distribution by machine type (pie) --------------------------------
        with dist_col1:
            if machines:
                type_counts: dict[str, int] = {}
                for m in machines:
                    m_type = m["type"]
                    type_counts[m_type] = type_counts.get(m_type, 0) + 1

                df_types = pd.DataFrame(
                    {"Tipo de Máquina": list(type_counts.keys()), "Quantidade": list(type_counts.values())}
                )

                fig = px.pie(
                    df_types,
                    values="Quantidade",
                    names="Tipo de Máquina",
                    title="Distribuição por Tipo de Máquina",
                    color_discrete_sequence=px.colors.sequential.Blues,
                    hole=0.4,
                )
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                    margin=dict(t=60, b=0, l=0, r=0),
                    height=320,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de máquinas disponíveis para mostrar a distribuição.")

        # Distribution by company (admin) -----------------------------------
        with dist_col2:
            if is_admin() and machines and len(companies) > 1:
                company_machine_counts: dict[str, int] = {}
                for m in machines:
                    comp_id = m["company_id"]
                    comp_name = next((c["name"] for c in companies if c["id"] == comp_id), "Desconhecida")
                    company_machine_counts[comp_name] = company_machine_counts.get(comp_name, 0) + 1

                df_company = pd.DataFrame(
                    {"Empresa": list(company_machine_counts.keys()), "Máquinas": list(company_machine_counts.values())}
                )

                fig = px.bar(
                    df_company,
                    x="Empresa",
                    y="Máquinas",
                    title="Máquinas por Empresa",
                    color="Máquinas",
                    color_continuous_scale=px.colors.sequential.Viridis,
                )
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Número de Máquinas",
                    margin=dict(t=60, b=0, l=0, r=0),
                    height=320,
                )
                st.plotly_chart(fig, use_container_width=True)
            elif not is_admin() and machines:
                status_counts = {
                    "Próximas": len(upcoming_maintenances),
                    "Concluídas": len(completed_maintenances),
                    "Atrasadas": len(overdue_maintenances),
                }
                if sum(status_counts.values()) > 0:
                    df_status = pd.DataFrame({"Estado": status_counts.keys(), "Quantidade": status_counts.values()})
                    fig = px.pie(
                        df_status,
                        values="Quantidade",
                        names="Estado",
                        title="Visão Geral do Estado da Manutenção",
                        color="Estado",
                        color_discrete_map={
                            "Próximas": "#FFC107",
                            "Concluídas": "#4CAF50",
                            "Atrasadas": "#F44336",
                        },
                        hole=0.4,
                    )
                    fig.update_layout(
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                        margin=dict(t=60, b=0, l=0, r=0),
                        height=320,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem dados de manutenção disponíveis para mostrar.")
            else:
                st.info("Sem dados disponíveis para mostrar a distribuição.")

        # MAINTENANCE CALENDAR ---------------------------------------------
        st.markdown("### Calendário de Manutenções (Próximos 30 Dias)")
        calendar_events: list[dict] = []
        for m in maintenances:
            sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
            if today <= sched_date <= next_month and not m.get("completed", False):
                machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                if machine:
                    m["machine_name"] = machine["name"]
                    if is_admin():
                        company = next((c for c in companies if c["id"] == machine["company_id"]), None)
                        if company:
                            m["company_name"] = company["name"]
                calendar_events.append(m)

        if calendar_events:
            days = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
            weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            events_per_day = {day: 0 for day in days}
            for m in calendar_events:
                events_per_day[m["scheduled_date"]] += 1

            week_data: list[list[int]] = [0] * 7
            calendar_data: list[list[int]] = []
            for idx, day in enumerate(days):
                weekday = datetime.strptime(day, "%Y-%m-%d").weekday()
                week_data[weekday] = events_per_day[day]
                # Close the week either on Sunday or on the last iteration
                if weekday == 6 or day == days[-1]:
                    calendar_data.append(week_data)
                    week_data = [0] * 7

            fig = go.Figure(
                data=go.Heatmap(
                    z=calendar_data,
                    x=weekdays,
                    y=[f"Semana {i+1}" for i in range(len(calendar_data))],
                    colorscale="YlOrRd",
                    showscale=False,
                )
            )
            fig.update_layout(title="Mapa de Calor de Eventos de Manutenção", height=250, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Ver Detalhes das Próximas Manutenções", expanded=True):
                events_by_date: dict[str, list[dict]] = {}
                for ev in calendar_events:
                    events_by_date.setdefault(ev["scheduled_date"], []).append(ev)

                for date_str in sorted(events_by_date.keys())[:10]:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                    formatted_date = date_obj.strftime("%A, %d %B %Y")
                    st.markdown(f"**{formatted_date}**")
                    for ev in events_by_date[date_str]:
                        machine_nm = ev.get("machine_name", "")
                        comp_info = f" - {ev.get('company_name', '')}" if is_admin() and ev.get("company_name") else ""
                        st.markdown(f"* {ev['type']} para **{machine_nm}**{comp_info}")
                    st.markdown("---")
        else:
            st.info("Não existem eventos de manutenção agendados para os próximos 30 dias.")

    # ----------------------------------------------------------------------
    # TAB 2 – MAINTENANCE STATUS ------------------------------------------
    # ----------------------------------------------------------------------
    with tab_status:
        st.subheader("Estado da Manutenção")
        
        # Key Performance Indicators
        maintenance_kpis = st.columns(3)
        
        with maintenance_kpis[0]:
            # Calculate completion rate
            total_past_maintenances = len(completed_maintenances) + len(overdue_maintenances)
            completion_rate = (len(completed_maintenances) / total_past_maintenances * 100) if total_past_maintenances > 0 else 0
            
            st.markdown(
                f"""
                <div style="background-color:#E8F5E9; padding:15px; border-radius:10px; text-align:center; border-left:5px solid #4CAF50">
                    <h2 style="color:#4CAF50; margin:0">Taxa de Conclusão</h2>
                    <h1 style="font-size:36px; margin:10px 0">{completion_rate:.1f}%</h1>
                    <p>{len(completed_maintenances)} de {total_past_maintenances} manutenções concluídas</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with maintenance_kpis[1]:
            # Calculate average delay for overdue maintenances
            avg_delay = sum(m.get("days_overdue", 0) for m in overdue_maintenances) / len(overdue_maintenances) if overdue_maintenances else 0
            
            st.markdown(
                f"""
                <div style="background-color:#FFEBEE; padding:15px; border-radius:10px; text-align:center; border-left:5px solid #F44336">
                    <h2 style="color:#F44336; margin:0">Atraso Médio</h2>
                    <h1 style="font-size:36px; margin:10px 0">{avg_delay:.1f} dias</h1>
                    <p>{len(overdue_maintenances)} manutenções atrasadas</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with maintenance_kpis[2]:
            # Calculate upcoming workload
            upcoming_workload = len(upcoming_maintenances)
            
            st.markdown(
                f"""
                <div style="background-color:#FFF8E1; padding:15px; border-radius:10px; text-align:center; border-left:5px solid #FFC107">
                    <h2 style="color:#FFA000; margin:0">Carga de Trabalho Próxima</h2>
                    <h1 style="font-size:36px; margin:10px 0">{upcoming_workload}</h1>
                    <p>Manutenções nos próximos 7 dias</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Maintenance Timeline
        st.markdown("### Linha do Tempo de Manutenções")
        
        if maintenances:
            # Prepare data for timeline
            timeline_data = []
            
            for m in maintenances:
                machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                machine_name = machine["name"] if machine else ""
                
                # Get company info if admin
                company_name = ""
                if is_admin() and machine:
                    company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                    company_name = company["name"] if company else "Empresa Desconhecida"
                
                scheduled_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
                
                # Determine status and color
                if m.get("completed", False):
                    status = "Concluída"
                    color = "#4CAF50"
                elif scheduled_date < today:
                    status = "Atrasada"
                    color = "#F44336"
                elif today <= scheduled_date <= next_week:
                    status = "Próxima"
                    color = "#FFC107"
                else:
                    status = "Agendada"
                    color = "#2196F3"
                
                # Create entry for the timeline
                entry = {
                    "ID": m["id"],
                    "Type": m["type"],
                    "Machine": machine_name,
                    "Company": company_name,
                    "Date": scheduled_date,
                    "Status": status,
                    "Color": color
                }
                
                timeline_data.append(entry)
            
            # Sort by date
            timeline_data = sorted(timeline_data, key=lambda x: x["Date"])
            
            # Create timeline visualization
            fig = go.Figure()
            
            for status, color in [("Concluída", "#4CAF50"), ("Atrasada", "#F44336"), ("Próxima", "#FFC107"), ("Agendada", "#2196F3")]:
                # Filter entries by status
                entries = [e for e in timeline_data if e["Status"] == status]
                
                if entries:
                    # Add trace for this status
                    fig.add_trace(go.Scatter(
                        x=[e["Date"] for e in entries],
                        y=[e["Machine"] for e in entries],
                        mode="markers",
                        marker=dict(
                            symbol="circle",
                            size=16,
                            color=color
                        ),
                        name=status,
                        text=[f"Tipo: {e['Type']}<br>Data: {e['Date']}<br>Estado: {e['Status']}" + 
                              (f"<br>Empresa: {e['Company']}" if e['Company'] else "") 
                              for e in entries],
                        hoverinfo="text"
                    ))
            
            # Layout
            fig.update_layout(
                title="Linha do Tempo de Manutenções",
                xaxis=dict(
                    title="Data",
                    tickformat="%d %b %Y",
                    range=[
                        (today - timedelta(days=30)),  # 30 days ago
                        (today + timedelta(days=60))   # 60 days in future
                    ]
                ),
                yaxis=dict(
                    title="Máquina",
                ),
                height=400,
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Add today line
            fig.add_vline(
                x=today,
                line_width=2,
                line_dash="dash",
                line_color="gray",
                annotation_text="Hoje",
                annotation_position="top right"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há dados de manutenção disponíveis para a linha do tempo.")
        
        # Maintenance Tables
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Manutenções Atrasadas")
            if overdue_maintenances:
                # Add machine name and company info
                for m in overdue_maintenances:
                    machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                    m["machine_name"] = machine["name"] if machine else "Máquina Desconhecida"
                    
                    # Add company info if admin
                    if is_admin() and machine:
                        company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                        m["company_name"] = company["name"] if company else "Empresa Desconhecida"
                
                # Sort by days overdue (most overdue first)
                overdue_maintenances = sorted(overdue_maintenances, key=lambda x: x.get("days_overdue", 0), reverse=True)
                
                for m in overdue_maintenances:
                    days_overdue = m.get("days_overdue", 0)
                    company_info = f" - {m.get('company_name', '')}" if is_admin() and "company_name" in m else ""
                    
                    st.markdown(
                        f"""
                        <div style="background-color:#FFEBEE; margin-bottom:10px; padding:10px; border-radius:5px; border-left:5px solid #F44336">
                            <div style="display:flex; justify-content:space-between">
                                <div>
                                    <h4 style="margin:0">{m.get('machine_name', 'Máquina Desconhecida')}{company_info}</h4>
                                    <p style="margin:5px 0">{m['type']}</p>
                                </div>
                                <div style="text-align:right">
                                    <p style="color:#F44336; font-weight:bold; margin:0">{days_overdue} dias de atraso</p>
                                    <p style="margin:5px 0">Data: {m['scheduled_date']}</p>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.success("Não há manutenções atrasadas!")
        
        with col2:
            st.markdown("### Manutenções Próximas")
            if upcoming_maintenances:
                # Add machine name and company info
                for m in upcoming_maintenances:
                    machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                    m["machine_name"] = machine["name"] if machine else "Máquina Desconhecida"
                    
                    # Add company info if admin
                    if is_admin() and machine:
                        company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                        m["company_name"] = company["name"] if company else "Empresa Desconhecida"
                
                # Sort by days remaining (soonest first)
                upcoming_maintenances = sorted(upcoming_maintenances, key=lambda x: x.get("days_remaining", 0))
                
                for m in upcoming_maintenances:
                    days_remaining = m.get("days_remaining", 0)
                    company_info = f" - {m.get('company_name', '')}" if is_admin() and "company_name" in m else ""
                    
                    # Color based on urgency
                    bg_color = "#FFF8E1"
                    border_color = "#FFC107"
                    if days_remaining <= 1:
                        bg_color = "#FFF3E0"
                        border_color = "#FF9800"
                    
                    st.markdown(
                        f"""
                        <div style="background-color:{bg_color}; margin-bottom:10px; padding:10px; border-radius:5px; border-left:5px solid {border_color}">
                            <div style="display:flex; justify-content:space-between">
                                <div>
                                    <h4 style="margin:0">{m.get('machine_name', 'Máquina Desconhecida')}{company_info}</h4>
                                    <p style="margin:5px 0">{m['type']}</p>
                                </div>
                                <div style="text-align:right">
                                    <p style="color:{border_color}; font-weight:bold; margin:0">Em {days_remaining} dias</p>
                                    <p style="margin:5px 0">Data: {m['scheduled_date']}</p>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("Não há manutenções agendadas para os próximos 7 dias.")
                
    with tab_analysis:
        # Fleet Analysis Tab
        st.subheader("Análise da Frota")
        
        # Health Score calculation
        if machines and maintenances:
            # Calculate health score for each machine
            machine_health = {}
            machine_maint_history = {}
            
            # Group maintenances by machine
            for m in maintenances:
                machine_id = m["machine_id"]
                if machine_id not in machine_maint_history:
                    machine_maint_history[machine_id] = []
                machine_maint_history[machine_id].append(m)
            
            # Calculate health score
            for machine in machines:
                machine_id = machine["id"]
                
                # Base health score starts at 100
                health_score = 100
                maintenance_count = 0
                overdue_count = 0
                
                if machine_id in machine_maint_history:
                    # Count all maintenances and overdue ones
                    for m in machine_maint_history[machine_id]:
                        maintenance_count += 1
                        
                        # Check if maintenance is overdue
                        sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
                        if sched_date < today and not m.get("completed", False):
                            overdue_count += 1
                            # Deduct points for overdue maintenances
                            days_overdue = (today - sched_date).days
                            health_score -= min(40, days_overdue * 2)  # Cap at -40 points
                    
                    # Adjust score based on maintenance history
                    if maintenance_count > 0:
                        completion_rate = (maintenance_count - overdue_count) / maintenance_count
                        health_score *= (0.5 + 0.5 * completion_rate)  # Scale factor based on completion
                
                # Ensure score is between 0 and 100
                health_score = max(0, min(100, health_score))
                
                # Store health score
                machine["health_score"] = health_score
                
                # Add machine name for display
                machine_name = machine["name"]
                machine_health[machine_name] = health_score
            
            # Gauge chart for fleet health
            avg_health = sum(m["health_score"] for m in machines) / len(machines)
            
            # Gauge figure
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_health,
                title={"text": "Média da Frota"},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "rgba(0,0,0,0)"},
                    "steps": [
                        {"range": [0, 50], "color": "lightcoral"},
                        {"range": [50, 75], "color": "gold"},
                        {"range": [75, 100], "color": "lightgreen"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": avg_health
                    }
                }
            ))
            
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Machine health scores
            st.markdown("### Pontuação de Máquinas")
            
            # Convert to DataFrame
            health_df = pd.DataFrame({
                "Máquina": list(machine_health.keys()),
                "Pontuação": list(machine_health.values())
            })
            
            # Sort by health score (ascending, so worst first)
            health_df = health_df.sort_values("Pontuação")
            
            # Bar chart for machine health
            if not health_df.empty:
                fig = px.bar(
                    health_df,
                    x="Máquina",
                    y="Pontuação",
                    title="Pontuação por Máquina",
                    color="Pontuação",
                    color_continuous_scale=["red", "orange", "green"],
                    range_color=[0, 100]
                )
                
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Pontuação ",
                    yaxis=dict(range=[0, 100]),
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Health breakdown table
                with st.expander("Detalhes da Pontuação", expanded=False):
                    # Create summary table
                    health_details = []
                    
                    for machine in machines:
                        machine_id = machine["id"]
                        machine_name = machine["name"]
                        health_score = machine["health_score"]
                        
                        # Get maintenance counts
                        total_maint = 0
                        completed_maint = 0
                        overdue_maint = 0
                        
                        if machine_id in machine_maint_history:
                            for m in machine_maint_history[machine_id]:
                                total_maint += 1
                                if m.get("completed", False):
                                    completed_maint += 1
                                elif datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date() < today:
                                    overdue_maint += 1
                        
                        # Create detail row
                        detail = {
                            "Máquina": machine_name,
                            "Pontuação": f"{health_score:.1f}",
                            "Total de Manutenções": total_maint,
                            "Concluídas": completed_maint,
                            "Atrasadas": overdue_maint,
                            "Taxa de Conclusão": f"{(completed_maint / total_maint * 100):.1f}%" if total_maint > 0 else "N/A"
                        }
                        
                        health_details.append(detail)
                    
                    # Convert to DataFrame and display
                    health_details_df = pd.DataFrame(health_details)
                    st.dataframe(health_details_df)
            else:
                st.info("Não há dados das máquinas disponíveis.")
            
            # Maintenance Type Analysis
            if maintenances:
                st.markdown("### Análise por Tipo de Manutenção")
                
                # Count maintenances by type
                maint_types = {}
                for m in maintenances:
                    maint_type = m["type"]
                    if maint_type not in maint_types:
                        maint_types[maint_type] = {"count": 0, "completed": 0}
                    
                    maint_types[maint_type]["count"] += 1
                    if m.get("completed", False):
                        maint_types[maint_type]["completed"] += 1
                
                # Create DataFrame
                maint_type_data = []
                for mtype, data in maint_types.items():
                    maint_type_data.append({
                        "Tipo": mtype,
                        "Quantidade": data["count"],
                        "Concluídas": data["completed"],
                        "Taxa de Conclusão": data["completed"] / data["count"] if data["count"] > 0 else 0
                    })
                
                maint_type_df = pd.DataFrame(maint_type_data)
                
                # Only show if there's data
                if not maint_type_df.empty:
                    # Create two-column layout
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Bar chart for maintenance types
                        fig = px.bar(
                            maint_type_df,
                            x="Tipo",
                            y="Quantidade",
                            title="Quantidade de Manutenções por Tipo",
                            color="Tipo"
                        )
                        
                        fig.update_layout(
                            xaxis_title="",
                            yaxis_title="Número de Manutenções",
                            height=350,
                            margin=dict(l=0, r=0, t=40, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Completion rate by type
                        fig = px.bar(
                            maint_type_df,
                            x="Tipo",
                            y="Taxa de Conclusão",
                            title="Taxa de Conclusão por Tipo",
                            color="Tipo",
                            text_auto='.0%'
                        )
                        
                        fig.update_layout(
                            xaxis_title="",
                            yaxis_title="Taxa de Conclusão",
                            yaxis=dict(tickformat='.0%'),
                            height=350,
                            margin=dict(l=0, r=0, t=40, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados de tipos de manutenção disponíveis para análise.")
        else:
            st.info("Dados insuficientes para calcular pontuações de saúde. Adicione máquinas e registros de manutenção para ver análises detalhadas.")
        
        # Machine Utilization and Performance (admin only)
        if is_admin() and machines and companies:
            st.markdown("### Utilização de Máquinas por Empresa")
            
            # Calculate machine counts by company
            company_machine_counts = {}
            for company in companies:
                company_id = company["id"]
                company_name = company["name"]
                company_machines = [m for m in machines if m["company_id"] == company_id]
                
                company_machine_counts[company_name] = len(company_machines)
            
            # Create DataFrame
            company_df = pd.DataFrame({
                "Empresa": list(company_machine_counts.keys()),
                "Quantidade de Máquinas": list(company_machine_counts.values())
            })
            
            # Sort by machine count (descending)
            company_df = company_df.sort_values("Quantidade de Máquinas", ascending=False)
            
            # Bar chart
            if not company_df.empty:
                fig = px.bar(
                    company_df,
                    x="Empresa",
                    y="Quantidade de Máquinas",
                    title="Quantidade de Máquinas por Empresa",
                    color="Quantidade de Máquinas",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Número de Máquinas",
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados de empresas disponíveis para análise.")

def format_maintenance_date(date_str):
    """Format a date string as a more readable format"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    return date_obj.strftime("%d %b, %Y")