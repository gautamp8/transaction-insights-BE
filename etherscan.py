import os
import requests

from logger import get_logger

session = requests.Session()

ETHERSCAN_API_KEY = os.environ["ETHERSCAN_API_KEY"]
BASE_URL = f"https://api.etherscan.io"

logger = get_logger(__name__)


def make_get(endpoint, consume_exceptions=False, defval=None, **params):
    url = f"{BASE_URL}/{endpoint}"
    response = session.get(url, params=params)
    if consume_exceptions:
        try:
            return response.json()
        except Exception as e:
            logger.error(
                f"Exception occurred in endpoint {endpoint}: {e}. Returning defval."
            )
            return defval
    return response.json()


def is_verified_contract(address):
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": ETHERSCAN_API_KEY,
    }
    response = make_get("api", **params)
    if response["status"] != "1":
        return False
    if not response["result"]:
        return False
    return response["result"][0]["SourceCode"] != "Contract source code not verified"
