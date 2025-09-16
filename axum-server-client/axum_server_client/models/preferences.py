import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.theme import Theme
from ..types import UNSET, Unset

T = TypeVar("T", bound="Preferences")


@_attrs_define
class Preferences:
    """
    Attributes:
        theme (Theme):
        last_login_at (Union[Unset, datetime.datetime]):
        timezone (Union[None, Unset, str]):
    """

    theme: Theme
    last_login_at: Union[Unset, datetime.datetime] = UNSET
    timezone: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        theme = self.theme.value

        last_login_at: Union[Unset, str] = UNSET
        if not isinstance(self.last_login_at, Unset):
            last_login_at = self.last_login_at.isoformat()

        timezone: Union[None, Unset, str]
        if isinstance(self.timezone, Unset):
            timezone = UNSET
        else:
            timezone = self.timezone

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "theme": theme,
            }
        )
        if last_login_at is not UNSET:
            field_dict["last_login_at"] = last_login_at
        if timezone is not UNSET:
            field_dict["timezone"] = timezone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        theme = Theme(d.pop("theme"))

        _last_login_at = d.pop("last_login_at", UNSET)
        last_login_at: Union[Unset, datetime.datetime]
        if isinstance(_last_login_at, Unset):
            last_login_at = UNSET
        else:
            last_login_at = isoparse(_last_login_at)

        def _parse_timezone(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        timezone = _parse_timezone(d.pop("timezone", UNSET))

        preferences = cls(
            theme=theme,
            last_login_at=last_login_at,
            timezone=timezone,
        )

        preferences.additional_properties = d
        return preferences

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
