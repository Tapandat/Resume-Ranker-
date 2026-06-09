from pymongo import MongoClient
import os

MONGO_URL = os.getenv(
"MONGO_URL",
"mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URL)

db = client["resumeranker"]

users_collection = db["users"]

def get_analytics():

```
total_users = users_collection.count_documents({})

active_users = users_collection.count_documents(
    {
        "status": "active"
    }
)

blocked_users = users_collection.count_documents(
    {
        "status": "blocked"
    }
)

admin_users = users_collection.count_documents(
    {
        "role": "admin"
    }
)

local_users = users_collection.count_documents(
    {
        "provider": "local"
    }
)

google_users = users_collection.count_documents(
    {
        "provider": "google"
    }
)

return {
    "total_users": total_users,
    "active_users": active_users,
    "blocked_users": blocked_users,
    "admin_users": admin_users,
    "local_users": local_users,
    "google_users": google_users
}
```

