.PHONY: essentials omf

files.git = ~/files

# MANUAL
# - generating ssh keys and uplodaing to remote servers for auth

# CON: output for the parallel version is incomprehensible because its just everything mixed into stdout
# CON: can't see what will happen before I agree to do it. Maybe dry run is ok for this.
# CON: I can't say "make everything" without manually defining everything. This kind of works.
all: $(shell sed -n -e '/^$$/ { n ; /^[^ .\#][^ ]*:/ { s/:.*$$// ; p ; } ; }' $(MAKEFILE_LIST))


# CON: everything has to be a file. This will alays re-execute
essentials:
	sudo apt install -y wget git vim autokey-gtk silversearcher-ag gawk xclip gnome-disk-utility cryptsetup build-essential dconf-editor ripgrep xdotool luarocks cmake libterm-readkey-perl expect ssh curl

~/.ssh/id_rsa:~/.ssh/id_rsa.pub
~/.ssh/id_rsa.pub:
	ssh-keygen -q -f ~/.ssh/id_rsa -N ""


$(files.git): essentials ~/.ssh/id_rsa.pub
	git clone naddeo@do.naddeo.org:~/git/files $@

~/notes: essentials
	git clone naddeo@do.naddeo.org:~/git/notes $@


##
## Terminal
##
.PHONY: terminal omf shell agave_font omf-config

terminal: essentials
	sudo apt install -y kitty fish tmux

# oh my fish
omf: terminal
	curl https://raw.githubusercontent.com/oh-my-fish/oh-my-fish/master/bin/install > /tmp/fish-install 
	chmod +x /tmp/fish-install
	/tmp/fish-install --noninteractive

omf-config: omf terminal
	fish -c "omf install fzf clearance"

# CON: Very awkward to do something like configure the login shell
shell: essentials
	sudo chsh -s /usr/bin/fish $(USER)

~/.tmux/plugins/tpm: terminal essentials
	git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm


# PRO While testing is awkward, doing multiple things is still very nice
agave_font: essentials
	curl https://github.com/ryanoasis/nerd-fonts/releases/download/v3.1.1/Agave.zip -o /tmp/agave.zip
	mkdir -p ~/.fonts
	unzip /tmp/agave.zip -d ~/.fonts/
	fc-cache -f -v


## 
## Dotfile symlinks
## 
~/.config/Code: $(files.git)
	mkdir -p ~/.config
	ln -s $(files.git)/vscode $@

~/.config/autokey: $(files.git)
	mkdir -p ~/.config
	ln -s $(files.git)/autokey $@

~/.ctags: $(files.git)
	ln -s $(files.git)/.ctags $@

~/.gitconfig: $(files.git)
	ln -s $(files.git)/.gitconfig $@

~/.tmux.conf: $(files.git)
	ln -s $(files.git)/.tmux.conf $@

~/.toprc: $(files.git)
	ln -s $(files.git)/.toprc $@

~/.xbindkeysrc: $(files.git)
	ln -s $(files.git)/.xbindkeysrc $@

~/.Xmodmap: $(files.git)
	ln -s $(files.git)/.Xmodmap $@

# PRO: doing multiple things for a target is straight forward
~/.config/kitty/kitty.conf: $(files.git)
	mkdir -p ~/.config/kitty
	ln -s $(files.git)/kitty.conf $@

##
## Python
##
.PHONY: python3.7 python3.8 python3.9 python3.10 poetry pipx

# CON: No way of modeling this sort of lock based dependency where all apt commands
# have to be queued, even if they don't depend on each other.
pipx: essentials terminal
	sudo apt install -y pipx

# CON: Again, this ends up being a file test
# CON: No easy way to add this to my path and have dependencies take advantage of it
#      I'll neeed to reference it directly by expected file path
PYENV = ~/.pyenv/bin/pyenv
$(PYENV): essentials terminal pipx
	# Various dependencies for building python
	sudo apt install -y \
		build-essential \
		libssl-dev \
		zlib1g-dev \
		libncurses5-dev \
		libncursesw5-dev \
		libreadline-dev \
		libsqlite3-dev \
		libgdbm-dev \
		libdb5.3-dev \
		libbz2-dev \
		libexpat1-dev \
		liblzma-dev \
		tk-dev \
		libffi-dev
	curl https://pyenv.run | bash

python3.7: $(PYENV)
	$(PYENV) install 3.7

python3.8: $(PYENV)
	$(PYENV) install 3.8

python3.9: $(PYENV)
	$(PYENV) install 3.9

python3.10: $(PYENV)
	$(PYENV) install 3.10
	$(PYENV) global 3.10

poetry: python3.10
	pipx install poetry


