from ast import Str
import json
from time import time
import urllib.parse
import logging
import os, sys, re
from dotenv import load_dotenv
from slack_bolt import App, Say
from slack_bolt.workflows.step import WorkflowStep
from slack_bolt.adapter.socket_mode import SocketModeHandler
import glob
import importlib
from helpcentral import get_kentaurus_client
from pprint import pprint as print
from slack_sdk import WebClient
from database import close_ticket, create_new_ticket, update_ticket
from datetime import datetime


from common import get_apple_dsid_from_email, get_name_from_email


log_format = '%(asctime)s - %(funcName)s - %(name)s - %(levelname)s - %(filename)s -%(lineno)s - %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel('INFO')
file_handler = logging.StreamHandler()
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
   

project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.append(project_root)

load_dotenv()

SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
app_password_prod = os.environ["app_password_prod"]
app_password_uat = os.environ["app_password_uat"]


# app = App(
#     name="DSEHelpBot",
#     client=WebClient(token=SLACK_BOT_TOKEN, proxy="http://dps.iso.apple.com:443"),
# )

app = App(
    name="DSEHelpBot",
    client=WebClient(
        token=SLACK_BOT_TOKEN,
    ),
) 

    
def load_plugins():
    loaded_plugins = []
    for _plugin in glob.glob("slackbot/plugins/*.py"):
        _plugin = os.path.splitext(_plugin)[0]
        module_name = _plugin.replace("/", ".")
        m = importlib.import_module(module_name)
        if hasattr(m, "plugin"):
            loaded_plugins.append(m.plugin)
    logger.info(f"loaded plugins: {[_.__class__.__name__ for _ in loaded_plugins]}")
    return loaded_plugins


loaded_plugins = load_plugins()


@app.event("message")
def brain(message: str, client, say):
    reply = ""
    logger.debug(f"got message event: {message}")
    for plugin in loaded_plugins:
        if plugin.match(message):
            reply = plugin.handle(client, message)
            if reply:
                ts = message.get("thread_ts") or message["ts"]
                say(text=reply, thread_ts=ts)
            else:
                None


@app.event("reaction_added")
def reaction(event, say, client):
    reaction = event.get("reaction")

    if reaction == "eyes":
        ts = event["item"]["ts"]
        channel_id = event["item"]["channel"]
        slack_user_id = event["user"]
        email = app.client.users_profile_get(user=slack_user_id, include_labels=True)
        apple_email = email["profile"]["email"]
        apple_dsid = get_apple_dsid_from_email(apple_email)
        result = client.conversations_history(
            channel=channel_id,
            latest=ts,
            limit=1,
            inclusive=True,
        )
        conversation_history = result["messages"][0]["text"]
        match = re.match("\[(INC\d+)]", conversation_history)
        match_nothelpcentral = re.match("\[(TKT\d+)]", conversation_history)
        if match_nothelpcentral:
            ticket_number:int = match_nothelpcentral.group(1)
            reply = f"<@{slack_user_id}> has been assigned with this ticket. Remember helpcentral ticket was not created for this issue"
            update_ticket(
                ticket_number=ticket_number,
                assigned_time=datetime.now(),
                assigned_to=apple_email,
            )
            say(text=reply, thread_ts=ts)
        elif match:
            ticket_number = match.group(1)

            ticket_details = {
                "module": "incident",
                "dsPrsId": "2701021274",
                "ticketId": ticket_number,
                "assignedPersonId": apple_dsid,
                "ticketOwnerId": apple_dsid,
            }
            reply = f"<@{slack_user_id}> has been assigned with this ticket"
            update_ticket(
                ticket_number=ticket_number,
                assigned_time=datetime.now(),
                assigned_to=apple_email,
            )
            try:
                incident_creation_response = get_kentaurus_client().update_record(
                    ticket_details
                )
                say(text=reply, thread_ts=ts)

            except Exception as exc:
                error = exc.args[0]
                error_msg = json.loads(error[6:].replace("'", '"'))
                logger.error(f"Ticekt update on assign part error: {error_msg}")
                say(text=error_msg["result"]["status"]["message"], thread_ts=ts)    
        else:
            None
    

