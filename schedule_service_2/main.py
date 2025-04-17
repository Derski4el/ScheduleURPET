from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import models
from stats import parse_schedule
from fastapi.middleware.cors import CORSMiddleware
import schemas
from database import engine, get_db
from auth import verify_password, get_password_hash, create_access_token, get_current_user, get_current_user_with_role

# Создание таблиц в базе данных
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:5173",  # Разрешаем только фронтенд на этом порту
    "http://127.0.0.1:5173",  # Для других случаев, если вы используете разные порты
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешаем доступ только с этих доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP-методы (GET, POST, PUT, DELETE и т. д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Эндпоинт для регистрации
@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверяем, не зарегистрирован ли email
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Проверяем уникальность username
    existing_username = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    # Создаем нового пользователя с email и phoneNumber
    db_user = models.User(
        username=user.username,
        email=user.email,
        phoneNumber=user.phoneNumber,
        role=user.role,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Эндпоинт для логина
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Эндпоинт для получения расписания
@app.get("/ras{group}")
def get_schedule(group):
    file_path = "14.04 - 18.04-1.xlsx"
    json = parse_schedule(group_name=group, file_path=file_path)
    return json

# Администрация: Управление расписанием и пользователями
@app.post("/admin/users/", response_model=schemas.User, dependencies=[Depends(get_current_user_with_role("admin"))])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверяем уникальность email
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Проверяем уникальность username
    existing_username = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    db_user = models.User(
        username=user.username,
        email=user.email,
        phoneNumber=user.phoneNumber,
        role=user.role,
        password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/admin/schedules/", response_model=schemas.Schedule, dependencies=[Depends(get_current_user_with_role("admin"))])
def create_schedule(schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)):
    db_schedule = models.Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

# Студенты: Просмотр расписания группы и уведомления
@app.get("/students/{group_id}/schedules/", response_model=List[schemas.Schedule], dependencies=[Depends(get_current_user_with_role("student"))])
def get_group_schedule(group_id: str, db: Session = Depends(get_db)):
    schedules = db.query(models.Schedule).filter(models.Schedule.group_id == group_id).all()
    if not schedules:
        raise HTTPException(status_code=404, detail="No schedules found for this group")
    return schedules

@app.post("/students/notifications/", response_model=schemas.Notification, dependencies=[Depends(get_current_user_with_role("student"))])
def create_notification(notification: schemas.NotificationCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id != notification.student_id:
        raise HTTPException(status_code=403, detail="Not authorized to create notification for this student")
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@app.get("/students/{student_id}/notifications/", response_model=List[schemas.Notification], dependencies=[Depends(get_current_user_with_role("student"))])
def get_notifications(student_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these notifications")
    return db.query(models.Notification).filter(models.Notification.student_id == student_id).all()

# @app.get("/admin/schedules/", response_model=List[schemas.Schedule], dependencies=[Depends(get_current_user_with_role("admin"))])
# def get_all_schedules(db: Session = Depends(get_db)):
#     return db.query(models.Schedule).all()

# # Преподаватели: Просмотр расписания и аналитика нагрузки
# @app.get("/teachers/{teacher_id}/schedules/", response_model=List[schemas.Schedule], dependencies=[Depends(get_current_user_with_role("teacher"))])
# def get_teacher_schedule(teacher_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     if current_user.id != teacher_id:
#         raise HTTPException(status_code=403, detail="Not authorized to view this schedule")
#     schedules = db.query(models.Schedule).filter(models.Schedule.teacher_id == teacher_id).all()
#     if not schedules:
#         raise HTTPException(status_code=404, detail="No schedules found for this teacher")
#     return schedules

# @app.get("/teachers/{teacher_id}/workload/", response_model=schemas.WorkloadAnalytics, dependencies=[Depends(get_current_user_with_role("teacher"))])
# def get_workload_analytics(teacher_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     if current_user.id != teacher_id:
#         raise HTTPException(status_code=403, detail="Not authorized to view this workload")
#     schedules = db.query(models.Schedule).filter(models.Schedule.teacher_id == teacher_id).all()
#     course_count = len(schedules)
#     total_hours = course_count * 2  # Предполагаем 2 часа на курс
#     return {"courses": course_count, "total_hours": total_hours}

# # Эндпоинт для загрузки Excel с расписанием
# @app.post("/admin/upload-schedule/", response_model=schemas.ScheduleUploadResponse, dependencies=[Depends(get_current_user_with_role("admin"))])
# async def upload_schedule(file: UploadFile = File(...), db: Session = Depends(get_db)):
#     schedules_added = parse_schedule_excel(file, db)
#     return {"message": "Schedule uploaded successfully", "schedules_added": schedules_added}


# # Технический персонал: Поддержка системы и резервное копирование
# @app.get("/tech/maintenance/", dependencies=[Depends(get_current_user_with_role("tech"))])
# def perform_maintenance():
#     return {"message": "System maintenance completed"}

# @app.get("/tech/backup/", dependencies=[Depends(get_current_user_with_role("tech"))])
# def create_backup(db: Session = Depends(get_db)):
#     users = db.query(models.User).count()
#     schedules = db.query(models.Schedule).count()
#     notifications = db.query(models.Notification).count()
#     return {"message": f"Backup created with {users} users, {schedules} schedules, {notifications} notifications"}
