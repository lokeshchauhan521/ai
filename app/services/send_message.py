from fastapi_utils import Resource
from fastapi import Request,BackgroundTasks
from modules.produce_messages import produce_message
from modules.chat_module import produce_and_generate_answer
from utils.constants import TOPIC_NAME
from utils.logger import FileLogs
import os
from utils.utils_funcs import get_topic_key

logs = FileLogs().get_logger(os.path.basename(__file__))


class PublishMsg(Resource):
    
    async def post(self, request:Request,background_tasks: BackgroundTasks):
                
        json_data = await request.json()
        logs.info("request recieved in send message")
        if not json_data:
            return {"message":"invalid paylod"}, 404
        
        user_id = json_data.get("user_id")
        product_id = json_data.get("product_id")
        question  = json_data.get("query")
        logs.info(f"payload :- {json_data}")
        if not product_id:
            return {"message":"required product id"} , 400
        
        if question == None:
            return {"message":"question required"} , 400
        
        # produce_and_generate_answer(question, user_id, product_id)
        background_tasks.add_task(produce_and_generate_answer,question, user_id, product_id)
    
        return {"message":f"message is published for user_id {user_id}"}, 200


    





