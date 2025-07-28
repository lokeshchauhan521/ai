from services.file_summary import SummarizePdf
from fastapi_utils import Api
from fastapi import Depends


def get_route_map():
    return [
        {
            'obj': SummarizePdf(),
            'pattern': '/summarize',
            'decorators': []
        }
        
        ]

def routing(app):
    
    route_map = get_route_map()  # Assume this returns a list of route objects
    for obj in route_map:
        dec_list = obj.get('decorators', [])
        api = Api(app) if not dec_list else Api(app, dependencies=[Depends(d) for d in dec_list])
        api.add_resource(obj['obj'], obj['pattern'])