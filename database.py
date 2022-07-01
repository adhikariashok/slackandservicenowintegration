from ast import Str
from datetime import datetime
import json
from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, DateTime, Integer, create_engine
from datamodel import ticket_datamodel, engine


Session = sessionmaker(engine)


def create_new_ticket(
    ticket_number:str,
    description:str,
    environment:str,
    title:str,
    impact_level:str,
    created_by:str,
    creation_time:datetime,
    category:str,
    additional_details:json,
    datacenter:str,
    ticket_type:str
):
    """Details on data types and description

    Args:
        ticket_number (str): Ticket number of the issue
        description (str): What is the issue about
        environment (str): Selection between IT/UAT/PROD
        title (str): Title of the issue
        impact_level (str): Impact level by default set to 3-LOW
        created_by (str): Who created the ticket
        creation_time (datetime): Time the ticket was generated
        category (str): Arcadia/Athena
        additional_details (json): All the additional details regarding issue provided by the user
        datacenter (str): RNO/SMP/MESA or OTHER
        ticket_type (str): Helpcentral/Radar/None
    """
    # local_session=Session(bind=engine)
    ticket_details = ticket_datamodel(
        ticket_number=ticket_number,
        description=description,
        environment=environment,
        title=title,
        impact_level=impact_level,
        created_by=created_by,
        creation_time=creation_time,
        category=category,
        additional_details=additional_details,
        datacenter = datacenter,
        ticket_type = ticket_type
    )

    with Session() as session:
        session.add(ticket_details)
        session.commit()
    # local_session.add(ticket_details)
    # local_session.commit()


def close_ticket(
    ticket_number:str, resolution:str, root_cause:str, close_notes:str, cause:str, closed_by:str, close_time:datetime
):
    """Details on data type

    Args:
        ticket_number (str): Ticket number for the issue
        resolution (str): Steps taken to resolve the issue
        root_cause (str): What was the reason behind the issue
        close_notes (str): Consists of resolution, closed notes and closed by
        cause (str): What was the cause of the issue?
        closed_by (str): Person who closed the ticket
        close_time (datetime): Time the ticket was closed
    """
    with Session() as session:
        ticket_details_to_update = (
            session.query(ticket_datamodel)
            .filter(ticket_datamodel.ticket_number == ticket_number)
            .first()
    )
        ticket_details_to_update.resolution = resolution
        ticket_details_to_update.root_cause = root_cause
        ticket_details_to_update.close_notes = close_notes
        ticket_details_to_update.cause = cause
        ticket_details_to_update.closed_by = closed_by
        ticket_details_to_update.close_time = close_time
    
        session.commit()


def update_ticket(ticket_number:str, assigned_time:datetime, assigned_to:str):
    """Details on data type

    Args:
        ticket_number (str): Ticket number for the issue
        assigned_time (datetime): When was the ticket was assigned
        assigned_to (str): Person the ticket was assigned to
    """    
    with Session() as session:
        ticket_details_to_update = (
            session.query(ticket_datamodel)
            .filter(ticket_datamodel.ticket_number == ticket_number)
            .first()
    )
        ticket_details_to_update.assigned_time = assigned_time
        ticket_details_to_update.assigned_to = assigned_to
        session.commit()


def link_update(ticket_number:str, slack_link:str):
    """Used to updating slack link to the ticket

    Args:
        ticket_number (str): Ticket number for the issue
        slack_link (str): Link to the slack chat where discussion about the ticket is ongoing
    """
    with Session() as session:
        ticket_details_to_update = (
            session.query(ticket_datamodel)
            .filter(ticket_datamodel.ticket_number == ticket_number)
            .first()
    )
        ticket_details_to_update.slack_link = slack_link
        session.commit()


if __name__ == "__main__":
    create_new_ticket("INC0542368", "Issue with arcadia", "IT")
    close_ticket("Ashok Adhikari")
