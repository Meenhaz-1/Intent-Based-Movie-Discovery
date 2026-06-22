"""Multi-profile database schema and migration utilities."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def create_multi_profile_schema(conn: sqlite3.Connection) -> None:
    """Create the new multi-profile schema."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS profiles (
            profile_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            profile_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_default BOOLEAN DEFAULT FALSE,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, profile_name)
        );

        CREATE TABLE IF NOT EXISTS profile_likes (
            profile_id TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rating REAL,
            review_text TEXT,
            PRIMARY KEY (profile_id, movie_id),
            FOREIGN KEY (profile_id) REFERENCES profiles(profile_id)
        );

        CREATE TABLE IF NOT EXISTS collab_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            profile_ids TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS cached_recommendations (
            cache_key TEXT PRIMARY KEY,
            profile_ids TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
    """)
    conn.commit()


def migrate_single_user_to_multi_profile(conn: sqlite3.Connection) -> Dict[str, int]:
    """
    Migrate existing single-user data to multi-profile schema.

    Returns a dict with migration stats:
        - users_created: number of new users
        - profiles_created: number of new default profiles
        - likes_migrated: total likes transferred
    """
    # First, ensure new schema exists
    create_multi_profile_schema(conn)

    # Get all unique user_ids from old user_likes table
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM user_likes ORDER BY user_id")
    old_user_ids = [row[0] for row in cursor.fetchall()]

    if not old_user_ids:
        return {"users_created": 0, "profiles_created": 0, "likes_migrated": 0}

    stats = {"users_created": 0, "profiles_created": 0, "likes_migrated": 0}

    for old_user_id in old_user_ids:
        # Create user entry if it doesn't exist
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, created_at, last_active) VALUES (?, ?, ?)",
            (old_user_id, datetime.now(), datetime.now()),
        )
        stats["users_created"] += 1

        # Create a default profile for this user
        default_profile_id = f"{old_user_id}_default"
        try:
            conn.execute(
                """INSERT INTO profiles (profile_id, user_id, profile_name, created_at, is_default)
                   VALUES (?, ?, ?, ?, ?)""",
                (default_profile_id, old_user_id, "Default Profile", datetime.now(), True),
            )
            stats["profiles_created"] += 1
        except sqlite3.IntegrityError:
            # Profile already exists, skip
            pass

        # Migrate all likes from user_likes to profile_likes
        cursor.execute(
            "SELECT movie_id, liked_at, review_text FROM user_likes WHERE user_id = ?",
            (old_user_id,),
        )
        likes = cursor.fetchall()

        for movie_id, liked_at, review_text in likes:
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO profile_likes (profile_id, movie_id, liked_at, review_text)
                       VALUES (?, ?, ?, ?)""",
                    (default_profile_id, movie_id, liked_at, review_text),
                )
                stats["likes_migrated"] += 1
            except sqlite3.Error:
                # Skip duplicates or errors
                pass

    conn.commit()
    return stats


def init_database(db_path: Path) -> sqlite3.Connection:
    """
    Initialize the database with proper schema.

    If the old single-user schema exists, migrates it automatically.
    Returns the database connection.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    # Check if old schema exists
    if table_exists(conn, "user_likes") and not table_exists(conn, "profiles"):
        # Run migration
        migrate_single_user_to_multi_profile(conn)
        # Optionally rename old table as backup
        try:
            conn.execute("ALTER TABLE user_likes RENAME TO user_likes_legacy")
            conn.commit()
        except sqlite3.Error:
            pass
    else:
        # Create new schema from scratch
        create_multi_profile_schema(conn)

    return conn


# ============================================================================
# Profile CRUD Operations
# ============================================================================


def create_profile(conn: sqlite3.Connection, user_id: str, profile_name: str) -> str:
    """
    Create a new profile for a user.

    Args:
        conn: Database connection
        user_id: User ID
        profile_name: Display name for the profile (e.g., "My Profile", "Partner")

    Returns:
        profile_id (generated as user_id_sanitized_name_timestamp)

    Raises:
        sqlite3.IntegrityError: If profile name already exists for this user
    """
    # Ensure user exists
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, created_at, last_active) VALUES (?, ?, ?)",
        (user_id, datetime.now(), datetime.now()),
    )

    # Generate profile ID (sanitize name for URL-safety)
    sanitized_name = profile_name.lower().replace(" ", "_")[:20]
    timestamp = int(datetime.now().timestamp())
    profile_id = f"{user_id}_{sanitized_name}_{timestamp}"

    conn.execute(
        """INSERT INTO profiles (profile_id, user_id, profile_name, created_at, is_default)
           VALUES (?, ?, ?, ?, ?)""",
        (profile_id, user_id, profile_name, datetime.now(), False),
    )
    conn.commit()
    return profile_id


def get_user_profiles(conn: sqlite3.Connection, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all profiles for a user, ordered by default first then by creation date.

    Returns a list of dicts:
        {
            "profile_id": str,
            "profile_name": str,
            "created_at": str,
            "is_default": bool,
            "like_count": int
        }
    """
    cursor = conn.cursor()
    cursor.execute(
        """SELECT p.profile_id, p.profile_name, p.created_at, p.is_default, COUNT(pl.movie_id) as like_count
           FROM profiles p
           LEFT JOIN profile_likes pl ON p.profile_id = pl.profile_id
           WHERE p.user_id = ?
           GROUP BY p.profile_id
           ORDER BY p.is_default DESC, p.created_at""",
        (user_id,),
    )
    return [
        {
            "profile_id": row[0],
            "profile_name": row[1],
            "created_at": row[2],
            "is_default": bool(row[3]),
            "like_count": row[4],
        }
        for row in cursor.fetchall()
    ]


