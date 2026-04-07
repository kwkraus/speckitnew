from dataclasses import dataclass

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    display_name: str


def get_current_user(request: Request) -> CurrentUser:
    raw_user = getattr(request.state, "user", None)
    if raw_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Valid authentication token required."},
        )

    return CurrentUser(
        user_id=str(raw_user.get("user_id", "local-dev-user")),
        display_name=str(raw_user.get("display_name", "Local User")),
    )

