from typing import Optional
from fastapi import FastAPI, Request,Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from models import Driver, Team,Query
import starlette.status as status
from fastapi.responses import RedirectResponse

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
    

@app.get("/drivers/create", response_class=HTMLResponse)
async def create_driver(request: Request,error: str = None):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            print("User Token:", user_token)  # Debugging output
        except ValueError as err:
            error_message = str(err)  # Display error message if token verification fails
    query = firestore_db.collection("teams")
    teams = [doc.to_dict() for doc in query.stream()]
    return templates.TemplateResponse(
        "add-driver.html",
        {"request": request,"error":error,"teams":teams}
    )

def driver_form(name: str = Form(...), age: int = Form(...),total_pole_positions:int = Form(...),
                total_race_wins: int = Form(...),total_points_scored:int = Form(...),
                total_world_titles:int = Form(...),total_fastest_laps:int = Form(...),
                team:str = Form(...)):
    return Driver(name=name, age=age,total_pole_positions=total_pole_positions,total_race_wins=total_race_wins,total_points_scored=total_points_scored,
                  total_world_titles=total_world_titles,total_fastest_laps=total_fastest_laps,team=team,)

@app.post("/drivers/create", response_class=RedirectResponse)
def create_driver(driver: Driver = Depends(driver_form)):
    print(driver)
    existing_driver = firestore_db.collection('drivers').where('name', '==', driver.name).limit(1).get() 
    if len(existing_driver) > 0:
        return RedirectResponse(
            url="/drivers/create?error=Driver%20name%20exists",
            status_code=303
        )
    if driver.age < 16:
        return RedirectResponse(
            url="/drivers/create?error=Age%20must%20be%20greater%20than%20 16",
            status_code=303
        )
    if driver.total_pole_positions < 0:
        return RedirectResponse(
            url="/drivers/create?error=total_pole_positions%20must%20be%20positive",
            status_code=303
        )
    if driver.total_race_wins < 0:
        return RedirectResponse(
            url="/drivers/create?error=total_race_wins%20must%20be%20positive",
            status_code=303
        )
    if driver.total_points_scored < 0:
        return RedirectResponse(
            url="/drivers/create?error=total_points_scored%20must%20be%20positive",
            status_code=303
        )
    if driver.total_world_titles < 0:
        return RedirectResponse(
            url="/drivers/create?error=total_world_titles%20must%20be%20positive",
            status_code=303
        )
    if driver.total_fastest_laps < 0:
        return RedirectResponse(
            url="/drivers/create?error=total_fastest_laps%20must%20be%20positive",
            status_code=303
        )
    
    # does_team_exist = firestore_db.collection('teams').where('name','==',driver.team).limit(1).get()
    # if len(does_team_exist)<=0:
    #    return RedirectResponse(
    #         url="/drivers/create?error=team%20name%20does%20not%20exists",
    #         status_code=303
    #     )
    
    firestore_db.collection('drivers').add(driver.dict())
    return RedirectResponse(
        url="/drivers/",
        status_code=303
    )

# @app.get("/drivers",response_class=HTMLResponse)
# def get_drivers(request:Request):
#     drivers = [doc.to_dict() for doc in firestore_db.collection('drivers').stream()]
#     return templates.TemplateResponse(
#         "drivers.html",
#         {"request": request, "drivers": drivers}
#     )










@app.get("/teams/create", response_class=HTMLResponse)
async def create_team(request: Request,error: str = None):
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
        "add-team.html",
        {"request": request,"error":error}
    )

def team_form(name: str = Form(...), year_founded: int = Form(...),total_pole_positions:int = Form(...),
                total_race_wins: int = Form(...),total_constructor_titles:int = Form(...),
                previous_season_position:int = Form(...)):
    return Team(name=name, year_founded=year_founded,total_pole_positions=total_pole_positions,total_race_wins=total_race_wins,total_constructor_titles=total_constructor_titles,
                  previous_season_position=previous_season_position)

@app.post("/teams/create", response_class=RedirectResponse)
def create_team(team: Team = Depends(team_form)):
    print(team)
    existing_team = firestore_db.collection('teams').where('name', '==', team.name).limit(1).get() 
    if len(existing_team) > 0:
        return RedirectResponse(
            url="/teams/create?error=Team%20name%20exists",
            status_code=303
        )
    if team.year_founded < 1900 or team.year_founded>2025:
        return RedirectResponse(
            url="/teams/create?error=team%20founded%20must%20be%20in%20between%20 1900%20to%20 2025",
            status_code=303
        )
    if team.total_pole_positions < 0:
        return RedirectResponse(
            url="/teams/create?error=total_pole_positions%20must%20be%20positive",
            status_code=303
        )
    if team.total_race_wins < 0:
        return RedirectResponse(
            url="/teams/create?error=total_race_wins%20must%20be%20positive",
            status_code=303
        )
    if team.total_constructor_titles < 0:
        return RedirectResponse(
            url="/teams/create?error=total_constructor_titles%20must%20be%20positive",
            status_code=303
        )
    if team.previous_season_position < 0:
        return RedirectResponse(
            url="/teams/create?error=previous_season_position%20must%20be%20positive",
            status_code=303
        )
    
    firestore_db.collection('teams').add(team.dict())
    return RedirectResponse(
        url="/teams/",
        status_code=303
    )

