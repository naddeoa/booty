<p align="center"><img src="https://raw.githubusercontent.com/naddeoa/booty/master/static/booty-logo-bg-sm.png"/></p>

Booty is a language and command line utility for bootstrapping the setup of personal OS installs. Its goal is to execute all of the things
that you do after your first boot, like install packages through your package manager, configure your shell, setup your terminal tools/IDE,
and install SDKs for various programming languages, without you having to download everything manually and run various scripts in the right
order.

You model your setup process as Targets and declare which ones depend on which ones, then execute `booty` to set everything up, if
everything isn't already setup. Your install.booty file will specify various `setup` and `is_setup` methods that `booty` uses to set your
system up, and to test if everything was actually setup.

<!-- <p align="center"><img src="https://raw.githubusercontent.com/naddeoa/booty/master/static/booty-status.jpg"/></p> </br> -->

<a href="https://asciinema.org/a/WUdlyBpkAJJ4kXMfRFNpyfO7c" target="_blank"><img src="https://asciinema.org/a/WUdlyBpkAJJ4kXMfRFNpyfO7c.svg" /></a>

# Install

Installing from pip

```bash
pip install booty-cli
```

Or download the appropriate binary from the latest release. This script just downloads it for you and marks it as executable, but you should
move it somewhere on your path. The script will drop it in your `pwd`.

## Linux

```bash
curl https://raw.githubusercontent.com/naddeoa/booty/master/scripts/booty-download-linux.sh | bash
```

## Mac x86

```bash
curl https://raw.githubusercontent.com/naddeoa/booty/master/scripts/booty-download-mac-x86.sh | bash
```

## Mac Arm

```bash
curl https://raw.githubusercontent.com/naddeoa/booty/master/scripts/booty-download-mac-universal.sh | bash
```

# Usage

You can run `booty --help` to see all of the options. You'll generally cd to a directory with an `install.booty` file and run `booty`.
You'll see a table that shows the status of all of your targets and you'll be prompted to install all of the missing ones, which will
display in real-time as a second table with a row for each target getting setup.

```
Usage: booty [OPTIONS]

Options:
  -c, --config TEXT   Path to the install.sysc file. Defaults to
                      ./install.booty
  -s, --status        Check the status of all known targets
  -i, --install       Install all uninstalled targets
  -d, --debug         See the AST of the config file
  -l, --log-dir TEXT  Where to store logs. Defaults to ./logs
  --no-sudo           Don't allow booty to prompt with sudo -v. Instead, you
                      can manually run sudo -v before using booty to cache
                      credentials for any targets that use sudo. By default,
                      booty runs sudo -v upfront if you use sudo in any
                      targets.
  -y, --yes           Don't prompt for confirmation
  --help              Show this message and exit.
```

# Testing/Dry Runs

Setting your system up is inherently side effect prone. Every command from `apt` to `pip` is probably doing something to some part of your
system that you didn't realize. If you want to execute your `install.booty` file without worrying about what might go wrong before you use
it for real then the best way to do that is via Docker (which is how this repo does "integration" testing).

