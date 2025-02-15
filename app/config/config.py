import os
from datetime import timedelta
from urllib.parse import quote_plus
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from flask_jwt_extended import JWTManager

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ['headers']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)


username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

username = quote_plus(username)
password = quote_plus(password)

cluster = MongoClient(f"mongodb://{username}:{password}@mongocluster-shard-00-00.nw1nz.mongodb.net:27017,mongocluster-shard-00-01.nw1nz.mongodb.net:27017,mongocluster-shard-00-02.nw1nz.mongodb.net:27017/Portfolio_Website?appName=MongoCluster&ssl=true&authSource=admin")
db=cluster["Portfolio_Website"]
login_data = db["Login_Data"]

db_schema_manager=cluster["Schema_Manager"]
schema_data=db_schema_manager["User_Schema_Info"]

session = cluster.start_session()
expires = timedelta(days=7)
bcrypt = Bcrypt()

jwt = JWTManager()


