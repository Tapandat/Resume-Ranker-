from fastapi import APIRouter

from backend.services.activity_logger import (
get_logs
)

from backend.services.user_service import (
get_all_users,
delete_user,
promote_user,
block_user,
unblock_user
)
from backend.services.analytics_service import (
    get_analytics
)

router = APIRouter(
prefix="/admin",
tags=["admin"]
)

@router.get("/logs")
def logs():
return get_logs()

@router.get("/users")
def users():
return get_all_users()

@router.get("/analytics")
def analytics():
return get_analytics()


@router.delete("/users/{email}")
def remove_user(email: str):
delete_user(email)

```
return {
    "message": "User deleted"
}
```

@router.put("/promote/{email}")
def promote(email: str):
promote_user(email)

```
return {
    "message": "User promoted"
}
```

@router.put("/block/{email}")
def block(email: str):
block_user(email)

```
return {
    "message": "User blocked"
}
```

@router.put("/unblock/{email}")
def unblock(email: str):
unblock_user(email)

```
return {
    "message": "User unblocked"
}
```
