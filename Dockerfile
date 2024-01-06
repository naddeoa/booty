from naddeoa/booty:ubuntu22.04

RUN sudo apt-get update
RUN --mount=type=cache,target=/var/cache/apt sudo apt-get install -y python3 python3-pip  # MANUAL install pip
COPY ./dist/*.whl ./
RUN --mount=type=cache,target=/home/myuser/.cache pip install --user ./*.whl  # MANUAL install booty

COPY ./ssh ./.ssh
RUN sudo chown -R myuser:myuser ./.ssh
RUN chmod 600 .ssh/id_rsa

COPY ./examples/install.booty ./

ENV PATH="/home/myuser/.local/bin:${PATH}"
# Don't prompt for sudo password in CI. Even when the user is in the sudoers file it becomes an interactive prompt.
RUN booty -i -y --no-sudo

CMD ["fish"]
