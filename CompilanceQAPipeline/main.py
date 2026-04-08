"""
Main the execution of the compilance Qa Pipleine 
"""
import uuid
import json 
import logging
from pprint import pprint

from dotenv import load_dotenv
load_dotenv()

from backend.src.graph.workflow import app 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger=logging.getLogger("Main")
