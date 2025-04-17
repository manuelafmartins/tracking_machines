import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import calendar
from frontend.utils.api import get_api_data
from frontend.utils.auth import is_admin

def show_dashboard():
    """Exibe o dashboard principal com métricas e gráficos avançados"""
    st.title("Fleet Dashboard")
    
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
    
    # Calculate maintenance statistics
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    next_month = today + timedelta(days=30)
    
    # Filter upcoming maintenances
    upcoming_maintenances = []
    completed_maintenances = []
    overdue_maintenances = []
    for m in maintenances:
        # Convert "scheduled_date" from string to date
        sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
        if m.get("completed", False):
            completed_maintenances.append(m)
        elif sched_date < today:
            overdue_maintenances.append(m)
            m["days_overdue"] = (today - sched_date).days
        elif today <= sched_date <= next_week:
            m["days_remaining"] = (sched_date - today).days
            upcoming_maintenances.append(m)
    
    # Dashboard Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Maintenance Status", "Fleet Analysis"])
    
    with tab1:
        # Overview Tab
        st.subheader("Fleet Overview")
        
        # Colored Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        
        # Card 1: Total Machines
        with col1:
            st.markdown(
                f"""
                <div style="background-color:#1E88E5; padding:10px; border-radius:10px; text-align:center">
                    <h1 style="color:white; font-size:36px">{len(machines)}</h1>
                    <p style="color:white; font-size:16px">Total Machines</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Card 2: Upcoming Maintenances
        with col2:
            st.markdown(
                f"""
                <div style="background-color:#FFC107; padding:10px; border-radius:10px; text-align:center">
                    <h1 style="color:white; font-size:36px">{len(upcoming_maintenances)}</h1>
                    <p style="color:white; font-size:16px">Upcoming Maintenances</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Card 3: Overdue Maintenances
        with col3:
            st.markdown(
                f"""
                <div style="background-color:#F44336; padding:10px; border-radius:10px; text-align:center">
                    <h1 style="color:white; font-size:36px">{len(overdue_maintenances)}</h1>
                    <p style="color:white; font-size:16px">Overdue Maintenances</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Card 4: Companies
        with col4:
            st.markdown(
                f"""
                <div style="background-color:#4CAF50; padding:10px; border-radius:10px; text-align:center">
                    <h1 style="color:white; font-size:36px">{len(companies)}</h1>
                    <p style="color:white; font-size:16px">Companies</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Distribution Charts
        st.markdown("### Fleet Distribution")
        col1, col2 = st.columns(2)
        
        # Machine Type Distribution
        with col1:
            if machines:
                type_counts = {}
                for m in machines:
                    machine_type = m["type"]
                    type_counts[machine_type] = type_counts.get(machine_type, 0) + 1
                
                df_types = pd.DataFrame({
                    "Machine Type": list(type_counts.keys()),
                    "Count": list(type_counts.values())
                })
                
                fig = px.pie(
                    df_types, 
                    values="Count", 
                    names="Machine Type", 
                    title="Distribution by Machine Type",
                    color_discrete_sequence=px.colors.sequential.Blues,
                    hole=0.4
                )
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                    margin=dict(t=60, b=0, l=0, r=0),
                    height=320
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No machine data available to display distribution.")
        
        # Company Distribution (Admin only)
        with col2:
            if is_admin() and machines and len(companies) > 1:
                company_machine_counts = {}
                for m in machines:
                    company_id = m["company_id"]
                    company_name = next((c["name"] for c in companies if c["id"] == company_id), "Unknown")
                    company_machine_counts[company_name] = company_machine_counts.get(company_name, 0) + 1
                
                df_company = pd.DataFrame({
                    "Company": list(company_machine_counts.keys()),
                    "Machines": list(company_machine_counts.values())
                })
                
                fig = px.bar(
                    df_company, 
                    x="Company", 
                    y="Machines",
                    title="Machines by Company",
                    color="Machines",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Number of Machines",
                    margin=dict(t=60, b=0, l=0, r=0),
                    height=320
                )
                st.plotly_chart(fig, use_container_width=True)
            elif not is_admin() and machines:
                # For fleet managers, show a different visualization
                # For example, pie chart of machine types in their company
                maint_status_counts = {
                    "Upcoming": len(upcoming_maintenances),
                    "Completed": len(completed_maintenances),
                    "Overdue": len(overdue_maintenances)
                }
                
                df_status = pd.DataFrame({
                    "Status": list(maint_status_counts.keys()),
                    "Count": list(maint_status_counts.values())
                })
                
                # Only show if there's data
                if sum(maint_status_counts.values()) > 0:
                    fig = px.pie(
                        df_status, 
                        values="Count", 
                        names="Status", 
                        title="Maintenance Status Overview",
                        color="Status",
                        color_discrete_map={
                            "Upcoming": "#FFC107",
                            "Completed": "#4CAF50",
                            "Overdue": "#F44336"
                        },
                        hole=0.4
                    )
                    fig.update_layout(
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                        margin=dict(t=60, b=0, l=0, r=0),
                        height=320
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No maintenance data available to display distribution.")
            else:
                st.info("No data available to display distribution.")
        
        # Maintenance Calendar for the next 30 days
        st.markdown("### Maintenance Calendar (Next 30 Days)")
        
        # Collect maintenance events for the next 30 days
        calendar_maintenances = []
        for m in maintenances:
            sched_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
            if today <= sched_date <= next_month and not m.get("completed", False):
                # Get machine details
                machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                if machine:
                    m["machine_name"] = machine["name"]
                    
                    # Get company details if admin
                    if is_admin():
                        company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                        if company:
                            m["company_name"] = company["name"]
                
                calendar_maintenances.append(m)
        
        # Create calendar heatmap
        if calendar_maintenances:
            # Prepare data for heatmap
            days = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
            weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            
            # Count events per day
            events_per_day = {}
            for day in days:
                events_per_day[day] = 0
            
            for m in calendar_maintenances:
                day = m["scheduled_date"]
                if day in events_per_day:
                    events_per_day[day] += 1
            
            # Create a list for each week
            calendar_data = []
            week_data = [0] * 7  # 7 days in a week
            
            for day in days:
                date_obj = datetime.strptime(day, "%Y-%m-%d")
                weekday = date_obj.weekday()  # 0 for Monday, 6 for Sunday
                
                # Adjust week_data with the count for this day
                week_data[weekday] = events_per_day[day]
                
                # If it's the end of the week or the last day, add the week to calendar_data
                if weekday == 6 or day == days[-1]:
                    calendar_data.append(week_data)
                    week_data = [0] * 7
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=calendar_data,
                x=weekdays,
                y=[f"Week {i+1}" for i in range(len(calendar_data))],
                colorscale="YlOrRd",
                showscale=False
            ))
            
            fig.update_layout(
                title="Maintenance Events Heatmap",
                height=250,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show upcoming events as a list below the heatmap
            with st.expander("View Upcoming Maintenance Details", expanded=True):
                if calendar_maintenances:
                    # Group by date
                    events_by_date = {}
                    for event in calendar_maintenances:
                        date = event["scheduled_date"]
                        if date not in events_by_date:
                            events_by_date[date] = []
                        events_by_date[date].append(event)
                    
                    # Sort dates
                    sorted_dates = sorted(events_by_date.keys())
                    
                    for date in sorted_dates[:10]:  # Show only next 10 days with events
                        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                        date_str = date_obj.strftime("%A, %d %B %Y")
                        st.markdown(f"**{date_str}**")
                        
                        for event in events_by_date[date]:
                            machine_name = event.get("machine_name", "Unknown Machine")
                            company_info = f" - {event.get('company_name', '')}" if is_admin() and "company_name" in event else ""
                            st.markdown(f"* {event['type']} for **{machine_name}**{company_info}")
                        
                        st.markdown("---")
                else:
                    st.info("No upcoming maintenance events in the next 30 days.")
        else:
            st.info("No maintenance events scheduled for the next 30 days.")

    with tab2:
        # Maintenance Status Tab
        st.subheader("Maintenance Status")
        
        # Key Performance Indicators
        maintenance_kpis = st.columns(3)
        
        with maintenance_kpis[0]:
            # Calculate completion rate
            total_past_maintenances = len(completed_maintenances) + len(overdue_maintenances)
            completion_rate = (len(completed_maintenances) / total_past_maintenances * 100) if total_past_maintenances > 0 else 0
            
            st.markdown(
                f"""
                <div style="background-color:#E8F5E9; padding:15px; border-radius:10px; text-align:center; border-left:5px solid #4CAF50">
                    <h2 style="color:#4CAF50; margin:0">Completion Rate</h2>
                    <h1 style="font-size:36px; margin:10px 0">{completion_rate:.1f}%</h1>
                    <p>{len(completed_maintenances)} of {total_past_maintenances} maintenances completed</p>
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
                    <h2 style="color:#F44336; margin:0">Average Delay</h2>
                    <h1 style="font-size:36px; margin:10px 0">{avg_delay:.1f} days</h1>
                    <p>{len(overdue_maintenances)} overdue maintenances</p>
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
                    <h2 style="color:#FFA000; margin:0">Upcoming Workload</h2>
                    <h1 style="font-size:36px; margin:10px 0">{upcoming_workload}</h1>
                    <p>Maintenances in the next 7 days</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Maintenance Timeline
        st.markdown("### Maintenance Timeline")
        
        if maintenances:
            # Prepare data for timeline
            timeline_data = []
            
            for m in maintenances:
                machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                machine_name = machine["name"] if machine else "Unknown Machine"
                
                # Get company info if admin
                company_name = ""
                if is_admin() and machine:
                    company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                    company_name = company["name"] if company else "Unknown Company"
                
                scheduled_date = datetime.strptime(m["scheduled_date"], "%Y-%m-%d").date()
                
                # Determine status and color
                if m.get("completed", False):
                    status = "Completed"
                    color = "#4CAF50"
                elif scheduled_date < today:
                    status = "Overdue"
                    color = "#F44336"
                elif today <= scheduled_date <= next_week:
                    status = "Upcoming"
                    color = "#FFC107"
                else:
                    status = "Scheduled"
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
            
            for status, color in [("Completed", "#4CAF50"), ("Overdue", "#F44336"), ("Upcoming", "#FFC107"), ("Scheduled", "#2196F3")]:
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
                        text=[f"Type: {e['Type']}<br>Date: {e['Date']}<br>Status: {e['Status']}" + 
                              (f"<br>Company: {e['Company']}" if e['Company'] else "") 
                              for e in entries],
                        hoverinfo="text"
                    ))
            
            # Layout
            fig.update_layout(
                title="Maintenance Timeline",
                xaxis=dict(
                    title="Date",
                    tickformat="%d %b %Y",
                    range=[
                        (today - timedelta(days=30)),  # 30 days ago
                        (today + timedelta(days=60))   # 60 days in future
                    ]
                ),
                yaxis=dict(
                    title="Machine",
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
                annotation_text="Today",
                annotation_position="top right"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No maintenance data available for the timeline.")
        
        # Maintenance Tables
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Overdue Maintenances")
            if overdue_maintenances:
                # Add machine name and company info
                for m in overdue_maintenances:
                    machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                    m["machine_name"] = machine["name"] if machine else "Unknown Machine"
                    
                    # Add company info if admin
                    if is_admin() and machine:
                        company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                        m["company_name"] = company["name"] if company else "Unknown Company"
                
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
                                    <h4 style="margin:0">{m.get('machine_name', 'Unknown Machine')}{company_info}</h4>
                                    <p style="margin:5px 0">{m['type']}</p>
                                </div>
                                <div style="text-align:right">
                                    <p style="color:#F44336; font-weight:bold; margin:0">{days_overdue} days overdue</p>
                                    <p style="margin:5px 0">Due: {m['scheduled_date']}</p>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.success("No overdue maintenances! 🎉")
        
        with col2:
            st.markdown("### Upcoming Maintenances")
            if upcoming_maintenances:
                # Add machine name and company info
                for m in upcoming_maintenances:
                    machine = next((mac for mac in machines if mac["id"] == m["machine_id"]), None)
                    m["machine_name"] = machine["name"] if machine else "Unknown Machine"
                    
                    # Add company info if admin
                    if is_admin() and machine:
                        company = next((comp for comp in companies if comp["id"] == machine["company_id"]), None)
                        m["company_name"] = company["name"] if company else "Unknown Company"
                
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
                                    <h4 style="margin:0">{m.get('machine_name', 'Unknown Machine')}{company_info}</h4>
                                    <p style="margin:5px 0">{m['type']}</p>
                                </div>
                                <div style="text-align:right">
                                    <p style="color:{border_color}; font-weight:bold; margin:0">In {days_remaining} days</p>
                                    <p style="margin:5px 0">Date: {m['scheduled_date']}</p>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("No upcoming maintenances in the next 7 days.")
                
    with tab3:
        # Fleet Analysis Tab
        st.subheader("Fleet Analysis")
        
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
                title={"text": "Average Fleet Health"},
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
            st.markdown("### Machine Health Scores")
            
            # Convert to DataFrame
            health_df = pd.DataFrame({
                "Machine": list(machine_health.keys()),
                "Health Score": list(machine_health.values())
            })
            
            # Sort by health score (ascending, so worst first)
            health_df = health_df.sort_values("Health Score")
            
            # Bar chart for machine health
            if not health_df.empty:
                fig = px.bar(
                    health_df,
                    x="Machine",
                    y="Health Score",
                    title="Health Score by Machine",
                    color="Health Score",
                    color_continuous_scale=["red", "orange", "green"],
                    range_color=[0, 100]
                )
                
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Health Score",
                    yaxis=dict(range=[0, 100]),
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Health breakdown table
                with st.expander("Health Score Details", expanded=False):
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
                            "Machine": machine_name,
                            "Health Score": f"{health_score:.1f}",
                            "Total Maintenances": total_maint,
                            "Completed": completed_maint,
                            "Overdue": overdue_maint,
                            "Completion Rate": f"{(completed_maint / total_maint * 100):.1f}%" if total_maint > 0 else "N/A"
                        }
                        
                        health_details.append(detail)
                    
                    # Convert to DataFrame and display
                    health_details_df = pd.DataFrame(health_details)
                    st.dataframe(health_details_df)
            else:
                st.info("No machine health data available.")
            
            # Maintenance Type Analysis
            if maintenances:
                st.markdown("### Maintenance Type Analysis")
                
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
                        "Type": mtype,
                        "Count": data["count"],
                        "Completed": data["completed"],
                        "Completion Rate": data["completed"] / data["count"] if data["count"] > 0 else 0
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
                            x="Type",
                            y="Count",
                            title="Maintenance Count by Type",
                            color="Type"
                        )
                        
                        fig.update_layout(
                            xaxis_title="",
                            yaxis_title="Number of Maintenances",
                            height=350,
                            margin=dict(l=0, r=0, t=40, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Completion rate by type
                        fig = px.bar(
                            maint_type_df,
                            x="Type",
                            y="Completion Rate",
                            title="Completion Rate by Type",
                            color="Type",
                            text_auto='.0%'
                        )
                        
                        fig.update_layout(
                            xaxis_title="",
                            yaxis_title="Completion Rate",
                            yaxis=dict(tickformat='.0%'),
                            height=350,
                            margin=dict(l=0, r=0, t=40, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No maintenance type data available for analysis.")
        else:
            st.info("Insufficient data to calculate health scores. Add machines and maintenance records to see detailed analytics.")
        
        # Machine Utilization and Performance (admin only)
        if is_admin() and machines and companies:
            st.markdown("### Machine Utilization by Company")
            
            # Calculate machine counts by company
            company_machine_counts = {}
            for company in companies:
                company_id = company["id"]
                company_name = company["name"]
                company_machines = [m for m in machines if m["company_id"] == company_id]
                
                company_machine_counts[company_name] = len(company_machines)
            
            # Create DataFrame
            company_df = pd.DataFrame({
                "Company": list(company_machine_counts.keys()),
                "Machine Count": list(company_machine_counts.values())
            })
            
            # Sort by machine count (descending)
            company_df = company_df.sort_values("Machine Count", ascending=False)
            
            # Bar chart
            if not company_df.empty:
                fig = px.bar(
                    company_df,
                    x="Company",
                    y="Machine Count",
                    title="Machine Count by Company",
                    color="Machine Count",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Number of Machines",
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No company data available for analysis.")

def format_maintenance_date(date_str):
    """Format a date string as a more readable format"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    return date_obj.strftime("%d %b, %Y")