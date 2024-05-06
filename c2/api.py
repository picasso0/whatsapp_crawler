from fastapi import FastAPI, Request, Depends, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from db import get_database
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from minio import Minio
from datetime import datetime
from io import BytesIO
from utils import send_profiles_to_worker
from json import dumps
from time import sleep
from fastapi.responses import JSONResponse
from bson import ObjectId
import asyncio
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    Token,
    UserInRequest,
    oauth2_scheme,
    HTTPException
)

async def get_db_instance():
    database = await get_database()
    return database

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start())


async def start():
    db = await get_db_instance()
    while(True):
        try:
            print("start")
            workers = db.worker.find({"status": 0})
            profiles_data = []
            async for worker in workers:
                profiles = db.profile.find().sort("whatsapp_searches", 1).limit(2000)
                i = 0
                async for profile in profiles:
                    if i == 0:
                        start_id = str(profile['_id'])
                    profiles_data.append(
                        {"id": str(profile['_id']), 'mobile': profile['mobile']})
                    i = i+1
                if len(profiles_data) > 1:
                    db.worker.update_one(
                        {"_id": worker["_id"]},
                        {"$set": {"status": 1}, "$inc": {'reports_count': 1}}
                    )
                    send_data = {
                        'phone_numbers': profiles_data, 'report': {
                            'id': worker['reports_count'],
                            'start_id': start_id,
                            'total_count': i,
                            'start_datetime': None,
                            'end_datetime': None,
                            'find_count': None
                        }
                    }
                    send_profiles_to_worker(worker['ip'], dumps(send_data))
        except:
            pass
        print("end")
        sleep(1800)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)



class WhatsappResult(BaseModel):
    find: bool
    whatsapp: dict
    mobile: str

class WhatsappResults(BaseModel):
    results: List[WhatsappResult]
    report: dict

@app.post("/initialize/")
async def initialize(request: Request, db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    client_ip = request.client.host
    worker = await db.worker.find_one({"ip": client_ip})
    if not worker:
        user_data = await db.user_data.find_one({"status": 0})
        worker_data = {
            "ip": client_ip,
            "app_id": user_data.get("_id"),
            "status": 0,
            "reports": [],
            "reports_count": 0
        }
        worker = await db.worker.insert_one(worker_data)
        if not worker.acknowledged:
            return {
                "status": False
            }
        worker_id = worker.inserted_id
    else:
        worker_id = worker.get("_id")
        user_data = await db.user_data.find_one({"_id": worker.get("app_id")})
        db.worker.update_one(
                        {"_id": worker.get("app_id")},
                        {"$set": {"status": 1}}
                    )
    return_data = {
        "worker_id": str(worker_id),
        "user_data_path": user_data.get("path"),
    }
    return return_data

@app.post("/results/")
async def recive_results(request: Request, results: WhatsappResults, db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    client_ip = request.client.host
    worker = await db.worker.find_one({"ip": client_ip})
    result_data = None
    for result in results.results:
        create_at = datetime.now()
        result_data = dict(result)
        result_data['worker_id'] = str(worker.get("_id"))
        result_data['create_at'] = create_at
        result_data['report_id'] = results.report['id']
        profile = await db.profile.find_one({"mobile": result.mobile})
        if not profile:
            db.profile.insert_one(
                {'mobile': result.mobile, "whatsapp_searches": 0})
        filter_query = {'mobile': result.mobile}
        update_operation = {
            '$push': {'whatsapp': result_data}, "$inc": {"whatsapp_searches": 1}}
        db.profile.update_one(filter_query, update_operation)
    db.worker.update_one(
        {"_id": worker["_id"]},
        {"$set": {"status": 0}, "$push": {'reports': results.report}}
    )
    return {"status": True}


# UI APIes
@app.get("/dashboard/")
async def dashboard(request: Request, current_user: dict = Depends(get_current_user) ,db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    workers_count = await db.worker.count_documents({})
    user_data_count = await db.user_data.count_documents({})
    profiles_count = await db.profile.count_documents({})
    finded_whatsapp_profiles = await db.profile.count_documents({"whatsapp": {"$elemMatch": {"find": True}}})
    return {"workers": workers_count ,"user_data": user_data_count, "profiles": profiles_count,"whatsapp_profiles":finded_whatsapp_profiles}

@app.get("/profiles")
async def get_records(request: Request, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db_instance), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    total_count = await db.profile.count_documents({})
    skip = (page - 1) * limit
    records = []
    async for record in db.profile.find({}).skip(skip).limit(limit):
        record["_id"] = str(record["_id"])
        records.append(record)
    return {"total_count": total_count,"data": records}

@app.get("/profile")
async def profile(request: Request, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db_instance), mobile: str = Query()):
    profile = await db.profile.find_one({"mobile":mobile})
    profile["_id"] = str(profile["_id"])
    return profile

@app.get("/workers")
async def get_records(request: Request, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db_instance), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    total_count = await db.worker.count_documents({})
    skip = (page - 1) * limit
    records = []
    async for record in db.worker.find({}).skip(skip).limit(limit):
        record["_id"] = str(record["_id"])
        if 'app_id' in record:
            record["app_id"] = str(record["app_id"])
        records.append(record)
    return {"total_count": total_count,"data": records}

@app.get("/worker")
async def worker(request: Request,current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db_instance), id: str = Query()):
    worker = await db.worker.find_one({"_id":ObjectId(id)})
    worker["_id"] = str(worker["_id"])
    if 'app_id' in worker:
        worker["app_id"] = str(worker["app_id"])
    return worker

@app.get("/userdatas")
async def get_records(request: Request, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db_instance), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    total_count = await db.user_data.count_documents({})
    skip = (page - 1) * limit
    records = []
    async for record in db.user_data.find({}).skip(skip).limit(limit):
        record["_id"] = str(record["_id"])
        records.append(record)
    return {"total_count": total_count,"data": records}





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'zip'
@app.post("/upload_userdata")
async def upload_zip_file(request: Request, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db_instance), file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only zip files are allowed.")
    minio_client = Minio(
    "minio.sirafgroup.com",
    access_key="7qMlPjxSnrQ6fKGCPpl3",
    secret_key="zuf+RJCJY2rlmuU3WYI7ztbyvnKqq4N7bIdt1AumjA82",
    secure=False
)
    try:
        minio_client.make_bucket("whatsapp")
    except Exception as err:
        print(err)
    try:
        # Save the file to MinIO
        content = await file.read()
        minio_client.put_object(
            "whatsapp",
            file.filename,
            BytesIO(content),
            len(content)
        )
        file_url = f"https://minio.sirafgroup.com/whatsapp/{file.filename}"
        user_data=await db.user_data.insert_one({'status': 0,'path': file_url})
        if not user_data.acknowledged:
            JSONResponse(content="cannot create userdata", status_code=500)        
        return {"message": f"File '{file.filename}' uploaded successfully."}
    except Exception as err:
        JSONResponse(content={"error": str(err)}, status_code=500)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: UserInRequest):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
        raise credentials_exception
        
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

