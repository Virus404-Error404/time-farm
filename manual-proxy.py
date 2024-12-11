import requests as reqs
import asyncio
import aiohttp
import time
import uuid
from curl_cffi import requests
from loguru import logger
from fake_useragent import UserAgent
from utils.banner import banner
from colorama import Fore, Style, init

# Constants
PING_INTERVAL = 60
RETRIES = 60
PROXY_FILE = 'auto_proxies.txt'
DOMAIN_API = {
    "SESSION": "http://api.nodepay.ai/api/auth/session",
    "PING": "https://nw.nodepay.org/api/network/ping"
}

CONNECTION_STATES = {
    "CONNECTED": 1,
    "DISCONNECTED": 2,
    "NONE_CONNECTION": 3
}

status_connect = CONNECTION_STATES["NONE_CONNECTION"]
browser_id = None
account_info = {}
last_ping_time = {}  

def uuidv4():
    return str(uuid.uuid4())

def show_copyright():
    print(Fore.MAGENTA + Style.BRIGHT + banner + Style.RESET_ALL)
        
def valid_resp(resp):
    if not resp or "code" not in resp or resp["code"] < 0:
        raise ValueError("Invalid response")
    return resp
    
async def render_profile_info(proxy, token):
    global browser_id, account_info

    try:
        np_session_info = load_session_info(proxy)

        if not np_session_info:
            # Generate new browser_id
            browser_id = uuidv4()
            response = await call_api(DOMAIN_API["SESSION"], {}, proxy, token)
            valid_resp(response)
            account_info = response["data"]
            if account_info.get("uid"):
                save_session_info(proxy, account_info)
                await start_ping(proxy, token)
            else:
                handle_logout(proxy)
        else:
            account_info = np_session_info
            await start_ping(proxy, token)
    except Exception as e:
        logger.error(f"Error in render_profile_info for proxy {proxy}: {e}")
        error_message = str(e)
        if any(phrase in error_message for phrase in [
            "sent 1011 (internal error) keepalive ping timeout; no close frame received",
            "500 Internal Server Error"
        ]):
            logger.info(f"Removing error proxy from the list: {proxy}")
            remove_proxy_from_list(proxy)
            return None
        else:
            logger.error(f"Connection error: {e}")
            return proxy

async def call_api(url, data, proxy, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": "chrome-extension://lgmpfmgeabnnlemejacfljbmonaomfmm",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.post(url, json=data, headers=headers, impersonate="safari15_5", proxies={
                                "http": proxy, "https": proxy}, timeout=15)

        response.raise_for_status()
        return valid_resp(response.json())
    except Exception as e:
        logger.error(f"Error during API call: {e}")
        raise ValueError(f"Failed API call to {url}")

async def start_ping(proxy, token):
    try:
        while True:
            await ping(proxy, token)
            await asyncio.sleep(PING_INTERVAL)
    except asyncio.CancelledError:
        logger.info(f"Ping task for proxy {proxy} was cancelled")
    except Exception as e:
        logger.error(f"Error in start_ping for proxy {proxy}: {e}")
        
async def ping(proxy, token):
    global last_ping_time, RETRIES, status_connect

    current_time = time.time()

    if proxy in last_ping_time and (current_time - last_ping_time[proxy]) < PING_INTERVAL:
        logger.info(f"Skipping ping for proxy { proxy}, not enough time elapsed")
        return

    last_ping_time[proxy] = current_time

    try:
        data = {
            "id": account_info.get("uid"),
            "browser_id": browser_id,  
            "timestamp": int(time.time()),
            "version": "2.2.7"
        }

        response = await call_api(DOMAIN_API["PING"], data, proxy, token)
        if response["code"] == 0:
            logger.info(f"Ping successful via proxy {proxy}: {response}")
            RETRIES = 0
            status_connect = CONNECTION_STATES["CONNECTED"]
        else:
            handle_ping_fail(proxy, response)
    except Exception as e:
        logger.error(f"Ping failed via proxy {proxy}: {e}")
        handle_ping_fail(proxy, None)

def handle_ping_fail(proxy, response):
    global RETRIES, status_connect

    RETRIES += 1
    if response and response.get("code") == 403:
        handle_logout(proxy)
    elif RETRIES < 2:
        status_connect = CONNECTION_STATES["DISCONNECTED"]
    else:
        status_connect = CONNECTION_STATES["DISCONNECTED"]

