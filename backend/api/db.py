# db.py
import os
from pymongo import MongoClient
import redis

# ---------- MongoDB ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "face_swap")

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
jobs_collection = mongo_db["jobs"]

# ---------- Redis ----------
REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
