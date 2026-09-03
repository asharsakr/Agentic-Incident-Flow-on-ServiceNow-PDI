from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
load_dotenv()