def create_edit(ack, step, configure):

    ack()

    blocks = [
        {
            "type": "input",
            "block_id": "title_name_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "name",
                "placeholder": {"type": "plain_text", "text": "Add a Title"},
            },
            "label": {"type": "plain_text", "text": "Title"},
        },
        {
            "type": "input",
            "block_id": "issue_description_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "description",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Add the description of the issue",
                },
            },
            "label": {"type": "plain_text", "text": "Issue Description"},
        },
        {
            "type": "input",
            "block_id": "impact_level_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "impact_level-action",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Impact level of the issue",
                },
            },
            "label": {"type": "plain_text", "text": "impact level selection"},
        },
        {
            "type": "input",
            "block_id": "environment_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "environment_selection-action",
                "placeholder": {"type": "plain_text", "text": "Environment affected"},
            },
            "label": {"type": "plain_text", "text": "Environment selection"},
        },
        {
            "type": "input",
            "block_id": "urgency_level_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "urgency_level-action",
                "placeholder": {"type": "plain_text", "text": "Urgency level"},
            },
            "label": {"type": "plain_text", "text": "Urgency selection"},
        },
        {
            "type": "input",
            "block_id": "user_id",
            "element": {
                "type": "plain_text_input",
                "action_id": "user_id-action",
                "placeholder": {"type": "plain_text", "text": "User Id"},
            },
            "label": {"type": "plain_text", "text": "User Id"},
        },
        {
            "type": "input",
            "block_id": "additional_details_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "additional_details",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Put key and value with seperate delimeter @@KV@@ so that it can be extracted later for query in SQL",
                },
            },
            "label": {"type": "plain_text", "text": "additional details"},
        },
        {
            "type": "input",
            "block_id": "ticket_category_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "ticket_category-action",
                "placeholder": {
                    "type": "plain_text",
                    "text": "ticket type (arcadia or notebook or else)",
                },
            },
            "label": {"type": "plain_text", "text": "ticket category"},
        },
        {
            "type": "input",
            "block_id": "datacenter_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "datacenter-action",
                "placeholder": {"type": "plain_text", "text": "datacenter"},
            },
            "label": {"type": "plain_text", "text": "datacenter selection"},
        },
        {
            "type": "input",
            "block_id": "tickettype_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "tickettype-action",
                "placeholder": {"type": "plain_text", "text": "helpcentral/radar/none"},
            },
            "label": {"type": "plain_text", "text": "tickettype selection"},
        },
    ]
    configure(blocks=blocks)


def create_save(ack, view, update):
    ack()
    values: str = view["state"]["values"]
    title_name: str = values["title_name_input"]["name"]
    issue_description: str = values["issue_description_input"]["description"]
    impact_level:str = values["impact_level_input"]["impact_level-action"]
    environment_selection:str  = values["environment_input"]["environment_selection-action"]
    urgency_level:str = values["urgency_level_input"]["urgency_level-action"]
    user_id:str = values["user_id"]["user_id-action"]
    additional_details:str = values["additional_details_input"]["additional_details"]
    ticket_category:str = values["ticket_category_input"]["ticket_category-action"]
    datacenter:str = values["datacenter_input"]["datacenter-action"]
    tickettype:str = values["tickettype_input"]["tickettype-action"]


    

    inputs = {
        "title_name": {"value": title_name["value"]},
        "issue_description": {"value": issue_description["value"]},
        "impact_level": {"value": impact_level["value"]},
        "environment_selection": {"value": environment_selection["value"]},
        "urgency_level": {"value": urgency_level["value"]},
        "user_id": {"value": user_id["value"]},
        "additional_details": {"value": additional_details["value"]},
        "ticket_category": {"value": ticket_category["value"]},
        "datacenter": {"value": datacenter["value"]},
        "tickettype": {"value": tickettype["value"]},
    }
    outputs = [
        {
            "type": "text",
            "name": "title_name",
            "label": "Title ",
        },
        {
            "type": "text",
            "name": "issue_description",
            "label": "Issue description",
        },
        {
            "type": "text",
            "name": "impact_level",
            "label": "Impact level selection",
        },
        {
            "type": "text",
            "name": "environment_selection",
            "label": "Affected environment selection",
        },
        {
            "type": "text",
            "name": "urgency_level",
            "label": "Urgency level selection",
        },
        {
            "type": "text",
            "name": "user_id",
            "label": "user id selection",
        },
        {
            "type": "text",
            "name": "additional_details",
            "label": "additional details",
        },
        {
            "type": "text",
            "name": "ticket_number",
            "label": "ticket number input",
        },
        {
            "type": "text",
            "name": "ticket_link",
            "label": "ticket link",
        },
        {
            "type": "text",
            "name": "ticket_category",
            "label": "ticket category",
        },
        {
            "type": "text",
            "name": "datacenter",
            "label": "datacenter selection",
        },
        {
            "type": "text",
            "name": "tickettype",
            "label": "tickettype selection",
        },
    ]
    
    
    update(inputs=inputs, outputs=outputs)


