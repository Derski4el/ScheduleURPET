import os
from fastapi import FastAPI, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import models
from fastapi.middleware.cors import CORSMiddleware
import schemas
from database import engine, get_db
from auth import verify_password, get_password_hash, create_access_token, get_current_user, get_current_user_with_role
import pandas as pd

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Эндпоинт для регистрации
@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверяем, не зарегистрирован ли email
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    existing_username = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)

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

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.role)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.put("/admin/users/{user_id}/", response_model=schemas.User, dependencies=[Depends(get_current_user_with_role("admin"))])
def manage_user(user_id: int, user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if db_user:
        if db_user.email != user_data.email:
            existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        if db_user.username != user_data.username:
            existing_username = db.query(models.User).filter(models.User.username == user_data.username).first()
            if existing_username:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
        db_user.username = user_data.username
        db_user.email = user_data.email
        db_user.phoneNumber = user_data.phoneNumber
        db_user.role = user_data.role
        db_user.password = get_password_hash(user_data.password) if user_data.password else db_user.password
    else:
        existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        existing_username = db.query(models.User).filter(models.User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
        db_user = models.User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            phoneNumber=user_data.phoneNumber,
            role=user_data.role,
            password=get_password_hash(user_data.password)
        )
        db.add(db_user)
    
    db.commit()
    db.refresh(db_user)
    return db_user

CSV_PATH = "all_groups_schedule.csv"

if not os.path.exists(CSV_PATH):
    raise RuntimeError("Файл all_groups_schedule.csv не найден")

df = pd.read_csv(CSV_PATH)
df.columns = [col.lower().strip() for col in df.columns]

if "id" not in df.columns:
    df.insert(0, "id", range(1, len(df) + 1))
    df.to_csv(CSV_PATH, index=False)

df.set_index("id", inplace=True)


def clean_result(result: pd.DataFrame):
    return result.where(pd.notnull(result), None).to_dict(orient="records")

@app.get("/by-teacher")
def get_by_teacher(name: str = Query(..., description="ФИО преподавателя")):
    result = df[df['teacher'].str.contains(name, case=False, na=False)]
    if result.empty:
        raise HTTPException(status_code=404, detail="Пары не найдены")
    return JSONResponse(content=clean_result(result))

@app.get("/by-cabinet")
def get_by_cabinet(room: str = Query(..., description="Номер кабинета")):
    result = df[df['cabinet'].astype(str).str.contains(room, case=False, na=False)]
    if result.empty:
        raise HTTPException(status_code=404, detail="Пары не найдены")
    return JSONResponse(content=clean_result(result))

@app.get("/by-group")
def get_by_group(group: str = Query(..., description="Название группы")):
    result = df[df['group'].str.contains(group, case=False, na=False)]
    if result.empty:
        raise HTTPException(status_code=404, detail="Пары не найдены")
    return JSONResponse(content=clean_result(result))


@app.put("/update/{item_id}")
def update_lesson(item_id: int, item: schemas.ScheduleItem):
    if item_id not in df.index:
        raise HTTPException(404, "Пара не найдена")
    df.loc[item_id] = item.dict()
    df.to_csv(CSV_PATH)
    return {"message": f"Пара с id={item_id} обновлена"}

@app.post("/add")
def add_lesson(item: schemas.ScheduleItem):
    new_id = df.index.max() + 1 if not df.empty else 1
    df.loc[new_id] = item.dict()
    df.to_csv(CSV_PATH)
    return {"message": f"Добавлена новая пара с id={new_id}"}

@app.delete("/delete/{item_id}")
def delete_lesson(item_id: int):
    if item_id not in df.index:
        raise HTTPException(404, "Пара не найдена")
    df.drop(item_id, inplace=True)
    df.to_csv(CSV_PATH)
    return {"message": f"Пара с id={item_id} удалена"}
