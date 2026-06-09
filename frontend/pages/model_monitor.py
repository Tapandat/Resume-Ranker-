import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
page_title="Model Monitor",
page_icon="🤖",
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

st.title("🤖 Model Monitor")

response = requests.get(
f"{API_BASE}/admin/model-monitor"
)

if response.status_code == 200:

```
data = response.json()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Resumes Analyzed",
        data["total_resumes"]
    )

with col2:
    st.metric(
        "Average Score",
        data["average_score"]
    )

with col3:
    st.metric(
        "Highest Score",
        data["highest_score"]
    )

with col4:
    st.metric(
        "Lowest Score",
        data["lowest_score"]
    )

st.markdown("---")

st.subheader("Top Skills")

skill_df = pd.DataFrame(
    list(data["top_skills"].items()),
    columns=[
        "Skill",
        "Frequency"
    ]
)

st.dataframe(
    skill_df,
    use_container_width=True
)
```

else:

```
st.error(
    "Unable to fetch model statistics."
)
```

st.markdown("---")

if st.button(
"⬅ Back to Admin Dashboard"
):
st.switch_page(
"pages/admin_dashboard.py"
)

