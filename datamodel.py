import json
import dotenv
from sqlalchemy import *
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
import psycopg2
import os, sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base

project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.append(project_root)

load_dotenv()

# engine = create_engine("sqlite:///issues.db", echo=True)
engine = create_engine(os.environ["SQL_CONNECTION_URL"], echo=True)
Base = declarative_base()


class ticket_datamodel(Base):

    __tablename__ = "ticket"
    ticket_number = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    impact_level = Column(String)
    environment = Column(String)
    additional_details = Column(JSONB)
    category = Column(String)
    creation_time = Column(DateTime)
    assigned_to = Column(String)
    assigned_time = Column(DateTime)
    close_time = Column(DateTime)
    resolution = Column(String)
    root_cause = Column(String)
    close_notes = Text(String)
    cause = Column(String)
    closed_by = Column(String)
    created_by = Column(String)
    slack_link = Column(String)
    datacenter = Column(String)
    ticket_type = Column(String)
    


#ticket_datamodel.__table__.drop(engine)
Base.metadata.create_all(engine)
