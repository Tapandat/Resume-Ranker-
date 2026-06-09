import streamlit as st
from pymongo import MongoClient
import os

MONGO_URL = os.getenv(
"MONGO_URL",
"mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URL)

db = client["resumeranker"]

users_collection = db["users"]
logs_collection = db["activity_logs"]
history_collection = db["ranking_history"]

st.set_page_config(
page_title="Settings",
page_icon="⚙️",
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

st.title("⚙️ Settings")

st.markdown("---")

st.subheader("System Information")

col1, col2, col3 = st.columns(3)

with col1:
st.metric(
"Total Users",
users_collection.count_documents({})
)

with col2:
st.metric(
"Total Logs",
logs_collection.count_documents({})
)

with col3:
st.metric(
"Total Resume Analyses",
history_collection.count_documents({})
)

st.markdown("---")

st.subheader("Maintenance")

col1, col2 = st.columns(2)

with col1:

```
if st.button(
    "🗑 Clear Activity Logs",
    use_container_width=True
):

    logs_collection.delete_many({})

    st.success(
        "Activity logs cleared successfully."
    )
```

with col2:

```
if st.button(
    "♻ Reset Ranking History",
    use_container_width=True
):

    history_collection.delete_many({})

    st.success(
        "Ranking history reset successfully."
    )
```

st.markdown("---")

st.subheader("Database Status")

try:

```
client.admin.command(
    "ping"
)

st.success(
    "MongoDB connection is healthy."
)
```

except Exception as e:

```
st.error(
    f"MongoDB error: {e}"
)
```

st.markdown("---")

if st.button(
"⬅ Back to Admin Dashboard"
):

```
st.switch_page(
    "pages/admin_dashboard.py"
)
```