def get_profile_likes(conn: sqlite3.Connection, profile_id: str) -> List[int]:
    """Get all liked movie IDs for a profile."""
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id FROM profile_likes WHERE profile_id = ? ORDER BY liked_at DESC", (profile_id,))
    return [row[0] for row in cursor.fetchall()]


def add_movie_to_profile(
    conn: sqlite3.Connection,
    profile_id: str,
    movie_id: int,
    rating: Optional[float] = None,
    review_text: Optional[str] = None,
) -> None:
    """Add a movie like (with optional rating and review) to a profile."""
    conn.execute(
        """INSERT OR REPLACE INTO profile_likes (profile_id, movie_id, liked_at, rating, review_text)
           VALUES (?, ?, ?, ?, ?)""",
        (profile_id, movie_id, datetime.now(), rating, review_text),
    )
    conn.commit()


def remove_movie_from_profile(conn: sqlite3.Connection, profile_id: str, movie_id: int) -> None:
    """Remove a movie like from a profile."""
    conn.execute("DELETE FROM profile_likes WHERE profile_id = ? AND movie_id = ?", (profile_id, movie_id))
    conn.commit()


def delete_profile(conn: sqlite3.Connection, profile_id: str) -> None:
    """
    Delete a profile and all its likes.

    Note: Cannot delete the last/only profile of a user.
    """
    cursor = conn.cursor()

    # Get user_id for this profile
    cursor.execute("SELECT user_id FROM profiles WHERE profile_id = ?", (profile_id,))
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Profile {profile_id} not found")

    user_id = result[0]

    # Check if this is the only profile for the user
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE user_id = ?", (user_id,))
    profile_count = cursor.fetchone()[0]

    if profile_count <= 1:
        raise ValueError("Cannot delete the only profile for a user. Create another profile first.")

    # Delete likes first (foreign key constraint)
    conn.execute("DELETE FROM profile_likes WHERE profile_id = ?", (profile_id,))

    # Delete profile
    conn.execute("DELETE FROM profiles WHERE profile_id = ?", (profile_id,))
    conn.commit()


def rename_profile(conn: sqlite3.Connection, profile_id: str, new_name: str) -> None:
    """Rename a profile."""
    conn.execute("UPDATE profiles SET profile_name = ? WHERE profile_id = ?", (new_name, profile_id))
    conn.commit()


def set_default_profile(conn: sqlite3.Connection, user_id: str, profile_id: str) -> None:
    """Set a profile as the default for a user."""
    # First, unset all other default profiles for this user
    conn.execute("UPDATE profiles SET is_default = 0 WHERE user_id = ?", (user_id,))

    # Then set the specified profile as default
    conn.execute("UPDATE profiles SET is_default = 1 WHERE profile_id = ? AND user_id = ?", (profile_id, user_id))
    conn.commit()


def get_default_profile(conn: sqlite3.Connection, user_id: str) -> Optional[str]:
    """Get the default profile ID for a user, or None if user has no profiles."""
    cursor = conn.cursor()
    cursor.execute("SELECT profile_id FROM profiles WHERE user_id = ? AND is_default = 1 LIMIT 1", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]

    # If no default, return the first profile (by creation date)
    cursor.execute("SELECT profile_id FROM profiles WHERE user_id = ? ORDER BY created_at LIMIT 1", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def clear_profile_likes(conn: sqlite3.Connection, profile_id: str) -> None:
    """Clear all likes from a profile."""
    conn.execute("DELETE FROM profile_likes WHERE profile_id = ?", (profile_id,))
    conn.commit()
