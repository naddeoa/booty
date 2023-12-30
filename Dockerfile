from naddeoa/booty:ubuntu22.04

RUN --mount=type=cache,target=/var/cache/apt sudo apt install -y python3 python3-pip  # MANUAL install pip
COPY ./dist/*.whl ./
RUN --mount=type=cache,target=/home/myuser/.cache pip install --user ./*.whl  # MANUAL install booty

COPY ./ssh ./.ssh
RUN sudo chown -R myuser:myuser ./.ssh
RUN chmod 600 .ssh/id_rsa

COPY ./examples/install.booty ./

ENV PATH="/home/myuser/.local/bin:${PATH}"
RUN booty -i -y

CMD ["fish"]
