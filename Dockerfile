from python:3.9.6-buster

ADD . /

RUN pip install -r requirements.txt

RUN cp ./client.py /usr/local/lib/python3.9/site-packages/discord/client.py

CMD [ "python", "./project_alfred.py", "live" ]
