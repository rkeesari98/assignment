from models import Driver
from typing import Dict, List, Optional, Union
from google.auth.transport import requests
from google.cloud import firestore
from models import Driver, Team,Query

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()
class DriverService:
    @staticmethod
    def create_driver(driver: Driver)->None:
        existing_driver = firestore_db.collection('drivers').where(field_path='name', op_string='==', value=driver.name).limit(1).get()
        if len(existing_driver) > 0:
            raise Exception("driver name already exists please use different one")
        if driver.age < 16:
            raise Exception("age must be 16 years old")
        if driver.total_pole_positions < 0:
            raise Exception("total pole positions cannot be less than 0")
        if driver.total_race_wins < 0:
            raise Exception("total race wins cannot be less than 0")
        if driver.total_points_scored < 0:
            raise Exception("toatl points scored cannot be less than 0")
        if driver.total_world_titles < 0:
            raise Exception("toatl world titles cannot be less than 0")
        if driver.total_fastest_laps < 0:
            raise Exception("toatl fastest laps cannot be less than 0")
        does_team_exist = firestore_db.collection('teams').where('name','==',driver.team).limit(1).get()
        if len(does_team_exist)<=0:
            raise Exception("create team name before assigning it to a driver")
        firestore_db.collection('drivers').add(driver.dict())
    
    @staticmethod
    def update_driver(driver:Driver,driver_id:str)->None:
        if driver.age < 16:
            raise Exception("age must be 16 years old")
        if driver.total_pole_positions < 0:
            raise Exception("total pole positions cannot be less than 0")
        if driver.total_race_wins < 0:
            raise Exception("total race wins cannot be less than 0")
        if driver.total_points_scored < 0:
            raise Exception("toatl points scored cannot be less than 0")
        if driver.total_world_titles < 0:
            raise Exception("toatl world titles cannot be less than 0")
        if driver.total_fastest_laps < 0:
            raise Exception("toatl fastest laps cannot be less than 0")
        does_team_exist = firestore_db.collection('teams').where('name','==',driver.team).limit(1).get()
        if len(does_team_exist)<=0:
            raise Exception("create team name before assigning it to a driver")
        driver_ref = firestore_db.collection("drivers").document(driver_id)
        driver_ref.update(driver.dict())
    
    @staticmethod
    def delete_driver(driver_id:str)->None:
        doc_ref = firestore_db.collection("drivers").document(driver_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise Exception("driver not found")
        doc_ref.delete()

    @staticmethod
    def get_driver_by_id(driver_id:str)->dict:
        doc_ref = firestore_db.collection("drivers").document(driver_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise Exception("driver not found")

        driver = {"id": doc.id, **doc.to_dict()}
        query = firestore_db.collection("teams")
        teams = [doc.to_dict() for doc in query.stream()]
        return {"driver": driver, "teams": teams}
    

    @staticmethod
    def get_drivers(attribute: Optional[str] = None, 
                    operator: Optional[str] = None, 
                    value: Optional[str] = None) -> List[Dict[str, Union[str, int]]]:
        
        query = firestore_db.collection('drivers')
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
        
        
        drivers = [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]
        
        return drivers, query_info
    
    @staticmethod
    def compare_drivers()->dict:
        drivers_ref = firestore_db.collection('drivers')
        drivers = []
        for doc in drivers_ref.stream():
            driver_data = doc.to_dict()
            driver_data['id'] = doc.id
            drivers.append(driver_data)
        return drivers
    @staticmethod
    def compare_drivers_attributes(driver1,driver2):
        # Get driver details
        driver1_doc = firestore_db.collection('drivers').document(driver1).get()
        driver2_doc = firestore_db.collection('drivers').document(driver2).get()
        
        if not driver1_doc.exists or not driver2_doc.exists:
            raise Exception("driver not found.")
        
        driver1_data = driver1_doc.to_dict()
        driver1_data['id'] = driver1_doc.id
        
        driver2_data = driver2_doc.to_dict()
        driver2_data['id'] = driver2_doc.id

        if driver1_data['id'] == driver2_data['id']:
            raise Exception("comparison cannot be done between two same entities")

        # Determine which stats are better
        comparison = {}
        comparison['age'] = 'driver1' if driver1_data['age'] < driver2_data['age'] else 'driver2'
        comparison['poles'] = 'driver1' if driver1_data['total_pole_positions'] > driver2_data['total_pole_positions'] else 'driver2'
        comparison['wins'] = 'driver1' if driver1_data['total_race_wins'] > driver2_data['total_race_wins'] else 'driver2'
        comparison['points'] = 'driver1' if driver1_data['total_points_scored'] > driver2_data['total_points_scored'] else 'driver2'
        comparison['titles'] = 'driver1' if driver1_data['total_world_titles'] > driver2_data['total_world_titles'] else 'driver2'
        comparison['fastestLaps'] = 'driver1' if driver1_data['total_fastest_laps'] > driver2_data['total_fastest_laps'] else 'driver2'
        result={
            'driver1':driver1_data,
            'driver2':driver2_data,
            'comparison':comparison
        }
        return result
    