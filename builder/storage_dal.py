import logging
import time
import traceback
from typing import Dict, List, Optional

import requests
from postgrest.types import ReturnMethod
from supabase import create_client
from supabase.lib.client_options import ClientOptions

from builder.model import User, RobustaPermissionScope, RobustaPermissionGroup, UserGroup

ACCOUNTS_TABLE = "Accounts"
PERMISSION_SCOPES_TABLE = "PermissionScopes"
PERMISSION_GROUPS_TABLE = "PermissionGroups"
USER_GROUPS_TABLE = "UserGroups"

class StorageDal:
    def __init__(
        self,
        url: str,
        key: str,
        email: str,
        password: str,
    ):
        httpx_logger = logging.getLogger("httpx")
        if httpx_logger:
            httpx_logger.setLevel(logging.WARNING)

        self.url = url
        self.key = key
        options = ClientOptions(postgrest_client_timeout=60)
        self.client = create_client(url, key, options)
        self.email = email
        self.password = password
        self.sign_in_time = 0
        self.sign_in()
        self.client.auth.on_auth_state_change(self.__update_token_patch)

    def __update_token_patch(self, event, session):
        logging.debug(f"Event {event}, Session {session}")
        if session and event == "TOKEN_REFRESHED":
            self.client.postgrest.auth(session.access_token)


    def get_account_id(self, account_name: str) -> Optional[str]:
        try:
            res = (
                self.client.table(ACCOUNTS_TABLE)
                    .select("*")
                    .eq("name", account_name)
                    .execute()
            )
            if len(res.data) == 0:
                logging.error(f"Account {account_name} not found. res: {res.data}")
                return None

            return res.data[0]["id"]

        except Exception:
            logging.error(f"Unexpected error in get account by name for {account_name}",  exc_info=True)
            return None

    def delete_account_groups(self, account_id: str):
        try:
            self.client.table(PERMISSION_GROUPS_TABLE).delete(returning=ReturnMethod.minimal)\
                .eq("account_id", account_id).execute()
        except Exception as e:
            logging.exception(f"Failed to delete account groups for {account_id}")
            raise e

    def delete_account_scopes(self, account_id: str):
        try:
            self.client.table(PERMISSION_SCOPES_TABLE).delete(returning=ReturnMethod.minimal)\
                .eq("account_id", account_id).execute()
        except Exception as e:
            logging.exception(f"Failed to delete account groups for {account_id}")
            raise e

    def set_user_groups(self, user_id: str, group_ids: List[str]):
        try:
            res = self.sync_rpc(func_name="set_user_external_rbac_groups",
                          params={
                              "_user_id": user_id,
                              "_group_ids": group_ids
                          })
            status_code = res.get("status_code")
            if status_code >= 300:
                self.handle_supabase_error()
                raise Exception(f"Failed to add user groups. user: {user_id} groups: {group_ids} code: {status_code}")

        except Exception as e:
            logging.exception(f"Error adding user groups for user:{user_id} groups:{group_ids}")
            raise e

    def get_users_groups(self) -> List[UserGroup]:
        try:
            res = self.client.table(USER_GROUPS_TABLE).select("*").execute()
            user_groups = [UserGroup(**entry) for entry in res.data]
        except Exception as e:
            logging.exception(f"Failed to list users robusta groups")
            raise e

        return user_groups

    def get_robusta_users(self) -> List[User]:
        robusta_users = []
        try:
            res = self.sync_rpc(func_name="relay_get_all_users")
            status_code = res.get("status_code")
            if status_code >= 300:
                self.handle_supabase_error()
                raise Exception(f"Failed to get robusta groups. code: {status_code}")

            response_data = res.get("data")
            if not response_data:
                logging.warning(f"No robusta users found. response data: {response_data}")
                return robusta_users

            for user_data in response_data:
                robusta_users.append(User(id=user_data["id"], email=user_data["email"]))

        except Exception as e:
            logging.exception(f"Failed to list robusta users")
            raise e

        return robusta_users

    def get_permission_scopes(self, account_id: str) -> List[RobustaPermissionScope]:
        try:
            res = self.client.table(PERMISSION_SCOPES_TABLE).select("*").eq("account_id", account_id).execute()
            robusta_scopes = [RobustaPermissionScope(**entry) for entry in res.data]
        except Exception as e:
            logging.exception(f"Failed to list robusta scopes for {account_id}")
            raise e

        return robusta_scopes

    def get_permission_groups(self, account_id: str) -> List[RobustaPermissionGroup]:
        try:
            res = self.client.table(PERMISSION_GROUPS_TABLE).select("*").eq("account_id", account_id).execute()
            robusta_groups = [RobustaPermissionGroup(**entry) for entry in res.data]
        except Exception as e:
            logging.exception(f"Failed to list robusta groups for {account_id}")
            raise e

        return robusta_groups

    def upsert_scope(self, scope: RobustaPermissionScope):
        try:
            self.client.table(PERMISSION_SCOPES_TABLE).upsert(scope.dict()).execute()
        except Exception as e:
            logging.exception(f"Failed to upsert scope {scope}")
            raise e

    def delete_scope(self, scope: RobustaPermissionScope):
        try:
            self.client.table(PERMISSION_SCOPES_TABLE).delete(returning=ReturnMethod.minimal)\
                .eq("account_id",scope.account_id).eq("scope_id", scope.scope_id).execute()
        except Exception as e:
            logging.exception(f"Failed to delete scope {scope}")
            raise e

    def upsert_group(self, group: RobustaPermissionGroup):
        try:
            self.client.table(PERMISSION_GROUPS_TABLE).upsert(group.dict()).execute()
        except Exception as e:
            logging.exception(f"Failed to upsert group {group}")
            raise e

    def delete_group(self, group: RobustaPermissionGroup):
        try:
            self.client.table(PERMISSION_GROUPS_TABLE).delete(returning=ReturnMethod.minimal)\
                .eq("account_id", group.account_id).eq("group_id", group.group_id).execute()
        except Exception as e:
            logging.exception(f"Failed to delete scope {group}")
            raise e

    def close(self):
        self.client.auth.sign_out()

    def sign_in(self):
        if time.time() > self.sign_in_time + 900:
            logging.info("Supabase dal login")
            self.sign_in_time = time.time()
            res = self.client.auth.sign_in_with_password({"email": self.email, "password": self.password})
            self.client.auth.set_session(res.session.access_token, res.session.refresh_token)
            self.client.postgrest.auth(res.session.access_token)

    def handle_supabase_error(self):
        """Workaround for Gotrue bug in refresh token."""
        # If there's an error during refresh token, no new refresh timer task is created, and the client remains not authenticated for good
        # When there's an error connecting to supabase server, we will re-login, to re-authenticate the session.
        # Adding rate-limiting mechanism, not to login too much because of other errors
        # https://github.com/supabase/gotrue-py/issues/9
        try:
            self.sign_in()
        except Exception:
            logging.error("Failed to signin on error", traceback.print_exc())

    def sync_rpc(self, func_name: str, params: Optional[dict] = None) -> Dict:
        """
        Supabase client is async. Sync impl of rpc call
        """
        client = self.client
        headers = client.table("").session.headers
        url: str = f"{client.rest_url}/rpc/{func_name}"

        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        response_data = {}
        try:
            if response.content:
                response_data = response.json()
        except Exception:  # this can be okay if no data is expected
            logging.debug("Failed to parse rpc response data")

        return {
            "data": response_data,
            "status_code": response.status_code,
        }
