"""
models.py — MongoDB database models for Orrbit user authentication.

Uses MongoDB Atlas via pymongo — no local database needed.
Collections are auto-created on first run.

Collections:
- users: stores user accounts
- sessions: stores active sessions
"""

import os
import uuid
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

# ── MongoDB connection ─────────────────────────────────────────────────────────

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL not set in .env file")

_client: MongoClient = None


def get_client() -> MongoClient:
    """Get or create MongoDB client (singleton)."""
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URL)
        print("[DB] Connected to MongoDB Atlas")
    return _client


def get_db():
    """Get the Orrbit database."""
    return get_client()["orrbit"]


def get_users_collection() -> Collection:
    """Get the users collection."""
    return get_db()["users"]


def get_sessions_collection() -> Collection:
    """Get the sessions collection."""
    return get_db()["sessions"]


# ── Database initialization ────────────────────────────────────────────────────

def init_db():
    """
    Initialize the database — create indexes for fast lookups.
    Called once when the server starts.
    """
    users = get_users_collection()

    # Ensure email and username are unique and indexed
    users.create_index([("email", ASCENDING)],    unique=True)
    users.create_index([("username", ASCENDING)], unique=True)

    print("[DB] MongoDB initialized — indexes created")


# ── User operations ────────────────────────────────────────────────────────────

def create_user(email: str, username: str, hashed_password: str) -> dict:
    """
    Create a new user in MongoDB.
    Returns the created user document.
    """
    user = {
        "_id":             str(uuid.uuid4()),
        "email":           email.lower().strip(),
        "username":        username.strip(),
        "hashed_password": hashed_password,
        "is_active":       True,
        "created_at":      datetime.utcnow().isoformat(),
        "last_login":      None,
    }
    get_users_collection().insert_one(user)
    print(f"[DB] Created user: {email}")
    return user


def get_user_by_email(email: str) -> dict | None:
    """Find a user by email address."""
    return get_users_collection().find_one({"email": email.lower().strip()})


def get_user_by_id(user_id: str) -> dict | None:
    """Find a user by their unique ID."""
    return get_users_collection().find_one({"_id": user_id})


def get_user_by_username(username: str) -> dict | None:
    """Find a user by username."""
    return get_users_collection().find_one({"username": username.strip()})


def update_last_login(user_id: str):
    """Update the last login timestamp for a user."""
    get_users_collection().update_one(
        {"_id": user_id},
        {"$set": {"last_login": datetime.utcnow().isoformat()}}
    )


def email_exists(email: str) -> bool:
    """Check if an email is already registered."""
    return get_users_collection().find_one({"email": email.lower()}) is not None


def username_exists(username: str) -> bool:
    """Check if a username is already taken."""
    return get_users_collection().find_one({"username": username}) is not None