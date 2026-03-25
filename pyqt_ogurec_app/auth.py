from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class User:
    username: str
    display_name: str
    role: str
    can_add: bool
    can_edit: bool
    can_delete: bool

    @property
    def is_read_only(self) -> bool:
        return not any((self.can_add, self.can_edit, self.can_delete))


USERS = {
    "admin": {
        "password": "admin",
        "display_name": "Администратор",
        "role": "Администратор",
        "can_add": True,
        "can_edit": True,
        "can_delete": True,
    },
    "manager": {
        "password": "manager",
        "display_name": "Менеджер",
        "role": "Менеджер",
        "can_add": True,
        "can_edit": True,
        "can_delete": False,
    },
    "viewer": {
        "password": "viewer",
        "display_name": "Пользователь",
        "role": "Пользователь",
        "can_add": False,
        "can_edit": False,
        "can_delete": False,
    },
}


def authenticate(username: str, password: str) -> Optional[User]:
    normalized_username = username.strip().lower()
    normalized_password = password.strip()
    record = USERS.get(normalized_username)
    if not record or record["password"] != normalized_password:
        return None
    return User(
        username=normalized_username,
        display_name=record["display_name"],
        role=record["role"],
        can_add=record["can_add"],
        can_edit=record["can_edit"],
        can_delete=record["can_delete"],
    )

