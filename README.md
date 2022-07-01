# DSEHelpBot

A Bot for integrating help central ticket creation, update and closing process by using workflow through Slack

# Requirements

All the requirements for packages have been listed in requirements.txt which will install by itself after you download it from github and dockerize it

# Files

Database:  Database.py which will create and update  POSTGRES SQL database for storing all the ticket information for creating reports
Datamodel: Datamodel.py has the name of the tables that will be created in database for storing values
Bot: Bot.py will link other functions and database for creating,updating and closing ticket along with checking emoji reaction and saving ticket information on database
Helpcentral: Helpcentral.py will establish the connection between Helpcentral API and our bot
Plugins: Plugins folder has helpcentral_plugin.py which will post the linkn of the slack chat to the ticket in HelpCentral

# Secrets

There are different secret required to run the program which are stored in .env file which is not uploaded in the github and you need to create your own .env file as well. The format for .env file is as below:

SLACK_APP_TOKEN = Your slack app token
SLACK_BOT_TOKEN= Your slack bot token
app_password_prod = "Your production password"
app_password_uat = "YOUR uat password"
SQL_CONNECTION_URL = "Link to connecting to the SQL datbase"

SLACK_APP_TOKEN: You can get this app token from api.slack.com
SLACK_BOT_TOKEN: You can also get this app token from api.slack.com
app_password_prod: This is for linking helpcentral production environment to our bot
app_password_uat: This is for linking helpcentral UAT environment to our bot
SQL_CONNECTION_URL: This will be the link to the databse where every ticket information will be saved

# Virtual env

Python virtaul env will allow to install multiple version of python onto your computer and will allow you option to switch between them. While developing the code we have used Pyenv and you can find details about it from the following link:

https://realpython.com/intro-to-pyenv/

For developing purposes we suggest you to take following steps for virtual env:

    * install pyenv
    * install pyenv-virtualenv
    * create virtualenv slackbot(you can name it as you want)
    * install required dependency
    * auto activate slackbot virtualenv when entering the project directory
    * configure vscode(or any IDE you use) to use the virtualenv


# YAML files

There are different YML files for contarization and CI/CD which you can configure according to your usage. You can go to the following links where you can get information about Apple CI/CD




Devloped by Ashok Adhikari and Lianjun Jiang








