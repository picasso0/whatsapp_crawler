from dotenv import load_dotenv
from requests import post
from os import getenv



def send_profiles_to_worker(worker_ip, profiles_json):
    load_dotenv()
    worker_port = int(getenv("WORKER_PORT"))
    token = str(getenv("TOKEN"))
    headers = {"Content-Type": "application/json", "authorization": token}
    response = post(
        f"http://{worker_ip}:{worker_port}/check_numbers/", data=profiles_json, headers=headers)
    return response.json()
