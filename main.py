# main.py (Production Version)

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base class for the applications
class BaseApp:
    def __init__(self, app: FastAPI, templates: Jinja2Templates):
        self.app = app
        self.templates = templates
        self.setup_routes()

    def setup_routes(self):
        raise NotImplementedError("Subclasses should implement this method")

# User Application
class UserApp(BaseApp):
    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def user_dashboard(request: Request):
            logger.info("User dashboard accessed")
            return self.templates.TemplateResponse("user_dashboard.html", {"request": request})

# Admin Application
class AdminApp(BaseApp):
    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def admin_dashboard(request: Request):
            logger.info("Admin dashboard accessed")
            return self.templates.TemplateResponse("admin_dashboard.html", {"request": request})

# Main Application
class MainApp:
    def __init__(self):
        self.app = FastAPI()
        self.templates = Jinja2Templates(directory="templates")
        self.configure_middlewares()
        self.mount_static()
        self.setup_routes()
        self.user_app = FastAPI()
        self.admin_app = FastAPI()
        self.setup_sub_apps()

    def configure_middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

    def mount_static(self):
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def home_page(request: Request):
            logger.info("Home page accessed")
            return self.templates.TemplateResponse("home.html", {"request": request})

        @self.app.get("/login", response_class=HTMLResponse)
        async def login_page(request: Request):
            logger.info("Login page accessed")
            return self.templates.TemplateResponse("login.html", {"request": request})

        @self.app.post("/login", response_class=HTMLResponse)
        async def login(request: Request, mobile: str = Form(...), password: str = Form(...), user_type: str = Form("user")):
            logger.info(f"Login attempt with mobile: {mobile}, user_type: {user_type}")
            if user_type == "user" and mobile == "1234567890" and password == "password":
                logger.info("User login successful")
                return RedirectResponse(url="/user/home.html", status_code=303)
            elif user_type == "admin" and mobile == "admin" and password == "password":
                logger.info("Admin login successful")
                return RedirectResponse(url="/admin", status_code=303)
            else:
                logger.warning("Invalid login attempt")
                return self.templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    def setup_sub_apps(self):
        user_templates = Jinja2Templates(directory="templates/user")
        admin_templates = Jinja2Templates(directory="templates/admin")

        user_app_instance = UserApp(self.user_app, user_templates)
        admin_app_instance = AdminApp(self.admin_app, admin_templates)

        self.app.mount("/user", user_app_instance.app)
        self.app.mount("/admin", admin_app_instance.app)

# Run the application
main_app = MainApp()
app = main_app.app

if __name__ == "__main__":
    logger.info("Starting server on 0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)