def create_execute(step, complete, fail, client, event):
    inputs = step["inputs"]
    apple_email:str = inputs["user_id"]
    email:str = apple_email["value"]

    apple_dsid:int = get_apple_dsid_from_email(email)
    

    outputs = {
        "title_name": inputs["title_name"]["value"],
        "issue_description": inputs["issue_description"]["value"],
        "impact_level": inputs["impact_level"]["value"],
        "environment_selection": inputs["environment_selection"]["value"],
        "urgency_level": inputs["urgency_level"]["value"],
        "user_id": inputs["user_id"]["value"],
        "additional_details": inputs["additional_details"]["value"],
        "ticket_category": inputs["ticket_category"]["value"],
        "datacenter": inputs["datacenter"]["value"],
        "tickettype": inputs["tickettype"]["value"],
    }

    additional_info = re.split("@@KV@@", outputs["additional_details"])
    # additional_info_formatted = {
    #     additional_info[0]: additional_info[1],
    #     additional_info[2]: additional_info[3],
    # }
    additional_info_formatted = {
        additional_info[i].strip(): additional_info[i + 1].strip()
        for i in range(0, len(additional_info), 2)
    }

    additional_info_str = "\n".join([f"{k}: {v}" for k,v in additional_info_formatted.items()])

    json_data = {
        "module": "incident",
        "callingApp": "181289",
        "callerId": apple_dsid,
        # "ticketOwnerId": "2700800811",
        # "dueDate":"2021 08 29 06 54 34",
        "businessService": "IS&T",
        # "category": "Alert & Monitoring",
        "configuration": "Athena",
        "assignmentGroupId": "600384",
        # "subCategory": "Job Overrun",
        "title": outputs["title_name"],
        "description": f"""Environment: {outputs['datacenter']}\nIssue Details: {outputs['issue_description']}\n{additional_info_str}""",
        "impact": outputs["impact_level"],
        "type": "Request",
        "urgency": outputs["urgency_level"],
        "appleKeywords": outputs["additional_details"],
        # "assignmentGroupId": "868912",
        # "assignedPersonId": DSID,
        "environment": outputs["environment_selection"],
        "contactType": "Chat",
        # "technicalDRI":"2304670255",
        # "incidentLocation": "Bangalore",
        # "watchlist":"2302796918,2304435628,2319833145,2302796918",
        # "tags": "Testing tag feature",
    }
    
    if outputs["tickettype"] == "helpcentral":
        try:
            inc = get_kentaurus_client().create_record["result"]["data"][0]["number"]
            url = "https://helpcentral.apple.com/tkt.do?tkt={0}".format(inc)
            outputs = {
                "title_name": inputs["title_name"]["value"],
                "issue_description": inputs["issue_description"]["value"],
                "impact_level": inputs["impact_level"]["value"],
                "environment_selection": inputs["environment_selection"]["value"],
                "urgency_level": inputs["urgency_level"]["value"],
                "user_id": inputs["user_id"]["value"],
                "additional_details": additional_info_formatted,
                "ticket_number": inc,
                "ticket_link": url,
                "ticket_category": inputs["ticket_category"]["value"],
                "datacenter": inputs["datacenter"]["value"],
                "tickettype": inputs["tickettype"]["value"],
            }

            create_new_ticket(
                ticket_number=outputs["ticket_number"],
                description=outputs["issue_description"],
                environment=outputs["environment_selection"],
                title=outputs["title_name"],
                impact_level=outputs["impact_level"],
                created_by=email,
                creation_time=datetime.now(),
                category=outputs["ticket_category"],
                additional_details=additional_info_formatted,
                datacenter=outputs["datacenter"],
                ticket_type=outputs["tickettype"],
            )

            complete(outputs=outputs)
        except Exception as exc:
            ts = event["item"]["ts"]
            channel_id = event["item"]["channel"]
            error = exc.args[0]
            error_msg = json.loads(error[6:].replace("'", '"'))
            logger.error(f"Ticekt create error: {error_msg}")
            result = client.chat_postMessage(
            channel=channel_id,
            text=error_msg
        
        )
            print(result)
            complete(outputs=outputs)

    else:
        startdate:datetime = datetime(2020,12,30,23,59,59)
        currentdate:datetime= datetime.now()
        create_new_ticket(
            ticket_number= "TKT"+str((currentdate-startdate).seconds),
            description=outputs["issue_description"],
            environment=outputs["environment_selection"],
            title=outputs["title_name"],
            impact_level=outputs["impact_level"],
            created_by=email,
            creation_time=datetime.now(),
            category=outputs["ticket_category"],
            additional_details=additional_info_formatted,
            datacenter= outputs["datacenter"],
            ticket_type= outputs["tickettype"]
        )
        outputs = {
            "title_name": inputs["title_name"]["value"],
            "issue_description": inputs["issue_description"]["value"],
            "impact_level": inputs["impact_level"]["value"],
            "environment_selection": inputs["environment_selection"]["value"],
            "urgency_level": inputs["urgency_level"]["value"],
            "user_id": inputs["user_id"]["value"],
            "additional_details": additional_info_formatted,
            "ticket_number": "TKT"+str((currentdate-startdate).seconds),
            "ticket_category": inputs["ticket_category"]["value"],
            "datacenter": inputs["datacenter"]["value"],
            "tickettype": inputs["tickettype"]["value"],
        }


        complete(outputs=outputs)

 

