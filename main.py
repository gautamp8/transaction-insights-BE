import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from flatten_json import flatten
import pyotp
from pydantic import BaseModel
import requests
import uvicorn

import constants
import etherscan
from logger import get_logger
import sourcify
import tenderly
from utils import ErrorHandlerRoute, is_contract_address_on_eth

import schemas

load_dotenv()
logger = get_logger(__name__)
auth_token = os.environ['AUTH_TOKEN']

app = FastAPI(
    title='f5 API', description='', version='0.1',
)
app.router.route_class = ErrorHandlerRoute

base_url = "https://6646-122-171-21-176.ngrok.io"

# TODO: This needs to be tuned
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

txns_cache = {}
counter = 0


def send_validation_error(detail):
    logger.error(f"Validation error: {detail}")
    raise HTTPException(status_code=422, detail=detail)


def validate_body(body) -> bool:
    return True


def get_totp():
    return pyotp.TOTP(os.getenv('TOTP_SECRET'))


@app.get('/')
async def status():
    return {
        'status': 'ok'
    }

class AnalyseAddressResponse(BaseModel):
    is_contract: bool
    is_spam_nft: bool
    is_blacklisted_token: bool
    is_verified: bool
    

def analyse_address(address):
    is_contract = is_contract_address_on_eth(address)
    is_spam_nft = is_contract and address in constants.spam_nft_contracts
    is_blacklisted_token = is_contract and address in constants.eth_blacklisted_tokens
    is_verified = is_contract and (sourcify.get_verification_status(address) or etherscan.is_verified_contract(address))
    
    return AnalyseAddressResponse(
        is_contract=is_contract,
        is_spam_nft=is_spam_nft,
        is_blacklisted_token=is_blacklisted_token,
        is_verified=is_verified,
    )

@app.post('/insights/prod', response_model=schemas.InsightsResponse)
async def get_txn_insights(request: schemas.InsightsRequest):
    comments = ""
    tenderly_obj = {
        "network_id": request.chainId.split(":")[1],
        "from": request.from_,
        "to": request.to,
        "input": request.data,
        "gas": int(request.gas, 16),
        "gas_price": "0", # TODO: check
        "value": 0,
        "save_if_fails": True,
        "save": False,
        "simulation_type": "quick"
    }
    
    tracing_response = tenderly.get_trace(tenderly_obj)
    tr_flat = flatten(tracing_response)
    unique_addresses = set()
    for k, v in tr_flat.items():
        if type(v) == str and len(v) == 42 and v.startswith('0x'):
            unique_addresses.add(v)
    
    spam_nfts = set()
    blacklisted_tokens = set()
    non_verified_contracts = set()
    
    global counter
    counter += 1
    txns_cache[counter] = tracing_response
    
    for addr in unique_addresses:
        analysis = analyse_address(addr)
        if analysis.is_contract and addr != '0x0000000000000000000000000000000000000000':
            if analysis.is_spam_nft:
                spam_nfts.add(addr)
            if analysis.is_blacklisted_token:
                blacklisted_tokens.add(addr)
            if not analysis.is_verified:
                non_verified_contracts.add(addr)
    
    if spam_nfts:
        comments += f'🔴 {len(spam_nfts)} Spam NFT contract(s) found. '
    
    if blacklisted_tokens:
        comments += f'🔴 {len(blacklisted_tokens)} Blacklisted token(s) found. '
        
    if non_verified_contracts:
        comments += f'🟡 {len(non_verified_contracts)} Non-verified contract(s) found. '
    
    if not comments:
        comments = '🟢 Safe'
    
    return schemas.InsightsResponse(
        comments=comments,
        is_flagged=bool(spam_nfts or blacklisted_tokens or non_verified_contracts),
        entire_trace_verified=True if (not non_verified_contracts) else False,
        trace_url=f'{base_url}/trace/{counter}',
    )


@app.get('/trace/{trace_id}')
async def get_trace_from_id(trace_id):
    return txns_cache[int(trace_id)]


@app.get('/basic_auth')
async def get_config(token=Depends(HTTPBearer())):
    creds = token.credentials
    if creds != auth_token:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Invalid auth token")
    return 'OK'


@app.post('/basic_auth_and_2fa',)
def update_config_and_save(token=Depends(HTTPBearer()), totp=Depends(get_totp)):
    items = token.credentials.split(':', 1)
    if len(items) < 2:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            detail=f'Invalid credentials provided : {token.credentials}')
    req_auth_token = items[0]
    otp_code = items[1]

    if req_auth_token != auth_token:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            detail=f'Invalid auth token : {token.credentials}')

    # verify otp code
    if not totp.verify(otp_code):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            detail=f'Can not verify otp : {token.credentials}')

    return 'OK'


@app.on_event('startup')
async def startup():
    pass


if __name__ == '__main__':
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    uvicorn.run('main:app', host="0.0.0.0", port=5555, reload=True)
