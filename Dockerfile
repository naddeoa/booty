from naddeoa/booty:ubuntu22.04 as base

##
## User space
## This also captures the things that have to be done manually before
## you can run booty
##

COPY ./dist/*.whl ./
RUN cat /etc/sudoers.d/myuser

RUN --mount=type=cache,target=/var/cache/apt sudo apt install -y python3 python3-pip  # MANUAL install pip
RUN --mount=type=cache,target=/home/myuser/.cache pip install --user ./*.whl  # MANUAL install booty

COPY ./ssh ./.ssh
RUN sudo chown -R myuser:myuser ./.ssh

COPY ./examples/install.booty ./

ENV PATH="/home/myuser/.local/bin:${PATH}"
RUN booty -i -y

CMD ["fish"]
