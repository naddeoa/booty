
# Overview
- can be extended via .sysc, don't require python
- can run targets in parallel
- can model dependencies
- can execute shell, including multiple things.
- everything executes in the user environment, no line-wise shell isolation like make
- can be tested via docker
- can dry run
- can show reports at the end
- can re-run things that need it
- can do configuration, not just installation (i.e. chsh)
- can generate a sequential sh script that effectively does what it was going to do
- can print dependency graph
- can show a nice, modern tui



- ~whitespace doesn't matter~ it makes the grammar nicer but it actually makes it a lot worse for the user unless I go full lisp. If I'm not
  going to ignore all of it then I might as well use it wherever it makes writing better.


# TODO
- Update the exection to show the current line from stdout on the row details. Going to be a little big to refactor
