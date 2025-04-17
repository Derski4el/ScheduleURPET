from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String)  # admin, teacher, student, tech
    password = Column(String)  # Хэшированный пароль

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, index=True)
    time = Column(String)
    room = Column(String)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(String)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)