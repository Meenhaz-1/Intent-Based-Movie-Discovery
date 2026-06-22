"""Profile management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

import db_migration
from main import app_state

router = APIRouter()


class ProfileCreate(BaseModel):
    user_id: str
    profile_name: str


class ProfileUpdate(BaseModel):
    profile_name: str


class ProfileResponse(BaseModel):
    profile_id: str
    profile_name: str
    like_count: int
    is_default: bool
    created_at: str


@router.get("/{user_id}")
async def get_user_profiles(user_id: str) -> List[ProfileResponse]:
    """Get all profiles for a user."""
    try:
        profiles = db_migration.get_user_profiles(app_state.conn, user_id)
        return [
            ProfileResponse(
                profile_id=p["profile_id"],
                profile_name=p["profile_name"],
                like_count=p["like_count"],
                is_default=p["is_default"],
                created_at=p["created_at"]
            )
            for p in profiles
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_profile(payload: ProfileCreate) -> dict:
    """Create a new profile."""
    try:
        profile_id = db_migration.create_profile(
            app_state.conn,
            payload.user_id,
            payload.profile_name
        )
        return {
            "profile_id": profile_id,
            "message": f"Profile '{payload.profile_name}' created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{profile_id}")
async def update_profile(profile_id: str, payload: ProfileUpdate) -> dict:
    """Rename a profile."""
    try:
        db_migration.rename_profile(app_state.conn, profile_id, payload.profile_name)
        return {"message": f"Profile renamed to '{payload.profile_name}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str) -> dict:
    """Delete a profile."""
    try:
        db_migration.delete_profile(app_state.conn, profile_id)
        return {"message": "Profile deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/{profile_id}/set-default")
async def set_default_profile(user_id: str, profile_id: str) -> dict:
    """Set a profile as default."""
    try:
        db_migration.set_default_profile(app_state.conn, user_id, profile_id)
        return {"message": "Profile set as default"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{profile_id}/default")
async def get_default_profile(user_id: str) -> dict:
    """Get the default profile for a user."""
    try:
        profile_id = db_migration.get_default_profile(app_state.conn, user_id)
        if not profile_id:
            raise HTTPException(status_code=404, detail="No profiles found for user")
        return {"profile_id": profile_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
