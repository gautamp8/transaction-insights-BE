import os
import requests

from logger import get_logger

session = requests.Session()

TENDERLY_API_KEY = os.environ["TENDERLY_API_KEY"]
BASE_URL = f"https://api.tenderly.co/api/v1/account/satwikkansal/project/project"

logger = get_logger(__name__)

def make_post(endpoint, data, consume_exceptions=False, defval=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        'X-Access-Key': TENDERLY_API_KEY
    }
    response = session.post(url, json=data, headers=headers)
    if consume_exceptions:
        try:
            return response.json()
        except Exception as e:
            logger.error(
                f"Exception occurred in endpoint {endpoint}: {e}. Returning defval."
            )
            return defval
    return response.json()


def get_trace(txn_data):
    response = make_post('simulate', txn_data)
    return response