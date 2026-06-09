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
page_title="Admin Dashboard",
page_icon="🛠️",
layout="wide"
)

# Authentication

if (
"token" not in st.session_state
or not st.session_state["token"]
):
st.switch_page("../login.py")

# Role check

if st.session_state.get("role") != "admin":
st.error("❌ Unauthorized access")
st.stop()

# Statistics

total_users = users_collection.count_documents({})

active_users = users_collection.count_documents(
{
"status": "active"
}
)

total_resumes = history_collection.count_documents({})

total_logs = logs_collection.count_documents({})

# Header

st.title("🛠️ Admin Portal")

st.success(
f"Welcome Admin {st.session_state['user']['name']}"
)

st.markdown("---")

# Metrics

col1, col2, col3, col4 = st.columns(4)

with col1:

```
st.metric(
    "Total Users",
    total_users
)
```

with col2:

```
st.metric(
    "Resumes Analyzed",
    total_resumes
)
```

with col3:

```
st.metric(
    "Activity Logs",
    total_logs
)
```

with col4:

```
st.metric(
    "Active Users",
    active_users
)
```

st.markdown("---")

st.subheader("Admin Actions")

# Row 1

col1, col2, col3 = st.columns(3)

with col1:

```
if st.button(
    "👥 User Management",
    use_container_width=True
):
    st.switch_page(
        "pages/user_management.py"
    )
```

with col2:

```
if st.button(
    "📊 Analytics",
    use_container_width=True
):
    st.switch_page(
        "pages/analytics.py"
    )
```

with col3:

```
if st.button(
    "📜 Activity Logs",
    use_container_width=True
):
    st.switch_page(
        "pages/activity_logs.py"
    )
```

# Row 2

col4, col5, col6 = st.columns(3)

with col4:

```
if st.button(
    "🤖 Model Monitor",
    use_container_width=True
):
    st.switch_page(
        "pages/model_monitor.py"
    )
```

with col5:

```
if st.button(
    "📜 Ranking History",
    use_container_width=True
):
    st.switch_page(
        "pages/ranking_history.py"
    )
```

with col6:

```
if st.button(
    "⚙ Settings",
    use_container_width=True
):
    st.switch_page(
        "pages/settings.py"
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
    "✅ MongoDB connection is healthy"
)
```

except Exception as e:

```
st.error(
    f"MongoDB connection failed: {e}"
)
```

st.markdown("---")

if st.button(
"🚪 Logout",
use_container_width=True
):

```
st.session_state.clear()

st.switch_page(
    "../login.py"
)
```
