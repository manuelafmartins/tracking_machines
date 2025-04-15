
# frontend/pages/maintenances.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ..utils.api import get_api_data, post_api_data, put_api_data
from ..utils.ui import is_admin, show_delete_button

def show_maintenances():
    st.title("Maintenance Scheduling")
    
    # Fetch data based on user role
    if is_admin():
        companies = get_api_data("companies") or []
        # Fetch all machines initially
        all_machines = get_api_data("machines") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            companies = [get_api_data(f"companies/{company_id}")] if get_api_data(f"companies/{company_id}") else []
            all_machines = get_api_data(f"machines/company/{company_id}") or []
        else:
            companies = []
            all_machines = []
    
    # Create a dictionary to quickly look up company names
    company_dict = {c["id"]: c["name"] for c in companies}
    
    # Create a form to schedule new maintenance
    with st.form("new_maintenance"):
        st.subheader("Schedule New Maintenance")
        
        # Company filter (admin only)
        if is_admin() and companies:
            company_options = [c["id"] for c in companies]
            company_labels = [c["name"] for c in companies]
            
            selected_company_idx = st.selectbox(
                "Filter by Company",
                options=range(len(company_options)),
                format_func=lambda idx: company_labels[idx],
                key="company_filter"
            )
            selected_company_id = company_options[selected_company_idx]
            
            # Filter machines by selected company
            machines = [m for m in all_machines if m["company_id"] == selected_company_id]
        else:
            # Fleet managers see only their company's machines
            machines = all_machines
        
        # Let user pick a machine
        if machines:
            machine_options = [m["id"] for m in machines]
            machine_labels = [f"{m['name']} ({m['type']})" for m in machines]
            
            selected_machine_idx = st.selectbox(
                "Machine",
                options=range(len(machine_options)),
                format_func=lambda idx: machine_labels[idx]
            )
            chosen_machine_id = machine_options[selected_machine_idx]
        else:
            st.warning("No machines available. Please add a machine first.")
            chosen_machine_id = None
        
        # Types of maintenance
        maintenance_type = st.selectbox(
            "Maintenance Type",
            ["Oil Change", "Full Review", "Filters", "Tires", "Other"]
        )
        
        final_type = maintenance_type
        if maintenance_type == "Other":
            user_type = st.text_input("Specify the maintenance type")
            if user_type:
                final_type = user_type
        
        # Date selection
        scheduled_date = st.date_input(
            "Scheduled Date",
            min_value=datetime.now().date(),
            value=datetime.now().date() + timedelta(days=7)
        )
        
        # Optional notes
        notes = st.text_area("Notes (Optional)")
        
        submitted = st.form_submit_button("Schedule")
        
        if submitted and chosen_machine_id:
            # According to MaintenanceCreate, we send: {"machine_id", "type", "scheduled_date", "notes"}
            data = {
                "machine_id": chosen_machine_id,
                "type": final_type,
                "scheduled_date": scheduled_date.isoformat()
            }
            if notes:
                data["notes"] = notes
                
            if post_api_data("maintenances", data):
                st.success(f"Maintenance scheduled on {scheduled_date}!")
                st.rerun()
    
    st.subheader("Scheduled Maintenances")
    
    # Fetch maintenances based on user role
    if is_admin():
        maintenances = get_api_data("maintenances") or []
    else:
        company_id = st.session_state.get("company_id")
        if company_id:
            maintenances = get_api_data(f"maintenances/company/{company_id}") or []
        else:
            maintenances = []
    
    if maintenances:
        # Add machine name for better display
        for m in maintenances:
            machine = next((mac for mac in all_machines if mac["id"] == m["machine_id"]), None)
            if machine:
                m["machine_name"] = machine["name"]
                m["machine_type"] = machine["type"]
                
                # Add company name
                company_id = machine.get("company_id")
                if company_id in company_dict:
                    m["company_name"] = company_dict[company_id]
        
        # Convert to DataFrame for display
        df_maint = pd.DataFrame(maintenances)
        
        # Convert "scheduled_date" to datetime
        if "scheduled_date" in df_maint.columns:
            df_maint["scheduled_date"] = pd.to_datetime(df_maint["scheduled_date"])
        
        # Sort by date
        if "scheduled_date" in df_maint.columns:
            df_maint = df_maint.sort_values("scheduled_date")
        
        # Simple highlight for overdue / soon
        today = datetime.now().date()
        
        # Display maintenances in tabs: Pending and Completed
        tab1, tab2 = st.tabs(["Pending", "Completed"])
        
        with tab1:
            # Filter for pending maintenances
            pending = df_maint[df_maint["completed"] == False] if "completed" in df_maint.columns else df_maint
            
            if not pending.empty:
                for idx, maint in pending.iterrows():
                    # Determine urgency for color coding
                    date_val = maint["scheduled_date"].date() if "scheduled_date" in maint else today
                    days_remaining = (date_val - today).days
                    
                    if days_remaining <= 0:
                        status = "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¯Ã‚Â¿Ã‚Â½ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â´ Overdue"
                    elif days_remaining <= 2:
                        status = "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  Urgent"
                    elif days_remaining <= 7:
                        status = "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ Soon"
                    else:
                        status = "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ Scheduled"
                    
                    # Create an expander with maintenance details
                    with st.expander(f"{status} - {maint.get('type', 'Maintenance')} on {maint.get('machine_name', 'Unknown Machine')} ({date_val})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**Machine:** {maint.get('machine_name', 'Unknown')}")
                            st.write(f"**Company:** {maint.get('company_name', 'Unknown')}")
                            st.write(f"**Type:** {maint.get('type', 'Unknown')}")
                            st.write(f"**Scheduled Date:** {date_val}")
                            
                            if "notes" in maint and maint["notes"]:
                                st.write(f"**Notes:** {maint['notes']}")
                        
                        with col2:
                            # Mark as completed button
                            if st.button("Mark Completed", key=f"complete_{maint['id']}"):
                                if put_api_data(f"maintenances/{maint['id']}", {"completed": True}):
                                    st.success("Maintenance marked as completed!")
                                    st.rerun()
                            
                            # Edit button
                            if st.button("Edit", key=f"edit_maint_{maint['id']}"):
                                st.session_state["edit_maint_id"] = maint["id"]
                                st.session_state["edit_maint_type"] = maint["type"]
                                st.session_state["edit_maint_date"] = maint["scheduled_date"]
                                st.session_state["edit_maint_notes"] = maint.get("notes", "")
                            
                            # Delete button
                            show_delete_button("maintenance", maint["id"])
                    
                    # Edit form appears if this maintenance is being edited
                    if st.session_state.get("edit_maint_id") == maint["id"]:
                        with st.form(f"edit_maint_{maint['id']}"):
                            st.subheader(f"Edit Maintenance")
                            
                            edit_type = st.text_input("Maintenance Type", value=st.session_state["edit_maint_type"])
                            
                            edit_date = st.date_input(
                                "Scheduled Date",
                                value=st.session_state["edit_maint_date"].date() 
                                    if isinstance(st.session_state["edit_maint_date"], datetime) 
                                    else datetime.strptime(st.session_state["edit_maint_date"], "%Y-%m-%d").date(),
                                min_value=datetime.now().date()
                            )
                            
                            edit_notes = st.text_area("Notes", value=st.session_state["edit_maint_notes"])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                submit_edit = st.form_submit_button("Save Changes")
                            with col2:
                                cancel_edit = st.form_submit_button("Cancel")
                            
                            if submit_edit and edit_type:
                                update_data = {
                                    "type": edit_type,
                                    "scheduled_date": edit_date.isoformat(),
                                    "notes": edit_notes
                                }
                                
                                if put_api_data(f"maintenances/{maint['id']}", update_data):
                                    st.success("Maintenance updated successfully!")
                                    # Clear edit state
                                    if "edit_maint_id" in st.session_state:
                                        del st.session_state["edit_maint_id"]
                                    st.rerun()
                            
                            if cancel_edit:
                                # Clear edit state
                                if "edit_maint_id" in st.session_state:
                                    del st.session_state["edit_maint_id"]
                                st.rerun()
            else:
                st.info("No pending maintenances.")
        
        with tab2:
            # Filter for completed maintenances
            completed = df_maint[df_maint["completed"] == True] if "completed" in df_maint.columns else pd.DataFrame()
            
            if not completed.empty:
                st.dataframe(completed[["scheduled_date", "type", "machine_name", "company_name"]])
            else:
                st.info("No completed maintenances.")
    else:
        st.info("No maintenances scheduled.")