from pydantic import BaseModel
from typing import Optional, List

# Базовые схемы
class UserBase(BaseModel):
    name: str
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        orm_mode = True

# Схемы для расписания
class ScheduleBase(BaseModel):
    course_id: str
    time: str
    room: str
    teacher_id: int
    group_id: str

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int
    class Config:
        orm_mode = True

# Схемы для уведомлений
class NotificationBase(BaseModel):
    message: str

class NotificationCreate(NotificationBase):
    student_id: int

class Notification(NotificationBase):
    id: int
    student_id: int
    class Config:
        orm_mode = True

# Схемы для аналитики нагрузки преподавателя
class WorkloadAnalytics(BaseModel):
    courses: int
    total_hours: int

# Схемы для аутентификации
class Login(BaseModel):
    name: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Схема для ответа при загрузке расписания
class ScheduleUploadResponse(BaseModel):
    message: str
    schedules_added: int