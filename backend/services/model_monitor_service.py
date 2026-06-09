from pymongo import MongoClient
from collections import Counter
import os

MONGO_URL = os.getenv(
"MONGO_URL",
"mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URL)

db = client["resumeranker"]

history_collection = db["ranking_history"]

def get_model_stats():

```
docs = list(
    history_collection.find(
        {},
        {"_id": 0}
    )
)

if len(docs) == 0:

    return {
        "total_resumes": 0,
        "average_score": 0,
        "highest_score": 0,
        "lowest_score": 0,
        "top_skills": {}
    }

scores = [
    d["score"]
    for d in docs
]

skill_counter = Counter()

for d in docs:
    skill_counter.update(
        d.get(
            "skills",
            []
        )
    )

return {
    "total_resumes": len(docs),
    "average_score": round(
        sum(scores) / len(scores),
        2
    ),
    "highest_score": round(
        max(scores),
        2
    ),
    "lowest_score": round(
        min(scores),
        2
    ),
    "top_skills": dict(
        skill_counter.most_common(10)
    )
}
```

