from ubuntu:22.04 as base

##
## Fresh install simulation
##
ENV DEBIAN_FRONTEND=noninteractive


RUN --mount=type=cache,target=/var/cache/apt <<EOF
apt update && apt upgrade -y
# TODO line, just to cache this stuff in docker to save time testing
apt install -y wget git vim autokey-gtk silversearcher-ag gawk xclip gnome-disk-utility cryptsetup build-essential dconf-editor ripgrep xdotool luarocks cmake libterm-readkey-perl expect ssh curl tar
apt install -y sudo locales keyboard-configuration
EOF

# Set the timezone
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set the locale
RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  



##
## User space
## This also captures the things that have to be done manually before
## you can run booty
##
from base
ENV DEBIAN_FRONTEND=noninteractive
RUN useradd -m myuser -s /bin/bash && \
    echo "myuser:password" | chpasswd && \
    adduser myuser sudo && \
    echo "myuser ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/myuser

USER myuser
WORKDIR /home/myuser/

COPY ./dist/*.whl ./
RUN cat /etc/sudoers.d/myuser

RUN --mount=type=cache,target=/var/cache/apt sudo apt install -y python3 python3-pip  # MANUAL install pip
RUN --mount=type=cache,target=/home/myuser/.cache pip install --user ./*.whl  # MANUAL install booty

COPY ./ssh ./.ssh
COPY ./examples/install.booty ./

RUN sudo chown -R myuser:myuser ./.ssh

ENV PATH="/home/myuser/.local/bin:${PATH}"
RUN sudo chown -R myuser:myuser ./.ssh
RUN booty -i -y
CMD ["fish"]
