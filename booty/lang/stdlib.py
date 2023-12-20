stdlib = """
recipe apt(packages):
    setup: sudo apt-get install -y $((packages))
    is_setup:
      for pkg in $(echo $((packages)) | tr " " "\n"); do
        if ! dpkg -l "$pkg" &> /dev/null; then
          echo "$pkg is not installed."
          exit 1
        fi
      done

recipe pipx(packages):
    setup: pipx install $((packages))
    is_setup: pipx list | grep $((packages))


recipe git(repo dist):
    setup: git clone $((repo)) $((dist))
    is_setup: test -d $((dist))

recipe git_shallow(repo dist):
    setup: git clone --depth 1 $((repo)) $((dist))
    is_setup: test -d $((dist))

recipe ln(src dst):
    setup: 
        mkdir -p $(dirname $((dst)))
        ln -fs $((src)) $((dst))
    is_setup: test -L $((dst)) && test -e $((dst))

recipe cp(src dst):
    setup: 
        mkdir -p $(dirname $((dst)))
        cp -r $((src)) $((dst))
    is_setup: test -e $((dst))

"""