# # # if something went wrong

# except:
#     print ("A failure with ticket creation occured")

# # if something went wrong


# Create a new WorkflowStep instance
create_ws = WorkflowStep(
    callback_id="dsehelpbot_create_ticket",
    edit=create_edit,
    save=create_save,
    execute=create_execute,
)

# Pass Step to set up listeners

app.step(create_ws)


def close_edit(ack, step, configure):

    ack()

    blocks = [
        {
            "type": "input",
            "block_id": "close_notes_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "name",
                "placeholder": {
                    "type": "plain_text",
                    "text": "What did you do to resolve the issue",
                },
            },
            "label": {"type": "plain_text", "text": "close_notes"},
        },
        {
            "type": "input",
            "block_id": "user_id",
            "element": {
                "type": "plain_text_input",
                "action_id": "user_id-action",
                "placeholder": {"type": "plain_text", "text": "User Id"},
            },
            "label": {"type": "plain_text", "text": "User Id"},
        },
        {
            "type": "input",
            "block_id": "resolution",
            "element": {
                "type": "plain_text_input",
                "action_id": "resolution-action",
                "placeholder": {"type": "plain_text", "text": "resolution"},
            },
            "label": {"type": "plain_text", "text": "resolution"},
        },
        {
            "type": "input",
            "block_id": "cause",
            "element": {
                "type": "plain_text_input",
                "action_id": "cause-action",
                "placeholder": {"type": "plain_text", "text": "cause"},
            },
            "label": {"type": "plain_text", "text": "cause"},
        },
        {
            "type": "input",
            "block_id": "permalink",
            "element": {
                "type": "plain_text_input",
                "action_id": "permalink-action",
                "placeholder": {"type": "plain_text", "text": "permalink"},
            },
            "label": {"type": "plain_text", "text": "permalink"},
        },
        {
            "type": "input",
            "block_id": "root_cause_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "root_cause_action",
                "placeholder": {
                    "type": "plain_text",
                    "text": "What was the root cause?",
                },
            },
            "label": {"type": "plain_text", "text": "root_cause"},
        },
    ]
    configure(blocks=blocks)


