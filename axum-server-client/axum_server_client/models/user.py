import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.account_status import AccountStatus
from ..models.role import Role
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.preferences import Preferences


T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """
    Attributes:
        active (bool):
        created_at (datetime.datetime):
        email (str):
        id (int):
        status (AccountStatus):
        username (str):
        preferences (Union['Preferences', None, Unset]):
        roles (Union[Unset, list[Role]]):
    """

    active: bool
    created_at: datetime.datetime
    email: str
    id: int
    status: AccountStatus
    username: str
    preferences: Union["Preferences", None, Unset] = UNSET
    roles: Union[Unset, list[Role]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.preferences import Preferences

        active = self.active

        created_at = self.created_at.isoformat()

        email = self.email

        id = self.id

        status = self.status.value

        username = self.username

        preferences: Union[None, Unset, dict[str, Any]]
        if isinstance(self.preferences, Unset):
            preferences = UNSET
        elif isinstance(self.preferences, Preferences):
            preferences = self.preferences.to_dict()
        else:
            preferences = self.preferences

        roles: Union[Unset, list[str]] = UNSET
        if not isinstance(self.roles, Unset):
            roles = []
            for roles_item_data in self.roles:
                roles_item = roles_item_data.value
                roles.append(roles_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "active": active,
                "created_at": created_at,
                "email": email,
                "id": id,
                "status": status,
                "username": username,
            }
        )
        if preferences is not UNSET:
            field_dict["preferences"] = preferences
        if roles is not UNSET:
            field_dict["roles"] = roles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preferences import Preferences

        d = dict(src_dict)
        active = d.pop("active")

        created_at = isoparse(d.pop("created_at"))

        email = d.pop("email")

        id = d.pop("id")

        status = AccountStatus(d.pop("status"))

        username = d.pop("username")

        def _parse_preferences(data: object) -> Union["Preferences", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                preferences_type_1 = Preferences.from_dict(data)

                return preferences_type_1
            except:  # noqa: E722
                pass
            return cast(Union["Preferences", None, Unset], data)

        preferences = _parse_preferences(d.pop("preferences", UNSET))

        roles = []
        _roles = d.pop("roles", UNSET)
        for roles_item_data in _roles or []:
            roles_item = Role(roles_item_data)

            roles.append(roles_item)

        user = cls(
            active=active,
            created_at=created_at,
            email=email,
            id=id,
            status=status,
            username=username,
            preferences=preferences,
            roles=roles,
        )

        user.additional_properties = d
        return user

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
