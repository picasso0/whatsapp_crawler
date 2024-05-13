from fastapi import FastAPI, HTTPException, Header
from typing import Dict, List
from pydantic import BaseModel
from worker import Worker
import asyncio
from dotenv import load_dotenv
import os
from time import sleep


app = FastAPI()
load_dotenv()
worker = Worker()
init_status=False
while(init_status==False):
    init_status=worker.initialize()
    sleep(60)
worker.im_ready()

class Initialize(BaseModel):
    worker_id: int
    user_data_path: str


class Profile(BaseModel):
    id: str
    mobile: str


class Profiles(BaseModel):
    phone_numbers: List[Profile]
    report: dict


@app.post("/check_numbers/")
async def check_numbers(profiles: Profiles, authorization: str = Header(None)):
    
    correct_token = str(os.getenv("TOKEN"))
    if authorization is None or authorization != correct_token:
        raise HTTPException(status_code=401, detail="کاربر احراز هویت نشده است")

    if worker.user_data_path == None or not os.path.exists(worker.user_data_path):
        return {"status": False}
    # asyncio.create_task(worker.check_whatsapp_phones(
    #     phones=profiles.phone_numbers, report=profiles.report))
    await worker.check_whatsapp_phones(phones=profiles.phone_numbers,report=profiles.report)
    return {"status": True}


@app.get("/check_alive/")
async def check_alive(authorization: str = Header(None)):
    return {"status": True}