def close_save(ack, view, update):
    ack()
    values = view["state"]["values"]
    close_notes:str = values["close_notes_input"]["name"]
    user_id:str = values["user_id"]["user_id-action"]
    resolution:str = values["resolution"]["resolution-action"]
    cause:str = values["cause"]["cause-action"]
    permalink:str = values["permalink"]["permalink-action"]
    root_cause:str = values["root_cause_input"]["root_cause_action"]

    inputs = {
        "close_notes": {"value": close_notes["value"]},
        "user_id": {"value": user_id["value"]},
        "resolution": {"value": resolution["value"]},
        "cause": {"value": cause["value"]},
        "permalink": {"value": permalink["value"]},
        "root_cause": {"value": root_cause["value"]},
    }
    outputs = [
        {
            "type": "text",
            "name": "resolution",
            "label": "resolution ",
        },
        {
            "type": "text",
            "name": "close_notes",
            "label": "close_notes ",
        },
        {
            "type": "text",
            "name": "user_id",
            "label": "user id selection",
        },
        {
            "type": "text",
            "name": "cause",
            "label": "cause ",
        },
        {
            "type": "text",
            "name": "permalink",
            "label": "permalink ",
        },
        {
            "type": "text",
            "name": "root_cause",
            "label": "root_cause",
        },
    ]
    update(inputs=inputs, outputs=outputs)


def close_execute(step, complete, event, client, fail):
    # try:
    inputs = step["inputs"]
    apple_email = inputs["user_id"]
    email = apple_email["value"]
    apple_dsid = get_apple_dsid_from_email(email)
    name = get_name_from_email(email)

    outputs = {
        "resolution": inputs["resolution"]["value"],
        "user_id": inputs["user_id"]["value"],
        "close_notes": inputs["close_notes"]["value"],
        "cause": inputs["cause"]["value"],
        "permalink": inputs["permalink"]["value"],
        "root_cause": inputs["root_cause"]["value"],
    }

    permalink = event["workflow_step"]["inputs"]["permalink"]
    myurl = permalink["value"]
    parse = urllib.parse.urlparse(myurl)
    queries = [q.split("=") for q in parse.query.split("&")]
    result_dict = {k: v for k, v in queries}
    ts = result_dict["thread_ts"]
    cid = result_dict["cid"]
    result = client.conversations_history(
        channel=cid,
        latest=ts,
        limit=1,
        inclusive=True,
    )
    conversation_history = result["messages"][0]["text"]
    match = re.match("\[(INC\d+)]", conversation_history)
    if match:
        kentaurus_client=get_kentaurus_client()
        ticket_number = match.group(1)

        json_data = {
            "module": "incident",
            "ticketId": ticket_number,
            "callingApp": "181289",
            # "ticketOwnerId": apple_dsid,
            # "callerId": apple_dsid,
            "dsPrsId": apple_dsid,
            "assignedPersonId": apple_dsid,
            "businessService": "IS&T",
            "configuration": "Athena",
            "resolution": outputs["resolution"],
            "cause": outputs["cause"],
            "contactType": "Chat",
            "ticketStatus": "Resolved",
            "resolutionSummary": f"Resolution: {outputs['close_notes']}\nRoot cause: {outputs['root_cause']}\nClosed by: {name}",
        }

        incident_creation_response = kentaurus_client.update_record(json_data)
        close_ticket(
            ticket_number=json_data["ticketId"],
            resolution=outputs["resolution"],
            root_cause=outputs["root_cause"],
            close_notes=outputs["close_notes"],
            cause=outputs["cause"],
            closed_by=outputs["user_id"],
            close_time=datetime.now(),
        )
        outputs = {
            "resolution": inputs["resolution"]["value"],
        }

        close_data = {
            "module": "incident",
            "ticketId": ticket_number,
            "callingApp": "181289",
            "callerId": apple_dsid,
            "dsPrsId": apple_dsid,
            "businessService": "IS&T",
            "configuration": "Athena",
            "contactType": "Chat",
            "ticketStatus": "Closed",
        }

        incident_creation_response = kentaurus_client.update_record(close_data)
        # error = {"message": "Ticket was already closed"}
        # fail(error=error)
    else:
        match = re.match("\[(TKT\d+)]", conversation_history)
        ticket_number = match.group(1)
        json_data = {
            "module": "incident",
            "ticketId": ticket_number,
            "callingApp": "181289",
            # "ticketOwnerId": apple_dsid,
            # "callerId": apple_dsid,
            "dsPrsId": apple_dsid,
            "assignedPersonId": apple_dsid,
            "businessService": "IS&T",
            "configuration": "Athena",
            "resolution": outputs["resolution"],
            "cause": outputs["cause"],
            "contactType": "Chat",
            "ticketStatus": "Resolved",
            "resolutionSummary": f"Resolution: {outputs['close_notes']}\nRoot cause: {outputs['root_cause']}\nClosed by: {name}",
        }
        close_ticket(
            ticket_number=json_data["ticketId"],
            resolution=outputs["resolution"],
            root_cause=outputs["root_cause"],
            close_notes=outputs["close_notes"],
            cause=outputs["cause"],
            closed_by=outputs["user_id"],
            close_time=datetime.now(),
        )

