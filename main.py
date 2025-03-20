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
from driver_service import DriverService
from team_service import TeamService

app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

# Mount static files correctly
app.mount("/static", StaticFiles(directory="static"), name="static")

# Firebase Auth Request Adapter

# Set up templates directory
templates = Jinja2Templates(directory="templates")


def is_logged_in(request:Request):
    id_token = request.cookies.get("token")
    if not id_token:
        return False
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        if user_token:
            return True
    except Exception as e:
        return False

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    return templates.TemplateResponse(
        "main.html",
        {"request": request}
    )


def get_user(user_token):
    user = firestore_db.collection('users').document(user_token['user_id'])
    if not user.get().exists:
        user_data = {
            'name':'chish',
            'age':273
        }
    firestore_db.collection('users').document(user_token['user_id']).set(user_data)

    
#get request to get all drivers
@app.get("/drivers", response_class=HTMLResponse)
def get_drivers(request: Request, 
                attribute: Optional[str] = None, 
                operator: Optional[str] = None, 
                value: Optional[str] = None):
    try:
        user_logged_in = is_logged_in(request)
        drivers, query_info = DriverService.get_drivers(attribute, operator, value)
        
        return templates.TemplateResponse(
            "drivers.html",
            {"request": request, "drivers": drivers, "query_info": query_info,"user_logged_in":user_logged_in}
        )
    
    except ValueError as e:
        return templates.TemplateResponse(
            "drivers.html",
            {"request": request, "drivers": [], "error": str(e)}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "drivers.html",
            {"request": request, "drivers": [], "error": "An error occurred"}
        )


#get request for creating a driver
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


#helper function to get data as pydantic model
def driver_form(name: str = Form(...), age: int = Form(...),total_pole_positions:int = Form(...),
                total_race_wins: int = Form(...),total_points_scored:int = Form(...),
                total_world_titles:int = Form(...),total_fastest_laps:int = Form(...),
                team:str = Form(...)):
    return Driver(name=name, age=age,total_pole_positions=total_pole_positions,total_race_wins=total_race_wins,total_points_scored=total_points_scored,
                  total_world_titles=total_world_titles,total_fastest_laps=total_fastest_laps,team=team
                  )

#post request to create a driver
@app.post("/drivers/create", response_class=RedirectResponse)
def create_driver(driver: Driver = Depends(driver_form)):
    try:
        DriverService.create_driver(driver)
        return RedirectResponse(
            url="/drivers",
            status_code=303
        )
    except Exception as e:
        # Correctly format the error message in the URL
        return RedirectResponse(
            url=f"/drivers/create?error={str(e)}",  # Convert the error to a string
            status_code=303
        )
    

#helper function to get pydantic model for querying 
    
def query_form(
    attribute: str = Form(...),
    operator: str = Form(...),
    value: str = Form(...)):
    return Query(attribute=attribute, operator=operator, value=value)
    
#route for querying the data 
@app.post("/drivers/query", response_class=RedirectResponse)
def query_drivers(query_params: Query = Depends(query_form)):
    # Redirect to GET endpoint with query parameters
    return RedirectResponse(
        url=f"/drivers?attribute={query_params.attribute}&operator={query_params.operator}&value={query_params.value}",
        status_code=303
    )

#post route to update a driver
@app.post("/drivers/{driver_id}", response_class=RedirectResponse)
def update_driver(request:Request,driver_id: str, driver: Driver = Depends(driver_form)):
    try:
        if not is_logged_in(request):
            print("not logged")
            return RedirectResponse(url="/", status_code=303)
        DriverService.update_driver(driver,driver_id)
        return RedirectResponse(
            url="/drivers",
            status_code=303
        )
    except Exception as e:
        # Correct the URL format to properly inject the error message
        return RedirectResponse(
            url=f"/drivers/{driver_id}?error={str(e)}",  # Use f-string to insert error message
            status_code=303
        )


#get request to get driver by id
@app.get("/drivers/{driver_id}", response_class=HTMLResponse)
def get_driver_by_id(driver_id: str, request: Request):
    try:
        data = DriverService.get_driver_by_id(driver_id)
        return templates.TemplateResponse(
            "add-driver.html",
            {"request": request, "driver": data['driver'], "teams": data['teams']}
        )
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=404)
    
#delete route to delete a driver
@app.delete("/drivers/{driver_id}", response_class=HTMLResponse)
def delete_driver(driver_id: str, request: Request):
    try:
        if not is_logged_in(request):
            print("trigger")
            return RedirectResponse(url="/", status_code=303)
        DriverService.delete_driver(driver_id)
        return RedirectResponse(url="/drivers", status_code=303)
    except Exception as e:
        return HTMLResponse(content="Driver not found", status_code=404)
    
#route for comparing drivers
@app.get("/compare_drivers")
async def compare_drivers(request: Request):
    try:
        drivers = DriverService.compare_drivers()
        return templates.TemplateResponse("compare_drivers.html", {
            "request": request,
            "drivers": drivers
        })
    except Exception as e:
        return HTMLResponse(content="Something went wrong please try again", status_code=404) 

