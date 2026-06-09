import streamlit as st

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# Authentication check
if "token" not in st.session_state or not st.session_state.get("token"):
    st.switch_page("../login.py")

# Role check
if st.session_state.get("role") != "admin":
    st.error("❌ Unauthorized access")
    st.stop()

# Header
st.title("🛠️ Admin Portal")
st.markdown("---")

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Users", 0)

with col2:
    st.metric("Total Resumes", 0)

with col3:
    st.metric("Rankings Generated", 0)

with col4:
    st.metric("Active Users", 0)

st.markdown("---")

st.subheader("Admin Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "👥 User Management",
        use_container_width=True
    ):
        st.switch_page("pages/user_management.py")

with col2:
    if st.button(
        "📊 Analytics",
        use_container_width=True
    ):
        st.switch_page("pages/analytics.py")

with col3:
    if st.button(
        "📜 Activity Logs",
        use_container_width=True
    ):
        st.switch_page("pages/activity_logs.py")

with col4:
    if st.button(
        "🤖 Model Monitor",
        use_container_width=True
    ):
        st.switch_page(
            "pages/model_monitor.py"
        )

st.markdown("---")

st.success(
    f"Welcome Admin {st.session_state['user']['name']}"
)
