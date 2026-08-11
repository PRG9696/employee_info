import sqlite3
import os
import pandas as pd
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
logo_icon = "📋"
for possible_name in ["logo.png", "logo.PNG", "logo.jpg", "logo.jpeg", "logo.webp"]:
    if os.path.exists(possible_name):
        logo_icon = possible_name
        break

st.set_page_config(page_title="Employee Info Update", page_icon=logo_icon, layout="wide")

# ==========================================
# 2. HIDE ALL STREAMLIT UI, BADGES & TOOLBARS
# ==========================================
hide_st_style = """
    <style>
    /* Hide top header, main menu, decoration line, and toolbar */
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}

    /* Hide standard footer, status widgets, and deploy buttons */
    footer {visibility: hidden !important;}
    [data-testid="stFooter"] {display: none !important;}
    .stDeployButton {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}

    /* Hide Streamlit Cloud viewer badges, profile tag, and bottom floating overlays */
    [data-testid="stBottomFloatingContainer"] {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    div[class*="stAppViewer"] {display: none !important;}
    div[class*="Profile"] {display: none !important;}
    button[title="View profile"] {display: none !important;}
    a[href*="streamlit.io/user"] {display: none !important;}
    iframe[title="streamlit_app"] {height: 100vh !important;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)


# ==========================================
# 3. DATABASE SETUP
# ==========================================
def get_connection():
    return sqlite3.connect("employee_records.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            school_dept TEXT NOT NULL,
            vehicles TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ==========================================
# 4. POP-UP CONFIRMATION DIALOG
# ==========================================
@st.dialog("✅ Information Updated!")
def show_confirmation_popup(name, email, vehicles):
    st.write(f"Thank you, **{name}**!")
    st.write("Your employee details have been successfully recorded.")
    st.info(f"📧 **Email:** {email}\n\n🚘 **Registered Vehicles:** {vehicles}")
    
    if st.button("Done", type="primary", use_container_width=True):
        for key in ["input_name", "input_email", "input_phone", "input_school"]:
            if key in st.session_state:
                st.session_state[key] = ""
        st.session_state.num_vehicles = 1
        st.rerun()


# ==========================================
# 5. HEADER SECTION (LOGO + TITLE)
# ==========================================
logo_file = None
for possible_name in ["logo.png", "logo.PNG", "logo.jpg", "logo.jpeg", "logo.webp"]:
    if os.path.exists(possible_name):
        logo_file = possible_name
        break

if logo_file:
    col_logo, col_title = st.columns([1, 6], vertical_alignment="center")
    with col_logo:
        st.image(logo_file, width=90)
    with col_title:
        st.title("Employee Information Update")
else:
    st.title("Employee Information Update")

st.caption("Please fill in your latest details below to update your records.")


# ==========================================
# 6. SIDEBAR ADMIN AUTHENTICATION
# ==========================================
st.sidebar.header("🔐 Admin Access")
admin_password = st.sidebar.text_input("Enter Admin Password", type="password")
correct_password = st.secrets.get("ADMIN_PASSWORD", "Chan@2606")
is_admin = (admin_password == correct_password)

if admin_password and not is_admin:
    st.sidebar.error("Incorrect Password")

if is_admin:
    tab_form, tab_admin = st.tabs(["📝 Employee Form", "📊 Admin Records"])
else:
    tab_form = st.container()
    tab_admin = None


# ==========================================
# 7. EMPLOYEE FORM TAB
# ==========================================
with tab_form:
    st.subheader("Employee Details")

    full_name = st.text_input("1. Full Name*", key="input_name")
    email = st.text_input("2. Company Email Address*", key="input_email")
    phone = st.text_input("3. Phone Number*", key="input_phone")
    school_dept = st.text_input("4. School or Department*", key="input_school")

    # Multiple Vehicles Input (Capped at 5)
    st.write("5. Vehicle Number(s)* (Maximum 5)")
    if "num_vehicles" not in st.session_state:
        st.session_state.num_vehicles = 1

    vehicle_list = []
    for i in range(st.session_state.num_vehicles):
        col_v, col_btn = st.columns([5, 1], vertical_alignment="bottom")
        with col_v:
            v_num = st.text_input(f"Vehicle #{i+1}*", key=f"veh_{i}", placeholder="e.g. JQA 1234")
            vehicle_list.append(v_num)
        with col_btn:
            if i > 0 and i == st.session_state.num_vehicles - 1:
                if st.button("❌ Remove", key=f"remove_{i}"):
                    st.session_state.num_vehicles -= 1
                    st.rerun()

    if st.session_state.num_vehicles < 5:
        if st.button("➕ Add Another Vehicle"):
            st.session_state.num_vehicles += 1
            st.rerun()
    else:
        st.caption("⚠️ Maximum limit of 5 vehicles reached.")

    st.markdown("---")

    if st.button("Submit Information", type="primary", use_container_width=True):
        valid_vehicles = [v.strip().upper() for v in vehicle_list if v.strip()]
        
        missing_fields = False
        if not full_name.strip() or not email.strip() or not phone.strip() or not school_dept.strip():
            missing_fields = True
        if len(valid_vehicles) == 0:
            missing_fields = True

        if missing_fields:
            st.error("⚠️ All fields marked with * are mandatory. Please complete all fields.")
        else:
            vehicles_str = ", ".join(valid_vehicles)
            
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO employee_info (full_name, email, phone, school_dept, vehicles)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(email) DO UPDATE SET
                        full_name = excluded.full_name,
                        phone = excluded.phone,
                        school_dept = excluded.school_dept,
                        vehicles = excluded.vehicles,
                        updated_at = CURRENT_TIMESTAMP
                """, (full_name.strip(), email.strip().lower(), phone.strip(), school_dept.strip(), vehicles_str))

                conn.commit()
                conn.close()

                show_confirmation_popup(full_name.strip(), email.strip().lower(), vehicles_str)

            except Exception as e:
                st.error(f"An error occurred while saving: {e}")
                conn.close()


# ==========================================
# 8. ADMIN DASHBOARD TAB
# ==========================================
if is_admin and tab_admin is not None:
    with tab_admin:
        st.header("📊 Submitted Employee Records")
        st.success("Admin Access Granted")

        conn = get_connection()
        query = """
            SELECT 
                id AS 'ID',
                full_name AS 'Full Name',
                email AS 'Company Email',
                phone AS 'Phone Number',
                school_dept AS 'School/Dept',
                vehicles AS 'Vehicle Number(s)',
                updated_at AS 'Last Updated'
            FROM employee_info
            ORDER BY updated_at DESC
        """
        df_employees = pd.read_sql_query(query, conn)
        conn.close()

        if df_employees.empty:
            st.info("No employee records found in the system yet.")
        else:
            st.dataframe(df_employees, use_container_width=True)

            csv_data = df_employees.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Employee List to CSV",
                data=csv_data,
                file_name="employee_info_export.csv",
                mime="text/csv",
            )