#route for comparing drivers
@app.post("/compare_drivers")
async def compare_drivers(request: Request, driver1: str = Form(...), driver2: str = Form(...)):
    
    try:
        result = DriverService.compare_drivers_attributes(driver1,driver2)
        return templates.TemplateResponse("compare_drivers_result.html", {
            "request": request,
            "driver1": result['driver1'],
            "driver2": result['driver2'],
            "comparison": result['comparison']
        })
    except Exception as e:
        return HTMLResponse(content=str(e), status_code=404)  







#team routes

#get route for listing all the teams
@app.get("/teams", response_class=HTMLResponse)
def get_teams(request: Request, 
                attribute: Optional[str] = None, 
                operator: Optional[str] = None, 
                value: Optional[str] = None):
    try:
        user_logged_in = is_logged_in(request)
        teams, query_info = TeamService.get_teams(attribute, operator, value)
        print(query_info)
        return templates.TemplateResponse(
            "teams.html",
            {"request": request, "teams": teams, "query_info": query_info,"user_logged_in":user_logged_in}
        )
    
    except ValueError as e:
        return templates.TemplateResponse(
            "teams.html",
            {"request": request, "teams": [], "error": str(e)}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "teams.html",
            {"request": request, "teams": [], "error": "An error occurred"}
        )
    


# get route for creating the team
@app.get("/teams/create", response_class=HTMLResponse)
async def create_team(request: Request,error: str = None):
    
    try:
        return templates.TemplateResponse(
            "add-team.html",
            {"request": request}
        )
        print("User Token:", user_token)  
    except ValueError as err:
        error_message = str(err)  
        return templates.TemplateResponse(
            "add-team.html",
            {"request": request,"error":error_message}
        )

#helper function for creating pydantic model 
def team_form(name: str = Form(...), year_founded: int = Form(...),total_pole_positions:int = Form(...),
                total_race_wins: int = Form(...),total_constructor_titles:int = Form(...),
                previous_season_position:int = Form(...)):
    return Team(name=name, year_founded=year_founded,total_pole_positions=total_pole_positions,total_race_wins=total_race_wins,total_constructor_titles=total_constructor_titles,
                  previous_season_position=previous_season_position)


#post request for creating team
@app.post("/teams/create", response_class=RedirectResponse)
def create_team(team: Team = Depends(team_form)):
    try:
        TeamService.create_team(team)
        return RedirectResponse(
            url="/teams/",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/teams/create?error={str(e)}",
            status_code=303
        )
    
#route for querying team data
@app.post("/teams/query", response_class=RedirectResponse)
def query_teams(query_params: Query = Depends(query_form)):
    # Redirect to GET endpoint with query parameters
    return RedirectResponse(
        url=f"/teams?attribute={query_params.attribute}&operator={query_params.operator}&value={query_params.value}",
        status_code=303
    )

#post request for updating team data
@app.post("/teams/{team_id}", response_class=RedirectResponse)
def update_team(request:Request,team_id: str, team: Team = Depends(team_form)):
    try:
        if not is_logged_in(request):
            return RedirectResponse(url="/", status_code=303)
        TeamService.update_team(team,team_id)
        return RedirectResponse(
            url="/teams",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/teams/{team_id}?error={str(e)}",  # Use f-string to insert error message
            status_code=303
        )


# get route for getting team by id
@app.get("/teams/{team_id}", response_class=HTMLResponse)
def get_team_by_id(team_id: str, request: Request):
    try:
        team = TeamService.get_team_by_id(team_id)
        return templates.TemplateResponse(
            "add-team.html",
            {"request": request, "team": team['team']}
        )
    except Exception as e:
        return HTMLResponse(content="Team not found", status_code=404)
    
#delete route for deleting team    
@app.delete("/teams/{teams_id}", response_class=HTMLResponse)
def delete_teams(teams_id: str, request: Request):
    try:
        if not is_logged_in(request):
            return RedirectResponse(url="/", status_code=303)
        TeamService.delete_team(teams_id)
        return RedirectResponse(url="/teams", status_code=303)
    except Exception as e:
        return HTMLResponse(content="Team not found", status_code=404)
    

#route for comparing teams
@app.get("/compare_teams")
async def compare_teams_page(request: Request):

    try:
        teams = TeamService.compare_teams()
        return templates.TemplateResponse("compare_teams.html", {
            "request": request,
            "teams": teams
        })
    except Exception as e:
        return HTMLResponse(content="something went wrong",status_code=404)

@app.post("/compare_teams")
async def compare_teams(request: Request, team1: str = Form(...), team2: str = Form(...)):
    
    try:
        result = TeamService.compare_teams_attributes(team1,team2)
        return templates.TemplateResponse("compare_teams_result.html", {
            "request": request,
            "team1": result['team1'],
            "team2": result['team2'],
            "comparison": result['comparison']
        })
    except Exception as e:
        return HTMLResponse(content=str(e),status_code=404)