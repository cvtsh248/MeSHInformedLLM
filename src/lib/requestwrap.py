import asyncio
import httpx
from httpx_retries import RetryTransport, Retry

async def get(url: str, headers: dict={}) -> httpx.Response:
    '''
        Send get request to URL
    '''
    try:
        async with httpx.AsyncClient(transport=RetryTransport()) as client:
            req = await client.get(url, headers=headers)
            return req
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e}")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except httpx.TimeoutException:
        print("The request timed out.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")