from functools import singledispatch
from types import SimpleNamespace
from typing import Callable

from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

    
import functools
import os
import requests
from urllib.parse import urlparse

from logger import get_logger


logger = get_logger(__name__)

BASE_URL = f"https://eth-mainnet.g.alchemy.com/v2/{os.environ['ALCHEMY_API_KEY']}"
session = requests.session()


@singledispatch
def wrap_namespace(ob):
    return ob


@wrap_namespace.register(dict)
def _wrap_dict(ob):
    return SimpleNamespace(**{k: wrap_namespace(v) for k, v in ob.items()})


@wrap_namespace.register(list)
def _wrap_list(ob):
    return [wrap_namespace(v) for v in ob]


class ErrorHandlerRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except RequestValidationError as exc:
                # Default handler will handle this
                raise exc
            except HTTPException as exc:
                # Default handler will handle this
                raise exc
            except Exception as exc:
                logger.exception(f"Error occurred: {exc}")
                # Raise unknown exception
                raise exc

        return custom_route_handler
    


def strip_scheme_from_url(url):
    parsed = urlparse(url)
    scheme = f"{parsed.scheme}://"
    return str(parsed.geturl()).replace(scheme, "", 1)


def is_contract_address_on_eth(address):
    if address.startswith("0x"):
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "params": [address, "latest"],
            "method": "eth_getCode",
        }
        response = session.post(BASE_URL, json=payload)
        data = response.json()
        return data.get("result") != "0x"
    return False


def fail_silently(defval):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception occurred in {func.__name__} args: {args} kwargs: {kwargs}: {e}"
                )
                return defval

        return wrapper

    return decorator

