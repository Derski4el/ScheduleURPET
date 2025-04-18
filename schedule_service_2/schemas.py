from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr
    phoneNumber: Optional[str] = None
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class NotificationBase(BaseModel):
    message: str

class NotificationCreate(NotificationBase):
    student_id: int

class Notification(NotificationBase):
    id: int
    student_id: int
    class Config:
        orm_mode = True

class Login(BaseModel):
    name: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ScheduleUploadResponse(BaseModel):
    message: str
    schedules_added: int

class ScheduleItem(BaseModel):
    day: str
    time: str
    subject: str
    teacher: str
    group: str
    cabinet: str