close_ws = WorkflowStep(
    callback_id="dsehelpbot_close_ticket",
    edit=close_edit,
    save=close_save,
    execute=close_execute,
)

# Pass Step to set up listeners

app.step(close_ws)


def check_edit(ack, step, configure):

    ack()

    blocks = [
        {
            "type": "input",
            "block_id": "permalink",
            "element": {
                "type": "plain_text_input",
                "action_id": "permalink-action",
                "placeholder": {"type": "plain_text", "text": "Permalink"},
            },
            "label": {"type": "plain_text", "text": "Permalink"},
        },
    ]
    configure(blocks=blocks)


def check_save(ack, view, update):
    ack()
    values = view["state"]["values"]

    permalink:str= values["permalink"]["permalink-action"]

    inputs = {
        "permalink": {"value": permalink["value"]},
    }
    outputs = [
        {
            "type": "text",
            "name": "permalink",
            "label": "permalink selection",
        },
    ]
    update(inputs=inputs, outputs=outputs)


def check_execute(step, complete, event, client, fail):
    # try:
    inputs = step["inputs"]

    outputs = {
        "permalink": inputs["permalink"]["value"],
    }

    parse:str = urllib.parse.urlparse(outputs["permalink"])
    components = parse.path.split("/")
    cid:int = components[2]
    raw_ts = components[3].replace("p", "")
    ts:int = raw_ts[:10] + "." + raw_ts[10:]
    result = client.conversations_history(
        channel=cid,
        latest=ts,
        limit=1,
        inclusive=True,
    )
    conversation_history = result["messages"][0]["text"]
    match = re.match("\[(INC\d+)]", conversation_history) or re.match("\[(TKT\d+)]", conversation_history)
    #match_nothelpdesk= re.match("\[(TKT\d+)]", conversation_history)
    if match:
        complete()
    else:
        error = {"message": "This is not ticket"}
        logger.error(f"Not a ticket error for emoji check: {error}")
        fail(error=error)


check_ws = WorkflowStep(
    callback_id="dsehelpbot_check_emoji",
    edit=check_edit,
    save=check_save,
    execute=check_execute,
)

# Pass Step to set up listeners


app.step(check_ws)


def main():
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    main()
