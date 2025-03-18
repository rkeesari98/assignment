from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status

app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

# Mount static files correctly
app.mount("/static", StaticFiles(directory="static"), name="static")

# Firebase Auth Request Adapter

# Set up templates directory
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            print("User Token:", user_token)  # Debugging output
        except ValueError as err:
            error_message = str(err)  # Display error message if token verification fails

    return templates.TemplateResponse(
        "main.html",
        {"request": request, "user_token": user_token, "error_message": error_message},
    )


def get_user(user_token):
    user = firestore_db.collection('users').document(user_token['user_id'])
    if not user.get().exists:
        user_data = {
            'name':'chish',
            'age':273
        }
    firestore_db.collection('users').document(user_token['user_id']).set(user_data)
    
