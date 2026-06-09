from pymongo import MongoClient
from datetime import datetime
import os

MONGO_URL = os.getenv(
"MONGO_URL",
"mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URL)

db = client["resumeranker"]

history_collection = db["ranking_history"]

def save_ranking(
candidate_name: str,
score: float,
skills: list,
job_description: str
):

```
history_collection.insert_one(
    {
        "candidate_name": candidate_name,
        "score": score,
        "skills": skills,
        "job_description": job_description,
        "timestamp": datetime.now()
    }
)
```

def get_history():

```
return list(
    history_collection.find(
        {},
        {"_id": 0}
    ).sort(
        "timestamp",
        -1
    )
)
```

