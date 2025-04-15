from fastapi import FastAPI
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, date
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
load_dotenv()

app = FastAPI()

MONGO_URI=os.getenv("MONGO_URI")


client = AsyncIOMotorClient(MONGO_URI)


try:
    client.admin.command('ping')
    print(" Connected to MongoDB!")
except Exception as e:
    print(e)


db = client["intern_management"]
intern_collection = db["intern"]
tasks_collection = db["Tasks"]
attendance_collection = db["attendance"]


class LoginRequest(BaseModel):
    name: str


class TaskAssignment(BaseModel):
    intern_name: str
    task: str

class TaskCompletion(BaseModel):
    intern_name: str
    task: str



class Intern(BaseModel):
    name: str



@app.post("/add")
async def create_intern(intern: Intern):
    intern_collection.insert_one(intern.dict())
    return {"message": f"Intern {intern.name} added successfully"}




@app.post("/login")
def login(request: LoginRequest):
    login_time = datetime.now()
    today_date = date.today()  
    converted_date = datetime.combine(today_date, datetime.min.time())
    attendance_collection.insert_one({
    "name": request.name,
    "login_time": login_time,
        "logout_time": None,
    "date": converted_date
    })
    return {"message": f"{request.name} logged in at {login_time}"}

@app.post("/logout")
def logout(request: LoginRequest):
    logout_time = datetime.now()
    result = attendance_collection.find_one_and_update(
        {"name": request.name, "logout_time": None},
        {"$set": {"logout_time": logout_time}}
    )
    if result:
        return {"message": f"{request.name} logged out at {logout_time}"}
    else:
        return {"message": "No active login session found for this user."}

@app.post("/assign_task")
def assign_task(data: TaskAssignment):
    tasks_collection.insert_one({
        "intern_name": data.intern_name,
        "task": data.task,
        "status": "assigned"
    })
    return {"message": f"Task assigned to {data.intern_name}"}

@app.post("/complete_task")
def complete_task(data: TaskCompletion):
    result = tasks_collection.update_one(
        {"intern_name": data.intern_name, "task": data.task},
        {"$set": {"status": "completed"}}
    )
    if result.modified_count > 0:
        return {"message": f"{data.intern_name} completed the task"}
    else:
        return {"message": "Task not found or already completed"}
