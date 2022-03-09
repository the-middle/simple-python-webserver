FROM python:3.9.10-slim-bullseye

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt update \
    && apt install libpq-dev gcc apt-transport-https curl gnupg2 -y \
    && curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list \
    && apt update \
    && apt install -y kubectl

RUN /usr/local/bin/python3 -m pip install psycopg2 pyYAML\
    && apt autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY ./server1.py /opt/server.py

CMD /usr/local/bin/python3 /opt/server.py