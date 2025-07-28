from fastapi_utils import Resource
from fastapi import Request
from utils.constants import TOPIC_NAME, LLM
from modules.summarize_pdf import get_summary
from utils.redis_utils import get_redis_summary, update_redis_summary
from utils.constants import PDF_URL
from utils.utils_funcs import get_pdf_file


class SummarizePdf(Resource):
    
    async def post(self, request:Request):
                
        json_data = await request.json()
        if not json_data:
            return {"message":"invalid paylod"}, 404
        
        user_id = json_data.get("user_id")
        product_id = json_data.get("product_id")
        if not product_id:
            return {"message":"invalid payload"}, 400
        
        key = f"{user_id}_{product_id}"
        summary = get_redis_summary(key)
        if summary:
            return {"message":summary}, 200
        
        filepath = get_pdf_file(product_id)
        if not summary:
            summary = get_summary(filepath , LLM)
            status = update_redis_summary(summary, key)
            return {"message":summary}, 200

        else:
            return {"message":"file path not found"} , 404


    





