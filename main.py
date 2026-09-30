import os, asyncio, shutil
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, Depends, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from gemini_utils import get_home_recommendations, get_party_recommendations, get_jewelry_recommendations

load_dotenv()
app = FastAPI(title="PocketSmart AI")
templates = Jinja2Templates(directory="templates")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SECRET_KEY = os.getenv("SECRET_KEY","ram_secret_123")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users_db, active_sessions, blacklisted_tokens = {}, {}, set()

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + (expires_delta or timedelta(minutes=15))})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_token(request: Request):
    return request.cookies.get("access_token")

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
    if token: blacklisted_tokens.add(token)
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
    if image and image.filename:
        path = f"static/uploads/{image.filename}"
        with open(path, "wb") as f: shutil.copyfileobj(image.file, f)
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
            for u in expired: del active_sessions[u]
            await asyncio.sleep(300)
    asyncio.create_task(cleanup())