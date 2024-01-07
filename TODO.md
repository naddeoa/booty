
# TODO

Some features that might be useful. If you feel up to contributing then these could be a good starting place.

- Language spec
- import system and package system

- Debug display issues with scrolling/collapsing tree during steup. This probably because the height of the table decreases and then the
  tallest area is "orphaned". I probably have to have a constant wosrt case padding at the bottom of the table, wich would be 12 lines?
- Refactor release process to delay the release creation until the last step. There is a period now where the copy/paste install fails
  because the new release binaries haven't been uploaded to the release yet.
- Timeouts for the installs
- Global variables. This would probably look just like make variables.
- Windows support. For all I know it already works, but I don't use Windows. It would be good to get a binary building for Windows users.
- Confirm the mac binaries work. I only use Linux personally.
