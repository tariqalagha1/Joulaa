from fastapi import HTTPException


def ensure_org_access(resource_org_id, user_org_id):
    if resource_org_id != user_org_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied for this organization"
        )
