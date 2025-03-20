from models import Driver
from typing import Dict, List, Optional, Union
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


firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()


class TeamService:
    @staticmethod
    def create_team(team:Team)->None:
        existing_team = firestore_db.collection('teams').where('name', '==', team.name).limit(1).get() 
        if len(existing_team) > 0:
            raise Exception("Team name already exists.Please use different name")
        if team.year_founded < 1900 or team.year_founded>2025:
            raise Exception("Year must be greater than 1900 and less than 2025")
        if team.total_pole_positions < 0:
            raise Exception("total pole positions must be greater than zero")
        if team.total_race_wins < 0:
            raise Exception("Toatl race wins must be greater than zero")
        if team.total_constructor_titles < 0:
            raise Exception("Total constructor title must be greater than zero")
        if team.previous_season_position < 0:
            raise Exception("previous season position must be greater than zero")
        
        firestore_db.collection('teams').add(team.dict())


    @staticmethod
    def update_team(team:Team,team_id:str)->None:
        teams_ref = firestore_db.collection("teams").document(team_id)
        existing_team = teams_ref.get()
        if not existing_team.exists:
            raise Exception("Team not found")
        if team.year_founded < 1900 or team.year_founded>2025:
            raise Exception("Year must be greater than 1900 and less than 2025")
        if team.total_pole_positions < 0:
            raise Exception("total pole positions must be greater than zero")
        if team.total_race_wins < 0:
            raise Exception("Toatl race wins must be greater than zero")
        if team.total_constructor_titles < 0:
            raise Exception("Total constructor title must be greater than zero")
        if team.previous_season_position < 0:
            raise Exception("previous season position must be greater than zero")
        team_ref = firestore_db.collection("teams").document(team_id)
        team_ref.update(team.dict())


    @staticmethod
    def delete_team(team_id:str)->None:
        doc_ref = firestore_db.collection("teams").document(team_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise Exception("team not found")
        doc_ref.delete()

    @staticmethod
    def get_team_by_id(team_id:str)->dict:
        doc_ref = firestore_db.collection("teams").document(team_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise Exception("Team not found")

        team = {"id": doc.id, **doc.to_dict()}
        return {"team": team}
    
    @staticmethod
    def get_teams(attribute: Optional[str] = None, 
                    operator: Optional[str] = None, 
                    value: Optional[str] = None) -> List[Dict[str, Union[str, int]]]:
        
        query = firestore_db.collection('teams')
        query_info = None
        
        if attribute and operator and value:
            if attribute == "name" or attribute == "team":
                typed_value = value  
            else:
                
                try:
                    typed_value = int(value)
                except ValueError:
                    raise ValueError(f"Invalid numeric value: {value}")
            
            
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
        
        
        teams = [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]
        
        return teams, query_info
