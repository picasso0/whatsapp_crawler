from dotenv import load_dotenv
from requests import post, get
from os import getenv



def send_data_to_worker(worker_ip, method, endpoint, data):
    try:
        load_dotenv()
        worker_port = int(getenv("WORKER_PORT"))
        token = str(getenv("TOKEN"))
        headers = {"Content-Type": "application/json", "authorization": token}
        if method=="POST":
            response = post(
                f"http://{worker_ip}:{worker_port}/{endpoint}/", data=data, headers=headers)
        if method=="GET":
            response = get(
                f"http://{worker_ip}:{worker_port}/{endpoint}/", params=data, headers=headers)
        return response
    except:
       return False