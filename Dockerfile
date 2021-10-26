from python:3.9.6-buster

# Setting Timezone
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ADD . /

RUN pip install -r requirements.txt

RUN cp ./client.py /usr/local/lib/python3.9/site-packages/discord/client.py

CMD [ "python", "./project_alfred.py", "live" ]
