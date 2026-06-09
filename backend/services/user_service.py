from pymongo import MongoClient
from backend.services.activity_logger import log_activity
import os

MONGO_URL = os.getenv(
"MONGO_URL",
"mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URL)

db = client["resumeranker"]

users_collection = db["users"]

def get_all_users():
return list(
users_collection.find(
{},
{"_id": 0, "password": 0}
)
)

def delete_user(email: str):

```
users_collection.delete_one(
    {"email": email}
)

log_activity(
    email,
    "Deleted User"
)
```

def promote_user(email: str):

```
users_collection.update_one(
    {"email": email},
    {
        "$set": {
            "role": "admin"
        }
    }
)

log_activity(
    email,
    "Promoted to Admin"
)
```

def block_user(email: str):

```
users_collection.update_one(
    {"email": email},
    {
        "$set": {
            "status": "blocked"
        }
    }
)

log_activity(
    email,
    "Blocked User"
)
```

def unblock_user(email: str):

```
users_collection.update_one(
    {"email": email},
    {
        "$set": {
            "status": "active"
        }
    }
)

log_activity(
    email,
    "Unblocked User"
)
```
