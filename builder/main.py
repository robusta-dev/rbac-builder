import os
import sys

from builder.ssh_utils import add_custom_certificate
ADDITIONAL_CERTIFICATE: str = os.environ.get("CERTIFICATE", "")

if add_custom_certificate(ADDITIONAL_CERTIFICATE):
    print("added custom certificate")

# DO NOT ADD IMPORTS ABOVE THIS LINE. IT MAY CAUSE CACHED HTTP CLIENT WHICH DOESN'T RESPECT CUSTOM CERTIFICATES

from builder.config_builder import ConfigBuilder
import logging
from typing import Optional

from builder.env_vars import LOG_LEVEL
from builder.robusta_store import RobustaStore

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(LOG_LEVEL)
logging.info(f'logger initialized using {LOG_LEVEL} log level')

# Pseudo code:
#
# Read the account_id, scopes and groups configuration file
# generate uuids for scopes
# generate uuids for groups
# update groups to scope mapping to be by uuid (not by name as in the config)
# delete all existing groups and scopes
# persist new scopes and groups

if __name__ == '__main__':
    logging.info("Running rbac builder...")
    robusta_store: Optional[RobustaStore] = None
    try:
        # read scopes and groups from the configuration
        config_reader = ConfigBuilder("../config/definitions.yaml")

        # Data layer for the Robusta platform DB
        robusta_store: RobustaStore = RobustaStore()

        account_id = config_reader.get_account_id()
        if not account_id:
            raise Exception("Account id not found in configuration file.")

        # need to first delete the groups, and only then the scopes because of foreign keys
        robusta_store.delete_account_groups(account_id=account_id)
        robusta_store.delete_account_scopes(account_id=account_id)

        # first create scopes, because of foreign keys
        for scope in config_reader.get_scopes():
            robusta_store.upsert_scope(scope=scope)

        for group in config_reader.get_groups():
            robusta_store.upsert_group(group=group)

    except Exception as e:
        logging.exception("Error building rbac definitions")
        raise e
    finally:
        logging.info("Done building rbac definitions")
        if robusta_store:
            robusta_store.close()
        logging.info("Exiting")
    sys.exit(0)
