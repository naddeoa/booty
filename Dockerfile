from ubuntu:22.04

##
## Fresh install simulation
##
ENV DEBIAN_FRONTEND=noninteractive




# Create a new user and switch to it
RUN apt update && apt upgrade -y

# DELETE Just to cache this stuff in docker to save time testing
RUN apt install -y wget git vim autokey-gtk silversearcher-ag gawk xclip gnome-disk-utility cryptsetup build-essential dconf-editor ripgrep xdotool luarocks cmake libterm-readkey-perl expect ssh curl tar

RUN apt install -y sudo locales keyboard-configuration
RUN useradd -m myuser -s /bin/bash && \
    echo "myuser:password" | chpasswd && \
    adduser myuser sudo
RUN echo "myuser ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/myuser

# Set the timezone
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set the locale
RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  





















##
## Real stuff
##
USER myuser
WORKDIR /home/myuser

COPY ./ssh ./.ssh
COPY ./install.makefile ./

# make .ssh/* visible to myuser
RUN sudo chown -R myuser:myuser ./.ssh



RUN make -k -j 6 -f ./install.makefile


RUN cat /etc/passwd
RUN sudo chsh -s /usr/bin/fish myuser
RUN cat /etc/passwd


CMD ["sudo", "su", "-", "myuser"]
