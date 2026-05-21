import os

class Config:
    SECRET_KEY = "pricepulse_secret_key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///pricepulse.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False