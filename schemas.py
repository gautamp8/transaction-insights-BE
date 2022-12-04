from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class InsightsRequest(BaseModel):
    from_: str = ''
    to: str = ''
    data: str = ''
    gas: str = ''
    maxFeePerGas: str = ''
    maxPriorityFeePerGas: str = ''
    value: str = ''
    chainId: str = ''


class InsightsResponse(BaseModel):
    comments: str
    is_flagged: bool
    entire_trace_verified: bool
    trace_url: str


class DevInsightsRequest(BaseModel):
    from_: str = ''
    to: str = ''
    data: str = ''
    gas: str = ''
    maxFeePerGas: str = ''
    maxPriorityFeePerGas: str = ''
    value: str = ''

class DevInsightsResponse(BaseModel):
    is_contract: bool
    is_spam_nft: bool
    is_blacklisted_token: bool
    is_verified_on_etherscan: bool
