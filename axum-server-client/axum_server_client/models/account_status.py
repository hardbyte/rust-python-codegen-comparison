from enum import Enum


class AccountStatus(str, Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"

    def __str__(self) -> str:
        return str(self.value)