There is a [public docker image (naddeoa/booty:ubuntu22.04)](https://hub.docker.com/repository/docker/naddeoa/booty/general) that you can
base your own Dockerfile on that mimics what a fresh install looks like for Ubuntu 22.04 users. You can create an image that does roughly
what you would do to your system to get the `booty` command working, and then run it and make sure everything works as expected. The image's
user is named `myuser` and its password is `password`. You can see how its created in
[Dockerfile.base](https://github.com/naddeoa/booty/blob/master/Dockerfile.base).

This Dockerfile is what I use to test my own installs.

```Dockerfile
from naddeoa/booty:ubuntu22.04

RUN sudo apt-get install -y curl # Just like IRL, install curl first
RUN curl https://raw.githubusercontent.com/naddeoa/booty/master/scripts/booty-download-linux.sh | bash # MANUAL install booty without pip

# Copy my ssh keys in so I can clone my private repos
COPY ./ssh ./.ssh
RUN sudo chown -R myuser:myuser ./.ssh
RUN chmod 600 .ssh/id_rsa

COPY ./examples/install.booty ./

# This would be on my path IRL
ENV PATH="/home/myuser/.local/bin:${PATH}"

CMD ["bash"]

```

Then you build and run the image, and execute booty.

```bash
# Build the image
docker build . -t my-booty-test

# Run it
docker run --rm -it --entrypoint bash my-booty-test

## Inside the image now
./booty_linux_x86_64 -y
```

You can't test everything here but you can get pretty far. One thing I can't test here, for example, is `chsh` because that requires logging
out, but I gets me confident enough to use it on a fresh install and know I won't mess things up. In practice, you do this sort of a test
infrequently, when you initially create your `install.booty` file or when you make big changes to it.

# Syntax Support

See [naddeoa/vim-booty](https://github.com/naddeoa/vim-booty) for the syntax plugin.

# Booty Language

For full examples, check out the [examples](https://github.com/naddeoa/booty/tree/master/examples) folder in github.

The Booty language is a small language inspired primarily by make, with some additions to better address the problem space. There are a few
different types of entities.

## Recipes

Recipes are reusable pieces of code that Targets and other Recipes can invoke. You can think of these as classes that implement a `Recipe`
by defining the `setup` and `is_setup` methods. Recipes are invoked with parameters being separated by commas, like `recipe_name(foo, bar)`.
Parameters can optionally container whitespace as well, meaning `recipe_name(a b c)` is a single parameter `a b c`. The body of the recipe
methods consists of one or more executable statements which can either be a line to invoke in shell or another recipe invocation.

This is a recipe named `apt` who's `setup` executes the shell command `sudo apt-get install -y $((packages))`, where `$((packages))` will be
substituted by the value of the paraemter `packages` when it's run. Its `is_setup` executes a multiline shell statement. The shell is
invoked via `bash -c ...`.

```make
recipe apt(packages):
    setup: sudo apt-get install -y $((packages))
    is_setup:
      for pkg in $(echo $((packages)) | tr " " "\n"); do
        if ! dpkg -l "$pkg" &> /dev/null; then
          echo "$pkg is not installed."
          exit 1
        fi
      done
```

## Targets

Targets are the main piece of a booty file. They invoke a recipe to accomplish their goal. This is a target named `essentials` that invokes
the `apt`recipe, passing it the parameter `wget git vim autokey-gtk silversearcher-ag gawk xclip`.

```make
essentials: apt(wget git vim autokey-gtk silversearcher-ag gawk xclip)
```

## Custom Targets

Custom Targets are similar to recipes, but they're defined inline. You would use this for something that didn't require any code shared
between other recipes. The body of a Custom Target follows the same rules as a Recipe.

```make
pyenv:
    setup: curl https://pyenv.run | bash
    is_setup: test -e ~/.pyenv/bin/pyenv

# Can also be multiline and invoke different commands/recipes.
pyenv:
    setup:
        apt(python3)
        curl https://pyenv.run | bash
    is_setup: test -e ~/.pyenv/bin/pyenv
```

## Dependencies

Dependencies determine the execution order at setup time. The way that you declare this is flexible. You can use either the `depends on`
syntax (`->`) or the `depended upon` syntax (`<-`). This is allowed because it's sometimes easier to manage a bunch of dependencies in a
single line when they're logically related. Its personal preference for how you maintain your install.booty file.

```haskell
# the target `essentials` is depended upon by foo and bar.
essentials <- foo bar

# the target `baz` depends on bar.
baz -> bar
```

## Stdlib

Certain recipes are included in booty by default. These include the following.

```make
recipe apt(packages):
    setup: sudo apt-get install -y $((packages))
    is_setup:
      for pkg in $(echo $((packages)) | tr " " "\n"); do
        if ! dpkg -l "$pkg" &> /dev/null; then
          echo "$pkg is not installed."
          exit 1
        fi
      done

recipe ppa(name):
    setup:
        sudo add-apt-repository $((name))
        sudo apt update
    is_setup: grep $((name)) /etc/apt/sources.list

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

```

Any of these can be referenced from any booty.install file, and you can redifine them locally if you want different recipe logic that uses
the same name.

# FAQ

## Why wasn't make good enough?

You can check the [experiments](https://github.com/naddeoa/booty/blob/master/experiments/install.makefile) folder to see what it looks like
to implement the [example booty](https://github.com/naddeoa/booty/blob/master/examples/install.booty) file in make. It's a fair bit longer
and clunkier for a few reasons:

- Every target in make is designed to be an actual file. This great for building things but it means that you end up marking a lot of
  targets as `.PHONY` if they don't result in differences on the file system.
- Implementing the `--status` flag from booty is very, very ugly. You'll just manually define two modes of each target and hard code a phony
  target that runs them all, with no particular attention paid to the output.
- Same goes for running the setup code -- manually enumerating all targets as a phony target's dependency gets you the `--install` flag in
  booty.
- Output in general isn't very digestible.
- Each line of a target is executed in a new shell. Good for sandboxing commands but it gets very ugly when you want to do something like an
  `if` statement.

There are a lot of good things about make though. My favorite relevant parts are:

- Easy, independent dependency specification
- Plain old shell for each target definition.
