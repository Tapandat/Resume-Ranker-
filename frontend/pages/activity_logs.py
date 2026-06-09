import streamlit as st
import pandas as pd
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
page_title="Activity Logs",
page_icon="📜",
layout="wide"
)

# Authentication

if (
"token" not in st.session_state
or not st.session_state["token"]
):
st.switch_page("../login.py")

# Admin check

if st.session_state.get("role") != "admin":
st.error("❌ Unauthorized access")
st.stop()

st.title("📜 Activity Logs")

try:

```
response = requests.get(
    f"{API_BASE}/admin/logs"
)

if response.status_code == 200:

    logs = response.json()

    if len(logs) > 0:

        df = pd.DataFrame(logs)

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.info(
            "No activity logs found."
        )

else:

    st.error(
        "Failed to fetch logs."
    )
```

except Exception as e:

```
st.error(
    f"Error: {e}"
)
```

st.markdown("---")

if st.button(
"⬅ Back to Admin Dashboard"
):
st.switch_page(
"pages/admin_dashboard.py"
)

