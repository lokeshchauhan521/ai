import os
from fastapi import FastAPI
from routing.routing import routing
from fastapi.middleware.cors import CORSMiddleware


def create_app():
    app = FastAPI()
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, PATCH, OPTIONS)
    allow_headers=["*"],  # Allows all headers
    )
    routing(app)
    return app

