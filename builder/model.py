from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional




class User(BaseModel):
    id: str
    email: Optional[str] = None


class RobustaPermissionScope(BaseModel):
    account_id: str
    scope_type: str
    scope_id: str
    name: str
    scope_data: Dict[str, List[str]]

    def __eq__(self, other) -> bool:
        if not isinstance(other, RobustaPermissionScope):
            return False

        return \
                self.account_id == other.account_id and \
                self.scope_type == other.scope_type and \
                self.scope_id == other.scope_id and \
                self.name == other.name and \
                self.__scope_data_eq(other.scope_data)

    def __scope_data_eq(self, other_scope_data: Dict[str, List[str]]) -> bool:
        return sorted(self.scope_data.keys()) == sorted(other_scope_data.keys()) and \
            all([
                sorted(self.scope_data.get(key)) == sorted(other_scope_data.get(key))
                for key in self.scope_data.keys()
            ])

class RobustaPermissionGroup(BaseModel):
    account_id: str
    group_id: str
    provider_group_id: str
    name: str
    scope_type: str
    scopes: List[str]
    permissions: List[str]

    def __eq__(self, other) -> bool:
        if not isinstance(other, RobustaPermissionGroup):
            return False

        return \
                self.account_id == other.account_id and \
                self.group_id == other.group_id and \
                self.provider_group_id == other.provider_group_id and \
                self.name == other.name and \
                self.scope_type == other.scope_type and \
                sorted(self.scopes) == sorted(other.scopes) and \
                sorted(self.permissions) == sorted(other.permissions)

class UserGroup(BaseModel):
    user_id: str
    group_id: str