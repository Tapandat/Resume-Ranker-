import streamlit as st
import pandas as pd
from pymongo import MongoClient
import os

MONGO_URL = os.getenv(
"MONGO_URL",
"mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URL)

db = client["resumeranker"]

history_collection = db["ranking_history"]

st.set_page_config(
page_title="Ranking History",
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

st.title("📜 Ranking History")

history = list(
history_collection.find(
{},
{"_id": 0}
).sort(
"timestamp",
-1
)
)

if history:

```
df = pd.DataFrame(history)

st.dataframe(
    df,
    use_container_width=True
)
```

else:

```
st.info(
    "No ranking history available."
)
```

st.markdown("---")

if st.button(
"⬅ Back to Admin Dashboard"
):
st.switch_page(
"pages/admin_dashboard.py"
)

