from fastapi import FastAPI, Request, Depends, Query, File, UploadFile, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from db import get_database
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from minio import Minio
from datetime import datetime
from multiprocessing import Process
from io import BytesIO
from utils import send_data_to_worker
from json import dumps
from time import sleep
from dotenv import load_dotenv
import os
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
import logging
import sys

# SET LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("start")

async def get_db_instance():
    database = await get_database()
    return database

app = FastAPI()
load_dotenv()
@app.on_event("startup")
async def startup_event():
    p = Process(target=run_async_function)
    p.start()


def run_async_function():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())

async def start():
    db = await get_db_instance()
    async for worker in db.worker.find({}):
        try:
            
            response = send_data_to_worker(worker['ip'], "GET", "check_alive", "")
            if response.status_code != 200:
                raise Exception("Worker is down")
            db.worker.update_one({'ip': worker['ip']}, {"$set": {"status": 0}})
        except Exception as e:
            logger.warning(f"Worker {worker['ip']} is down: {str(e)}")
            db.worker.update_one({'ip': worker['ip']}, {"$set": {"status": 3}})
            
    while(True):
        try:
            logger.info("start loop")
            workers = db.worker.find({"status": 0})
            profiles_data = []
            async for worker in workers:
                profiles = db.profile.find({"whatsapp_searching": 0}).sort([("whatsapp_searches", 1), ("_id", -1)]).limit(50)
                i = 0
                async for profile in profiles:
                    if i == 0:
                        start_id = str(profile['_id'])
                    profiles_data.append(
                        {"id": str(profile['_id']), 'mobile': profile['mobile']})
                    db.profile.update_one({'mobile': profile['mobile']},{"$set": {"whatsapp_searching": 1}})
                    i = i+1
                if len(profiles_data) >= 1:
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
                    send_data_to_worker(worker['ip'], "POST", "check_numbers", dumps(send_data))
                    logger.info(f"sended data to {worker['ip']} worker")
        except:
            pass
        logger.info("end loop")
        sleep(30)

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
    failed_numbers: List

@app.post("/initialize/")
async def initialize(request: Request, db: AsyncIOMotorDatabase = Depends(get_db_instance), authorization: str = Header(None)):
    correct_token = str(os.getenv("TOKEN"))
    if authorization is None or authorization != correct_token:
        raise HTTPException(status_code=401, detail="کاربر احراز هویت نشده است")
    
    client_ip = request.headers.get("worker_ip")
    worker = await db.worker.find_one({"ip": client_ip})
    if not worker:
        user_data = await db.user_data.find_one({"status": 0})
        if user_data:
            worker_data = {
                "ip": client_ip,
                "app_id": user_data.get("_id"),
                "status": 1,
                "reports": [],
                "reports_count": 0
            }
        else:
            worker_data = {
                "ip": client_ip,
                "app_id": 0,
                "status": 2,
                "reports": [],
                "reports_count": 0
            }
        worker = await db.worker.insert_one(worker_data)
        if not worker.acknowledged:
            logger.error("cannot create worker ")
            return JSONResponse(content={"status":False},status_code=500)
        if not user_data:
            logger.error(f"has not any unused user_data for {client_ip} worker")
            return JSONResponse(content={"status":False},status_code=500)
        worker_id = worker.inserted_id
        
    else:
        worker_id = worker.get("_id")
        if worker.get("app_id")==0:
            user_data = await db.user_data.find_one({"status": 0})
            if not user_data:
                logger.error(f"has not any unused user_data for {client_ip} worker")
                return JSONResponse(content={"status":False},status_code=500)
        else:
            user_data = await db.user_data.find_one({"_id": worker.get("app_id"),"status":1})
            if not user_data:
                user_data = await db.user_data.find_one({"status": 0})
                if not user_data:
                    logger.error(f"has not any unused user_data for {client_ip} worker")
                    return JSONResponse(content={"status":False},status_code=500)
        db.worker.update_one(
                        {"_id": worker.get("_id")},
                        {"$set": {"status": 1}}
                    )
    db.user_data.update_one(
                        {"_id": user_data.get("_id")},
                        {"$set": {"status": 1}}
                    )
    return_data = {
        "worker_id": str(worker_id),
        "user_data_path": user_data.get("path"),
    }
    return JSONResponse(content=return_data,status_code=200)

    
@app.get("/send_status/")
async def worker_status(request: Request, db: AsyncIOMotorDatabase = Depends(get_db_instance), status: int = Query(), authorization: str = Header(None)):
    correct_token = str(os.getenv("TOKEN"))
    if authorization is None or authorization != correct_token:
        raise HTTPException(status_code=401, detail="کاربر احراز هویت نشده است")
    
    client_ip = request.headers.get("worker_ip")
    worker = await db.worker.find_one({"ip": client_ip})
    db.worker.update_one(
                        {"_id": worker.get("_id")},
                        {"$set": {"status": status}}
                    )
    return JSONResponse(content={"status":True},status_code=200)
    

@app.post("/results/")
async def recive_results(request: Request, results: WhatsappResults, db: AsyncIOMotorDatabase = Depends(get_db_instance), authorization: str = Header(None)):
    
    correct_token = str(os.getenv("TOKEN"))
    if authorization is None or authorization != correct_token:
        raise HTTPException(status_code=401, detail="کاربر احراز هویت نشده است")

    client_ip = request.headers.get("worker_ip")
    worker = await db.worker.find_one({"ip": client_ip})
    result_data = None
    
    db.worker.update_one(
        {"_id": worker["_id"]},
        {"$set": {"status": 0}, "$push": {'reports': results.report}}
    )
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
            '$push': {'whatsapp': result_data} ,'$set': {"whatsapp_searching": 0}, "$inc": {"whatsapp_searches": 1}}
        db.profile.update_one(filter_query, update_operation)
    
    for failed_number in results.failed_numbers:
        filter_query = {'mobile': failed_number.mobile}
        update_operation = {
        '$set': {"whatsapp_searching": 0}}
        db.profile.update_one(filter_query, update_operation)
   
    return {"status": True}


# UI APIes
@app.get("/dashboard/")
async def dashboard(request: Request, current_user: dict = Depends(get_current_user) ,db: AsyncIOMotorDatabase = Depends(get_db_instance)):
    workers_count = await db.worker.count_documents({})
    user_data_count = await db.user_data.count_documents({})
    profiles_count = await db.profile.count_documents({})
    finded_whatsapp_profiles = await db.profile.count_documents({"whatsapp": {"$elemMatch": {"find": True}}})
    whatsapp_searched_profiles = await db.profile.count_documents({"whatsapp_searches": {"$gt": 0}})
    return {"workers": workers_count ,"user_data": user_data_count, "profiles": profiles_count,"whatsapp_profiles":finded_whatsapp_profiles,"whatsapp_searched_profiles": whatsapp_searched_profiles}

@app.get("/profiles")
async def get_records(request: Request, whatsapp_finded = Query() , current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db_instance), page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    filter={}
    if whatsapp_finded=='true' or whatsapp_finded=='false':
        if whatsapp_finded=="true":
            whatsapp_finded=True
        else:
            whatsapp_finded=False
        filter["whatsapp"]= {"$elemMatch": {"find": whatsapp_finded}}
    skip = (page - 1) * limit
    records = []
    total_count = await db.profile.count_documents(filter)
    async for record in db.profile.find(filter).skip(skip).limit(limit):
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
@app.post("/upload_userdata/")
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

