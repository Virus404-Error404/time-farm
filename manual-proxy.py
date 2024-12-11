import requests
import json
import time

req = requests.Session()
#PASTE HERE
token = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzQwMDg2MzcsInR5cGUiOiJhY2Nlc3MiLCJpYXQiOjE3MzM5MjIyMzcsImF1ZCI6InRnLmFpLmpvYnMiLCJpc3MiOiJ0Zy5haS5qb2JzIiwic3ViIjoiNzc2NTAzNjU4OSIsImp0aSI6IjRkbWNjcnFtNGp3ajR0cCJ9.Nxj1tYHc0guBwnRnjH7_17KfJ8071h8jAfQhrRFGTzWKlL-7gPkCkIzA5SUkbd3gtvOo9zJkU5_iWgNxs_jTjnDv8W2_pjtBxz6VYBnAkdLaMUuQTNYqSUS1mzKuVlQMkDG5gTCPIQlsm32XqroW33ZybcXyhXmDO5DIUvDoPpMuphHR53u8tF3HUOgtxBxmMFsLl0AuySYLilyzD3fPC-amG5b_E9eg95JlHOl4wDuKyjhraDQemR9GT1epf2DGGrQesqoEnDt-QL_eiq4Bb_ipNQMgu5A0Ni0cTwhUaz6dkM2W0vQnWnTAHcyzPhj17UcuaEPx5rar3qvLe5-Kw0ackWmOus2KGa-2zCd5LMBbrB9NotkB8W8nFb9vsKnzAvuEvd2ic8byOdHn-Bj1Lua-T0Nd0AbC47pKDEWxom2UkSOM5mdAZ41ghwxpmjCAEQCSG4n5izcyAaGkWRBWYMkk2-JDTrAgUu3FzOZ4cg-Ta5Tpy3QfrX0DU9Ax3cI_DJpbcip8EvwNPLWGqAS84Nb08tkJTtoQNeDS96X03lu4XZwC31zuZWrVJBDamIgyrmbuY89nVnjo6GRn34Bj9XLHQU6sQcf8FvjhFSnt6gNtkAl9w4IHZrDN4nSBFMFAY_9mcroDlVzHizxAV9wjkkBqZOc05fGtcO6ZJ_QDzYw"

headers = {
    "accept": "/",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "authorization": token,
    "Content-Type": "application/json",
    "Origin": "https://tg-tap-miniapp.laborx.io",
    "Referer": "https://tg-tap-miniapp.laborx.io/",
    "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\"",
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": "\"ANDROID\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "sec-gpc": "1",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
}

def get_balance_info():
    try:
        response = req.get("https://tg-bot-tap.laborx.io/api/v1/farming/info", headers=headers)
        data = response.json()
        balance = data.get("balance")
        active_farm = data.get("activeFarmingStartedAt")
        print("Balance: " + str(balance))
        print("Active Farming Started At: " + str(active_farm))
    except requests.RequestException as error:
        print("Error getting farming info:", error)

def start_farming():
    try:
        response = req.post("https://tg-bot-tap.laborx.io/api/v1/farming/start", headers=headers, data={})
        if response.status_code == 200:
            print("Started Farming")
    except requests.RequestException as e:
        print("Error starting farming:", e)

def finish_farming():
    try:
        response = req.post("https://tg-bot-tap.laborx.io/api/v1/farming/finish", headers=headers, data={})
        if response.status_code == 200:
            print("Finished Farming")
            time.sleep(3)
            start_farming()
    except requests.RequestException as e:
        print("Error finishing farming:", e)

def get_id_task():
    url = "https://tg-bot-tap.laborx.io/api/v1/tasks/"
    try:
        response_tasks = req.get(url, headers=headers)
        response_data_tasks = response_tasks.json()
        ids = [item["id"] for item in response_data_tasks]
        titles = [item["title"] for item in response_data_tasks]
        return ids, titles
    except requests.RequestException as error:
        print("Error getting farming info:", error)

def complete_task():
    try:
        ids, titles = get_id_task()
        for id_task, title in zip(ids, titles):
            url = "https://tg-bot-tap.laborx.io/api/v1/tasks/{}/submissions".format(id_task)
            response = req.post(url, headers=headers).json()
            if 'OK' in response:
                print("Bypass => " + title)
                print(response)
                time.sleep(1)
            else:
                print("Already submitted => " + title)
    except requests.RequestException as error:
        print("Error completing task:", error)

def claim_task():
    complete_task()
    ids, titles = get_id_task()
    try:
        for id_task, title in zip(ids, titles):
            response = req.get("https://tg-bot-tap.laborx.io/api/v1/tasks/{}".format(id_task), headers=headers)
            task = response.json()
            if not task.get("submission") or task.get("submission").get("status") == "REJECTED":
                response = req.post("https://tg-bot-tap.laborx.io/api/v1/tasks/{}/submissions".format(id_task), headers=headers)
                print("Successfully submitted task : " + title)
                time.sleep(1)
            elif task.get("submission").get("status") == "SUBMITTED":
                print("cannot be claimed yet " + " => " +  title)
            elif task.get("submission").get("status") == "COMPLETED":
                response = req.post("https://tg-bot-tap.laborx.io/api/v1/tasks/{}/claims".format(id_task), headers=headers)
                print("Successfully claimed task" + " => " +  title)
                time.sleep(1)
            elif task.get("submission").get("status") == "CLAIMED":
                print("already claimed" + " => " +  title)
            if task.get("submission") and task.get("submission").get("status") != "CLAIMED":
                all_claimed = False
        if all_claimed:
            print("All tasks have been completed")
    except requests.RequestException as error:
        print("Error processing tasks:", error)

if __name__ == "__main__":
    get_balance_info()
    finish_farming()
    claim_task()
    print("\nWaiting 1 hour before starting again...")
    time.sleep(60 * 60)
