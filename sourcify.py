import requests

session = requests.session()

def get_url(addresses):
    url = f'https://sourcify.dev/server/checkAllByAddresses?addresses={",".join(addresses)}&chainIds=0,1,4,5,11155111,421613,42161,592,1313161554,1313161555,43114,43113,56,97,288,28,534,7700,44787,62320,42220,10200,103090,53935,335,44,43,432201,246,73799,9001,9000,122,486217935,192837465,356256156,100,71402,71401,420420,420666,8217,1001,82,83,1287,1284,1285,62621,311752642,4216137055,10,28528,420,300,99,77,11297108109,11297108099,137,80001,336,57,5700,40,41,8,106,11111,51'
    return url

def get_verification_status(*addresses):
    url = get_url(addresses)
    response = session.get(url).json()
    try:
        chainIds = response[0]["chainIds"]
        return True if chainIds else False
    except Exception as e:
        print(f"Exception occurred {e}")
        return False
