import os
import asyncio
from config.app_config import create_app
from fastapi import WebSocket,FastAPI, WebSocketDisconnect
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from modules.chat_module import produce_and_generate_answer
from modules.consume_message import consume_message
from utils.constants import TOPIC_NAME
from modules.summarize_pdf import get_summary
from utils.db_utils import get_db_summary,insert_db_summary,regenerate_summary
from utils.utils_funcs import get_pdf_file,cleanup_space
import json
from utils.logger import FileLogs

logs = FileLogs().get_logger(os.path.basename(__file__))

load_dotenv()


app = create_app()

@app.websocket("/summarize/{product_id}")
async def websocket_endpoint(product_id ,websocket: WebSocket):
    """Websocket endpoint for real-time AI responses."""
    await websocket.accept()
    try:
        if not product_id:
            return {"message":"invalid payload"}, 400
        
        summary = get_db_summary(product_id)
        if summary:
            regen_summary = regenerate_summary(product_id)
            if regen_summary:
                logs.info(f"Need summary {regen_summary}")
                summary = None
            elif regen_summary is None:
                return {"message":"error occured in generating summary"}, 500
            else:
                await websocket.send_json(json.dumps({"message":summary}))
        
        filepath = get_pdf_file(product_id)
        if not summary:
            summary = await get_summary(filepath)
            status = insert_db_summary(product_id, summary)
            await websocket.send_json(json.dumps({"message":summary}))
    except WebSocketDisconnect:
        cleanup_space(product_id)
        logs.error("WebSocket disconnected")
    except Exception as e:
        logs.error("error occured in summarize api", exc_info=1)
        

@app.websocket("/recieve-msg/{user_id}/{product_id}")
async def websocket_endpoint(user_id, product_id ,websocket: WebSocket):
    """Websocket endpoint for real-time AI responses."""
    await websocket.accept()
    for msg in consume_message(TOPIC_NAME, user_id, product_id):
        await websocket.send_json(eval(msg))
    try:
        while True:
            question = await websocket.receive_text()
            ai_response = await produce_and_generate_answer(question, user_id, product_id)
            await websocket.send_json(ai_response)
    except WebSocketDisconnect:
        cleanup_space(product_id)
        logs.error("WebSocket disconnected")
    except Exception as e:
        logs.error("error occured in recieve message api", exc_info=1)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=os.getenv('FASTAPI_RUN_HOST'), port=os.getenv('FASTAPI_RUN_HOST'))