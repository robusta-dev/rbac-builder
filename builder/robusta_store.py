from collections import defaultdict
from typing import List, Dict

from builder.env_vars import STORE_URL, STORE_API_KEY, STORE_USER, STORE_PASSWORD, ACCOUNT_NAME
from builder.model import RobustaPermissionScope, RobustaPermissionGroup, User
from builder.storage_dal import StorageDal


class RobustaStore:

    def __init__(self):
        self.dal = StorageDal(
            url=STORE_URL,
            key=STORE_API_KEY,
            email=STORE_USER,
            password=STORE_PASSWORD,
        )

    def close(self):
        try:
            self.dal.close()
        except:
            pass

    def get_account_id(self) -> str:
        if not ACCOUNT_NAME:
            raise Exception("Account name parameter not found")
        return self.dal.get_account_id(ACCOUNT_NAME)

    def get_robusta_users(self) -> List[User]:
        return self.dal.get_robusta_users()

    def get_permission_scopes(self, account_id: str) -> Dict[str, RobustaPermissionScope]:
        return {scope.name: scope for scope in self.dal.get_permission_scopes(account_id=account_id)}

    def get_permission_groups(self, account_id: str) -> Dict[str, RobustaPermissionGroup]:
        return {group.name: group for group in self.dal.get_permission_groups(account_id=account_id)}

    def upsert_scope(self, scope: RobustaPermissionScope):
        self.dal.upsert_scope(scope=scope)

    def delete_scope(self, scope: RobustaPermissionScope):
        self.dal.delete_scope(scope=scope)

    def upsert_group(self, group: RobustaPermissionGroup):
        self.dal.upsert_group(group=group)

    def delete_group(self, group: RobustaPermissionGroup):
        self.dal.delete_group(group=group)

    def delete_account_groups(self, account_id: str):
        self.dal.delete_account_groups(account_id=account_id)

    def delete_account_scopes(self, account_id: str):
        self.dal.delete_account_scopes(account_id=account_id)

    def set_user_groups(self, user_id: str, groups: List[str]):
        self.dal.set_user_groups(user_id, groups)

    def get_users_groups(self) -> Dict[str, List[str]]:
        user_groups: Dict[str, List[str]] = defaultdict(list)
        stored_groups = self.dal.get_users_groups()
        for user_group in stored_groups:
            user_groups[user_group.user_id].append(user_group.group_id)
        return user_groups