# @app.get("/teams",response_class=HTMLResponse)
# def get_drivers(request:Request):
#     teams = [doc.to_dict() for doc in firestore_db.collection('teams').stream()]
#     return templates.TemplateResponse(
#         "teams.html",
#         {"request": request, "teams": teams}
#     )


def query_form(
    attribute: str = Form(...),
    operator: str = Form(...),
    value: str = Form(...)
):
    return Query(attribute=attribute, operator=operator, value=value)

@app.get("/teams", response_class=HTMLResponse)
def get_teams(request: Request, 
              attribute: Optional[str] = None, 
              operator: Optional[str] = None, 
              value: Optional[str] = None):
    query = firestore_db.collection('teams')
    query_info = None
    
    # Apply filter if all parameters are provided
    if attribute and operator and value:
        # Convert value to proper type based on attribute
        if attribute == "name":
            typed_value = value  # Keep as string
        else:
            # Convert to int for numeric fields
            try:
                typed_value = int(value)
            except ValueError:
                teams = []
                return templates.TemplateResponse(
                    "teams.html",
                    {"request": request, "teams": teams, "error": f"Invalid numeric value: {value}"}
                )
        
        # Map operator to Firestore comparison
        operator_map = {
            "eq": "==",
            "gt": ">",
            "lt": "<",
            "gte": ">=",
            "lte": "<="
        }
        
        if operator in operator_map:
            query = query.where(attribute, operator_map[operator], typed_value)
            query_info = f"{attribute} {operator_map[operator]} {value}"
    
    # Execute query
    teams = [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]

    
    return templates.TemplateResponse(
        "teams.html",
        {"request": request, "teams": teams, "query_info": query_info}
    )

@app.post("/teams/query", response_class=RedirectResponse)
def query_teams(query_params: Query = Depends(query_form)):
    # Redirect to GET endpoint with query parameters
    return RedirectResponse(
        url=f"/teams?attribute={query_params.attribute}&operator={query_params.operator}&value={query_params.value}",
        status_code=303
    )

@app.get("/drivers",response_class=HTMLResponse)
def get_drivers(request:Request,
                attribute: Optional[str] = None, 
              operator: Optional[str] = None, 
              value: Optional[str] = None):
    query = firestore_db.collection('drivers')
    query_info = None
    
    # Apply filter if all parameters are provided
    if attribute and operator and value:
        # Convert value to proper type based on attribute
        if attribute == "name" or attribute=="team":
            typed_value = value  # Keep as string
        else:
            # Convert to int for numeric fields
            try:
                typed_value = int(value)
            except ValueError:
                drivers = []
                return templates.TemplateResponse(
                    "drivers.html",
                    {"request": request, "drivers": drivers, "error": f"Invalid numeric value: {value}"}
                )
        
        # Map operator to Firestore comparison
        operator_map = {
            "eq": "==",
            "gt": ">",
            "lt": "<",
            "gte": ">=",
            "lte": "<="
        }
        
        if operator in operator_map:
            query = query.where(attribute, operator_map[operator], typed_value)
            query_info = f"{attribute} {operator_map[operator]} {value}"
    
    drivers = [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]

    # Execute query
    
    return templates.TemplateResponse(
        "drivers.html",
        {"request": request, "drivers": drivers, "query_info": query_info}
    )

@app.post("/drivers/query", response_class=RedirectResponse)
def query_drivers(query_params: Query = Depends(query_form)):
    # Redirect to GET endpoint with query parameters
    return RedirectResponse(
        url=f"/drivers?attribute={query_params.attribute}&operator={query_params.operator}&value={query_params.value}",
        status_code=303
    )

@app.get("/drivers/{driver_id}", response_class=HTMLResponse)
def get_driver_by_id(driver_id: str, request: Request):
    doc_ref = firestore_db.collection("drivers").document(driver_id)
    doc = doc_ref.get()

    if not doc.exists:
        return HTMLResponse(content="Driver not found", status_code=404)

    driver = {"id": doc.id, **doc.to_dict()}
    query = firestore_db.collection("teams")
    teams = [doc.to_dict() for doc in query.stream()]
    
    return templates.TemplateResponse(
        "add-driver.html",
        {"request": request, "driver": driver,"teams":teams}
    )


