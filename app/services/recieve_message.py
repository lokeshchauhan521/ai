from fastapi_utils import Resource
from fastapi import Request
from fastapi.responses import StreamingResponse
from modules.consume_message import consume_message
from utils.constants import TOPIC_NAME


class ConsumeMsg(Resource):
    
    def get(self, user_id, product_id):
        streamer = consume_message(TOPIC_NAME, user_id, product_id)
        return StreamingResponse(streamer, media_type="text/event-stream")

        


    





