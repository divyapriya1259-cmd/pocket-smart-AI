from fastapi import FastAPI, Request, Form, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import pathlib
import asyncio
import shutil
app = FastAPI()
templates = Jinja2Templates(directory="templates")
templates = Jinja2Templates(directory="templates")  <- ITHU LINE 13

def get_home_recommendations(obj):    <- ITHA INGA PASTE PANNUGA KELA
    return {"message": f"Home budget {obj.total_budget} success"}
def get_party_recommendations(obj):
    return {"message": f"Party {obj.party_type} success"}
def get_jewelry_recommendations(obj, path):
    return {"message": f"Jewelry {obj.occasion} success"}

# Vercel fix - static folder check  <- ITHU ADUTHA LINE
if pathlib.Path("static").exists():
# Vercel fix - static folder check
if pathlib.Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
# --- Your existing variables ---
users_db = {}
active_sessions = {}
blacklisted_tokens = set()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
async def get_token(request: Request):
    token = request.cookies.get("access_token")
    return token
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = create_access_token({"sub": form_data.username}, timedelta(minutes=30))
    active_sessions[form_data.username] = {"token": token, "last_activity": datetime.utcnow()}
    resp = JSONResponse({"access_token": token})
    resp.set_cookie(key="access_token", value=token, httponly=True, max_age=1800)
    return resp
# --- THIS IS THE FIX FOR "Not Found" ---
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return RedirectResponse(url="/login", status_code=303)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
@app.post("/register")
async def register_user(username: str = Form(...), password: str = Form(...)):
    users_db[username] = {"username": username, "hashed_password": pwd_context.hash(password)}
    return RedirectResponse(url="/login", status_code=303)
@app.post("/logout")
async def logout(request: Request):
    token = await get_token(request)
    if token:
        blacklisted_tokens.add(token)
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("access_token")
    return resp
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
@app.post("/home-budget")
async def home_budget(request: Request):
    data = await request.json()
    obj = type('obj', (), {'total_budget': data.get('budget'), 'room_type': data.get('room_type')})()
    return get_home_recommendations(obj)
@app.post("/party-budget")
async def party_budget(request: Request):
    data = await request.json()
    obj = type('obj', (), {'total_budget': data.get('budget'), 'party_type': data.get('party_type'), 'num_guests': data.get('guests')})()
    return get_party_recommendations(obj)
@app.post("/jewelry-budget")
async def jewelry_budget(total_budget: float = Form(...), occasion: str = Form(...), image: UploadFile = File(None)):
    path = None
    obj = type('obj', (), {'total_budget': total_budget, 'occasion': occasion})()
    return get_jewelry_recommendations(obj, path)
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})
@app.on_event("startup")
async def startup():
    async def cleanup():
        while True:
            now = datetime.utcnow()
            expired = [u for u,s in active_sessions.items() if (now - s["last_activity"]).total_seconds() > 1800]
            for u in expired:
                del active_sessions[u]
            await asyncio.sleep(300)
    asyncio.create_task(cleanup())