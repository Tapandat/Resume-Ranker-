from pymongo import MongoClient
from datetime import datetime
import os

MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URL)

db = client["resumeranker"]

logs_collection = db["activity_logs"]


def log_activity(
    user_email: str,
    action: str
):
    logs_collection.insert_one(
        {
            "user": user_email,
            "action": action,
            "timestamp": datetime.now()
        }
    )


def get_logs():

    return list(
        logs_collection.find(
            {},
            {"_id": 0}
        ).sort(
            "timestamp",
            -1
        )
    )
