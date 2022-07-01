from ast import Str
from ..plugin_base import SlackPlugin
import re
from helpcentral import get_kentaurus_client
from database import link_update



class HelpCentralPlugin(SlackPlugin):
    def match(self, message):
        text_message = message["text"]
        match = re.match("\[(INC\d+)]", text_message) or re.match("\[(TKT\d+)]", text_message)
        if match:
            return True
        else:
            return False

    def handle(self, client, message):
        ts = message.get("thread_ts") or message["ts"]
        text_message = message["text"]
        m = re.match("\[(INC\d+)]", text_message)
        if m: 
        # if m:
            ticket_number = m.group(1)
            channel = message.get("channel")
            ma = client.chat_getPermalink(
            channel=message.get("channel"), message_ts=message.get("ts")
            )
            url = ma.get("permalink")
            link_update(ticket_number=ticket_number, slack_link=url)
            ticket_details = {
                "module": "incident",
                "ticketId": ticket_number,
                "dsPrsId": "2701021274",
                "workLog": "The link to the slack chat is " + url,
            }
        
            incident_creation_response = get_kentaurus_client().update_record(ticket_details)
        else:
            m = re.match("\[(TKT\d+)]", text_message)
            ticket_number = m.group(1)
            channel = message.get("channel")
            ma = client.chat_getPermalink(
            channel=message.get("channel"), message_ts=message.get("ts")
            )
            url = ma.get("permalink")
            link_update(ticket_number=ticket_number, slack_link=url)
            None


plugin = HelpCentralPlugin()
