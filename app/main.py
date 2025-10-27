import os
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import secrets

from app.auth import get_current_user, oauth_login, oauth_callback, logout
from app.drive import get_drive_service, read_file_from_drive, save_to_drive
from app.generator import generate_study_guide

# Load environment variables
load_dotenv()

app = FastAPI(title="Bible Study Generator")

# Add session middleware
SESSION_SECRET = os.getenv("SESSION_SECRET_KEY", secrets.token_urlsafe(32))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=604800)  # 7 days

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: dict = Depends(get_current_user)):
    """Main application page - requires authentication"""
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        }
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page with Google OAuth"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth flow"""
    return await oauth_login(request)


@app.get("/auth/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    return await oauth_callback(request)


@app.get("/auth/logout")
async def logout_route(request: Request):
    """Logout user"""
    return await logout(request)


@app.get("/api/access-token")
async def get_access_token(request: Request, user: dict = Depends(get_current_user)):
    """Get OAuth access token for Google Picker API"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        creds_data = request.session.get("credentials")
        if not creds_data or not creds_data.get("token"):
            raise HTTPException(status_code=401, detail="No access token found")

        return JSONResponse({
            "access_token": creds_data["token"]
        })

    except Exception as e:
        print(f"Error getting access token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/list-files")
async def list_files(request: Request, user: dict = Depends(get_current_user)):
    """List all .txt files from user's Google Drive"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        from app.drive import list_text_files
        drive_service = get_drive_service(request)
        files = list_text_files(drive_service)

        return JSONResponse({
            "success": True,
            "files": files
        })

    except Exception as e:
        print(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_guide(
    request: Request,
    series_title: str = Form(...),
    target_audience: str = Form(...),
    model: str = Form(...),
    file_ids: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """Generate Bible study guide from selected Drive files"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Parse file IDs (comma-separated)
        file_id_list = [fid.strip() for fid in file_ids.split(",") if fid.strip()]

        if not file_id_list:
            raise HTTPException(status_code=400, detail="No files selected")

        if len(file_id_list) > 8:
            raise HTTPException(status_code=400, detail="Maximum 8 sermon files allowed")

        # Get Drive service
        drive_service = get_drive_service(request)

        # Read sermon files from Drive (sorted alphabetically by filename)
        sermons = []
        for file_id in file_id_list:
            file_metadata = drive_service.files().get(fileId=file_id, fields="name").execute()
            file_content = read_file_from_drive(drive_service, file_id)
            sermons.append({
                "filename": file_metadata["name"],
                "content": file_content
            })

        # Sort alphabetically by filename (handles "## 01, 02..." pattern)
        sermons.sort(key=lambda x: x["filename"])

        # Generate study guide
        study_guide_content = await generate_study_guide(
            sermons=sermons,
            series_title=series_title,
            target_audience=target_audience,
            model=model
        )

        # Save to Google Drive
        filename = f"{series_title}_Study_Guide.md"
        folder_id = os.getenv("STUDY_GUIDE_OUTPUT_FOLDER_ID")

        # If folder_id not set, save to root of Drive
        if not folder_id or folder_id == "None":
            folder_id = None  # None means root folder in Drive API

        file_url = save_to_drive(
            drive_service=drive_service,
            filename=filename,
            content=study_guide_content,
            folder_id=folder_id
        )

        return JSONResponse({
            "success": True,
            "message": "Study guide generated successfully!",
            "file_url": file_url,
            "filename": filename
        })

    except Exception as e:
        # Log error for debugging
        print(f"Error generating study guide: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
