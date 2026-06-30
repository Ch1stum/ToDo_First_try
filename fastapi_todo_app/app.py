import bcrypt  
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Task

# Create tables
Base.metadata.create_all(bind=engine)
	
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Registration
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@app.post("/register")
def register(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Этот пользователь уже зарегестрирован"}
        )

    if len(password) < 4:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Пароль минимум 4 символа"}
        )
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)
  
    hashed_password_str = hashed_password_bytes.decode('utf-8')

    new_user = User(username=username, hashed_password=hashed_password_str)
    db.add(new_user)
    db.commit()


    user_from_db = db.query(User).filter(User.username == username).first()


    response = RedirectResponse(url="/add-task", status_code=303)
    response.set_cookie(key="user_id", value=str(user_from_db.id), httponly=True)
    return response

# Login
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

@app.post("/login")
def login(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Пользователь не найден"}
        )
    
    password_bytes = password.encode('utf-8')
    hashed_db_bytes = user.hashed_password.encode('utf-8')
    
    if not bcrypt.checkpw(password_bytes, hashed_db_bytes):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Неверный пароль"}
        )
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response

# Logout
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    return response

# Home Page
@app.get("/", response_class=HTMLResponse)
def read_index(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    user = None
    tasks = []

    if user_id:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            tasks = db.query(Task).filter(Task.owner_id == int(user_id)).all()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "tasks": tasks,
            "user": user
        }
    )

# Add Task
@app.post("/tasks")
def add_task(request: Request, 
             title: str = Form(...),
             description: str = Form(None),   
             deadline: str = Form(None),       
             category: str = Form(None), 
             db: Session = Depends(get_db)
             ):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    task = Task(title=title,
                description=description,   
                deadline=deadline,          
                category=category, 
                owner_id=int(user_id))
    db.add(task)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# Toggle Complete
@app.post("/tasks/{task_id}/toggle")
def toggle_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == int(user_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = not task.completed
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# Delete Task
@app.post("/tasks/{task_id}/delete")
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == int(user_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    db.delete(task)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# Update Task
@app.post("/tasks/{task_id}/update")
def update_task(task_id: int, request: Request, title: str = Form(...), db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == int(user_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task.title = title
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/add-task", response_class=HTMLResponse)
def add_task_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="add_task.html",
        context={"user": user}
    )
