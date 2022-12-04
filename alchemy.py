import os
import requests

from logger import get_logger

session = requests.Session()

ALCHEMY_API_KEY = os.environ["ALCHEMY_API_KEY"]
BASE_URL = f"https://eth-mainnet.alchemyapi.io/v2/{ALCHEMY_API_KEY}"

logger = get_logger()


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