@app.post("/drivers/{driver_id}", response_class=RedirectResponse)
def update_driver(driver_id: str, driver: Driver = Depends(driver_form)):
    print(driver)
    driver_ref = firestore_db.collection("drivers").document(driver_id)
    existing_driver = driver_ref.get()
    
    if not existing_driver.exists:
        return RedirectResponse(
            url="/drivers?error=Driver%20not%20found",
            status_code=303
        )
    if driver.age < 16:
        return RedirectResponse(
            url="/drivers/{}/edit?error=Age%20must%20be%20greater%20than%2016".format(driver_id),
            status_code=303
        )
    if driver.total_pole_positions < 0:
        return RedirectResponse(
            url="/drivers/{}/edit?error=total_pole_positions%20must%20be%20positive".format(driver_id),
            status_code=303
        )
    if driver.total_race_wins < 0:
        return RedirectResponse(
            url="/drivers/{}/edit?error=total_race_wins%20must%20be%20positive".format(driver_id),
            status_code=303
        )
    if driver.total_points_scored < 0:
        return RedirectResponse(
            url="/drivers/{}/edit?error=total_points_scored%20must%20be%20positive".format(driver_id),
            status_code=303
        )
    if driver.total_world_titles < 0:
        return RedirectResponse(
            url="/drivers/{}/edit?error=total_world_titles%20must%20be%20positive".format(driver_id),
            status_code=303
        )
    if driver.total_fastest_laps < 0:
        return RedirectResponse(
            url="/drivers/{}/edit?error=total_fastest_laps%20must%20be%20positive".format(driver_id),
            status_code=303
        )
    
    driver_ref.update(driver.dict())
    
    return RedirectResponse(
        url="/drivers",
        status_code=303
    )

@app.delete("/drivers/{driver_id}", response_class=HTMLResponse)
def delete_driver(driver_id: str, request: Request):
    doc_ref = firestore_db.collection("drivers").document(driver_id)
    doc = doc_ref.get()

    if not doc.exists:
        return HTMLResponse(content="Driver not found", status_code=404)

    # Proceed to delete the driver
    doc_ref.delete()

    # Redirect to the /drivers page after deleting
    return RedirectResponse(url="/drivers", status_code=303)










@app.get("/teams/{team_id}", response_class=HTMLResponse)
def get_team_by_id(team_id: str, request: Request):
    doc_ref = firestore_db.collection("teams").document(team_id)
    doc = doc_ref.get()

    if not doc.exists:
        return HTMLResponse(content="Team not found", status_code=404)

    team = {"id": doc.id, **doc.to_dict()}
    
    return templates.TemplateResponse(
        "add-team.html",
        {"request": request, "team": team}
    )


@app.post("/teams/{team_id}", response_class=RedirectResponse)
def update_team(team_id: str, team: Team = Depends(team_form)):
    print(team)
    teams_ref = firestore_db.collection("teams").document(team_id)
    existing_team = teams_ref.get()
    
    if not existing_team.exists:
        return RedirectResponse(
            url="/teams?error=Team%20not%20found",
            status_code=303
        )
    if team.year_founded < 1900 or team.year_founded>2025:
        return RedirectResponse(
            url="/teams/create?error=team%20founded%20must%20be%20in%20between%20 1900%20to%20 2025",
            status_code=303
        )
    if team.total_pole_positions < 0:
        return RedirectResponse(
            url="/teams/create?error=total_pole_positions%20must%20be%20positive",
            status_code=303
        )
    if team.total_race_wins < 0:
        return RedirectResponse(
            url="/teams/create?error=total_race_wins%20must%20be%20positive",
            status_code=303
        )
    if team.total_constructor_titles < 0:
        return RedirectResponse(
            url="/teams/create?error=total_constructor_titles%20must%20be%20positive",
            status_code=303
        )
    if team.previous_season_position < 0:
        return RedirectResponse(
            url="/teams/create?error=previous_season_position%20must%20be%20positive",
            status_code=303
        )
    
    teams_ref.update(team.dict())
    
    return RedirectResponse(
        url="/teams",
        status_code=303
    )

@app.delete("/teams/{teams_id}", response_class=HTMLResponse)
def delete_teams(teams_id: str, request: Request):
    doc_ref = firestore_db.collection("teams").document(teams_id)
    doc = doc_ref.get()

    if not doc.exists:
        return HTMLResponse(content="Team not found", status_code=404)

    # Proceed to delete the driver
    doc_ref.delete()

    # Redirect to the /drivers page after deleting
    return RedirectResponse(url="/teams", status_code=303)