# models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)  # было name, затем email, теперь username
    email = Column(String, unique=True, index=True, nullable=False)  # было email, затем username, теперь снова email
    phoneNumber = Column(String, nullable=True)  # уже переименовано ранее
    role = Column(String)  # admin, teacher, student, tech
    password = Column(String)

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
