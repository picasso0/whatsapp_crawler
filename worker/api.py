from fastapi import FastAPI
from typing import Dict, List
from utils import extract_zip, download_file, is_zip_file, remove_directory, send_data_to_c2
from pydantic import BaseModel
from worker import Worker
import asyncio
import os


worker = Worker()
app = FastAPI()


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
async def profile(profiles: Profiles):
    if worker.user_data_path == None or not os.path.exists(worker.user_data_path):
        return {"status": False}
    asyncio.create_task(worker.check_whatsapp_phones(
        phones=profiles.phone_numbers, report=profiles.report))
    # await worker.check_whatsapp_phones(phones=profiles.phone_numbers,report=profiles.report)
    return {"status": True}


@app.get("/check_alive/")
async def check_alive():
    return {"status": True}