def handle_logout(proxy):
    global status_connect, account_info

    status_connect = CONNECTION_STATES["NONE_CONNECTION"]
    account_info = {}
    save_status(proxy, None)
    logger.info(f"Logged out and cleared session info for proxy {proxy}")

def load_proxies(proxy_file):
    try:
        with open(proxy_file, 'r') as file:
            proxies = file.read().splitlines()
        return proxies
    except Exception as e:
        logger.error(f"Failed to load proxies: {e}")
        raise SystemExit("Exiting due to failure in loading proxies")

def save_status(proxy, status):
    pass  

def save_session_info(proxy, data):
    data_to_save = {
        "uid": data.get("uid"),
        "browser_id": browser_id  
    }
    pass

def load_session_info(proxy):
    return {}  

def is_valid_proxy(proxy):
    return True  

def remove_proxy_from_list(proxy):
    pass  
        
async def main():
    all_proxies = load_proxies(PROXY_FILE)  

    tokens = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzEwMjQ3ODQ1MzE5NjcxODA4IiwiaWF0IjoxNzMzODM1NTQwLCJleHAiOjE3MzUwNDUxNDB9.JSI41mtK9aaf8MKNPM5oR0DSJHDjJNizoifgiVbGiTeb3_xjKzUFo_WSV8_r1293TLGr0WFB4GBbdoXtSEGe_A"
    if not tokens:
        print("Token cannot be empty. Exiting the program.")
        exit()
    if not all_proxies:
        print("Proxies cannot be empty. Exiting the program.")
        exit()

    while True:
        for token in tokens:
            active_proxies = [
            proxy for proxy in all_proxies if is_valid_proxy(proxy)][:100]
            tasks = {asyncio.create_task(render_profile_info(
                proxy, token)): proxy for proxy in active_proxies}
    
            done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                failed_proxy = tasks[task]
                if task.result() is None:
                    logger.info(f"Removing and replacing failed proxy: {failed_proxy}")
                    active_proxies.remove(failed_proxy)
                    if all_proxies:
                        new_proxy = all_proxies.pop(0)
                        if is_valid_proxy(new_proxy):
                            active_proxies.append(new_proxy)
                            new_task = asyncio.create_task(
                                render_profile_info(new_proxy, token))
                            tasks[new_task] = new_proxy
                tasks.pop(task)
    
            for proxy in set(active_proxies) - set(tasks.values()):
                new_task = asyncio.create_task(
                    render_profile_info(proxy, token))
                tasks[new_task] = proxy
            await asyncio.sleep(3)
    await asyncio.sleep(10)  

def fetch_proxies():
    api_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text"
    try:
        response = requests.get(api_url, stream=True)
        if response.status_code == 200:
            print(response.status_code)
            proxies = response.text.strip().splitlines()
            if proxies:
                with open('auto_proxies.txt', 'w') as f:
                    f.writelines([proxy + '\n' for proxy in proxies])
                print(f"Fetched and saved {len(proxies)} proxies to 'auto_proxies.txt'.")
            else:
                print("No proxies found from the API.")
                return False
        else:
            print(f"Failed to fetch proxies. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error fetching proxies: {e}")
        return False
    return True

import os
PROXY_SOURCE_URL = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text"

if __name__ == '__main__':
    if os.path.exists(PROXY_FILE):
        os.remove(PROXY_FILE)
        logger.info(f"Deleted existing {PROXY_FILE}")

    try:
        response = requests.get(PROXY_SOURCE_URL, timeout=10)
        response.raise_for_status()  # Raise error for HTTP issues
        proxies = response.text.strip()  # Get the proxies as plain text

        if not proxies:
            raise ValueError("No proxies received from the source!")

        # Save proxies to proxies.txt
        with open(PROXY_FILE, 'w') as proxy_file:
            proxy_file.write(proxies)
        logger.info(f"Fetched and saved new proxies to {PROXY_FILE}")

    except Exception as e:
        logger.error(f"Failed to fetch proxies: {e}")
        raise SystemExit("Exiting due to failure in fetching proxies.")
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Program terminated by user.")
