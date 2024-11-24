import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.append("..")
sys.path.append("./app")

MONGO_URI = os.environ.get("MONGO_URI")
DATETIME_FORMAT = os.environ.get("DATETIME_FORMAT")
