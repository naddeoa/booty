
<p align="center"><img src="https://raw.githubusercontent.com/naddeoa/booty/master/static/booty-logo-bg-sm.png"/></p> </br>

Booty is a language and command line utility for bootstrapping the setup of peronal OS installs. It's goal is to execute all of the things
that you do after your first boot, like install packges through your package manager, configure your shell, setup your terminal tools/IDE,
and install SDKs for various programming languages, without you having to download everything manually and run various scripts in the right
order.

You model your setup process as Targets and declare which ones depend on which ones, then execute `booty` to set everything up, if
everything isn't alrady setup.

<p align="center"><img src="https://raw.githubusercontent.com/naddeoa/booty/master/static/booty-status.jpg"/></p> </br>


# Install

Installing from pip

```bash
pip install booty-cli
```

Or download the appropriate binary from the latest release. This script just downloads it for you and marks it as executable, but you should
move it somewhere on your path. The script will drop it in your `pwd`.

```bash
# Linux
curl https://raw.githubusercontent.com/naddeoa/booty/master/scripts/booty-download-linux.sh | bash

# Mac x86
curl https://raw.githubusercontent.com/naddeoa/booty/master/scripts/booty-download-mac-x86.sh | bash

# Mac Arm
curl https://raw.githubusercontent.com/naddeoa/booty/master/scripts/booty-download-mac-universal.sh | bash
```

## Syntax

A simple syntax definition is available for vim/nvim. This can be placed in `~/.config/nvim/syntax/booty.vim`, for example. This will be
updated with a dedicated repo soon.

```syntax
syntax clear

syntax region bootyArgs start=/(/ end=/)/ contains=@Spell
syntax region bootyParams start=/$((/ end=/))/ contains=@Spell
syntax match bootyTargetName "\v^\zs[^ \t:]+\ze:.*"
syntax match bootyTargetDependenciesName "\v^\zs[^ \t]+\ze\s+(-\>|\<-).*"
syntax match bootyImplementsName "\v^\s+\zs[^ \t:]+\ze:.*"
syntax keyword bootyKeyword recipe setup is_setup
syntax match bootyOpDependsOn "->"
syntax match bootyOpDependedUpon "<-"
syntax match bootyComment "^#.*$"

highlight link bootyComment Comment
highlight link bootyKeyword Keyword
highlight link bootyOpDependsOn Operator
highlight link bootyOpDependedUpon Operator
highlight link bootyTargetName Function
highlight link bootyTargetDependenciesName Function
highlight link bootyImplementsName Function
highlight link bootyRecipeCall Funciton
highlight link bootyArgs String
highlight link bootyParams Type

```


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

```booty
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
the `apt`recipe, passing it the paramter `wget git vim autokey-gtk silversearcher-ag gawk xclip`.

```booty
essentials: apt(wget git vim autokey-gtk silversearcher-ag gawk xclip)
```

## Custom Targets

Custom Targets are similar to recipes, but they're defined inline. You would use this for something that didn't require any code shared
between other recipes. The body of a Custom Target follows the same rules as a Recipe.

```booty
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
syntax (`->`) or the `depended upon` syntax (`<-`). This is allowed because its sometimes easier to manage a bunch of dependencies in a
single line when they're logically related. Its personal preference for how you maintain your install.booty file.

```booty
# the target `essentials` is depended upon by foo and bar.
essentials <- foo bar

# the target `baz` depends on bar.
baz -> bar
```

## Stdlib

Certain recipes are included in booty by default. These include the following.

```booty
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
```

Any of these can be referenced from any booty.install file.



