FROM python:3.8
WORKDIR /slack_bot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt -i https://pypi.apple.com/simple
COPY ./slackbot ./slackbot
COPY ./tests ./tests
COPY bot.py bot.py
COPY helpcentral.py helpcentral.py
COPY database.py database.py
COPY datamodel.py datamodel.py
COPY common.py common.py
CMD ["python", "./bot.py"]