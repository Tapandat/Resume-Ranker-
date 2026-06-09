import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
page_title="Analytics",
page_icon="📊",
layout="wide"
)

if (
"token" not in st.session_state
or not st.session_state["token"]
):
st.switch_page("../login.py")

if st.session_state.get("role") != "admin":
st.error("Unauthorized access")
st.stop()

st.title("📊 Analytics Dashboard")

response = requests.get(
f"{API_BASE}/admin/analytics"
)

if response.status_code == 200:

```
data = response.json()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Users",
        data["total_users"]
    )

    st.metric(
        "Active Users",
        data["active_users"]
    )

with col2:
    st.metric(
        "Blocked Users",
        data["blocked_users"]
    )

    st.metric(
        "Admin Users",
        data["admin_users"]
    )

with col3:
    st.metric(
        "Google Users",
        data["google_users"]
    )

    st.metric(
        "Local Users",
        data["local_users"]
    )
```

else:

```
st.error(
    "Unable to fetch analytics."
)
```

st.markdown("---")

if st.button(
"⬅ Back to Admin Dashboard"
):
st.switch_page(
"pages/admin_dashboard.py"
)

