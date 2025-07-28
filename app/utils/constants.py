import os
# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_API_KEY"]='api keyq'

LLM = ChatOpenAI(model_name="gpt-4o-mini")
BOOTSTRAP_SERVER = os.getenv("KAFKA_SERVER")
TOPIC_NAME = os.getenv("TOPIC_NAME")
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
PDF_URL=os.getenv("PDF_URL")
PROFILE_NAME = os.getenv("PROFILE_NAME")
BUCKET_NAME = os.getenv("BUCKET_NAME")

