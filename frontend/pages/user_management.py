import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="User Management",
    page_icon="👥",
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
st.title("👥 User Management")
st.markdown("---")

# Temporary data
users = [
    {
        "Name": "Admin",
        "Email": "admin@gmail.com",
        "Role": "admin",
        "Status": "active"
    },
    {
        "Name": "John Doe",
        "Email": "john@gmail.com",
        "Role": "user",
        "Status": "active"
    },
    {
        "Name": "Alice",
        "Email": "alice@gmail.com",
        "Role": "user",
        "Status": "blocked"
    }
]

df = pd.DataFrame(users)

st.subheader("Registered Users")

st.dataframe(
    df,
    use_container_width=True
)

st.markdown("---")

st.subheader("Admin Actions")

selected_email = st.selectbox(
    "Select User",
    df["Email"]
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button(
        "⬆ Promote to Admin",
        use_container_width=True
    ):
        st.success(
            f"{selected_email} promoted to admin."
        )

with col2:
    if st.button(
        "🚫 Block User",
        use_container_width=True
    ):
        st.warning(
            f"{selected_email} blocked."
        )

with col3:
    if st.button(
        "✅ Unblock User",
        use_container_width=True
    ):
        st.success(
            f"{selected_email} unblocked."
        )

with col4:
    if st.button(
        "🗑 Delete User",
        use_container_width=True
    ):
        st.error(
            f"{selected_email} deleted."
        )

st.markdown("---")

if st.button("⬅ Back to Admin Dashboard"):
    st.switch_page("pages/admin_dashboard.py")
