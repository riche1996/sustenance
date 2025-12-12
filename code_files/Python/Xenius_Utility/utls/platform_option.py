

import json
import os

from utility.common_utility.path_manager import safe_join
from utility.db_utility.pg_db_engine import log_utils

logger = log_utils.get_logger()

CURRENT_DIR = os.path.abspath(os.getcwd())
CONFIG_DIR = safe_join(CURRENT_DIR, "config")
FILE_NAME = "platform_options.json"
SUCCESS = "Success"
FAILED = "Failed"


def get_platform_options(_request):
    """
    This methods helps to get the platform options (only active).
    Sorted the content based on id.
    """
    file_path = safe_join(CONFIG_DIR, FILE_NAME)
    if os.path.exists(file_path):
        try:
            with open(file_path, encoding="utf_8") as f:
                json_response = json.load(f)

            filtered_data = [
                category for category in json_response if category["is_active"] == "True"
            ]
            for category in filtered_data:
                category["category_items"] = [
                    item for item in category["category_items"] if item["is_active"] == "True"
                ]

            sorted_data = sorted(filtered_data, key=lambda x: x["category_id"])
            for category in sorted_data:
                category["category_items"] = sorted(
                    category["category_items"], key=lambda x: x["id"]
                )

            return {"status": SUCCESS, "data": sorted_data, "err_msg": ""}
        except Exception as e:
            logger.error(str(e), exc_info=True)
            print(f"Exception : {str(e)}")
            return {"status": FAILED, "data": [], "err_msg": "File Not Found."}
    else:
        return {"status": FAILED, "data": [], "err_msg": "File Not Found."}
