
# Condenser

Compress jpegs, pngs or webp images.  This uses pngquant, jpegoptim
and cwebp to do the actual compression.

The source filename and the output filename can be renamed and a
destination dir can be specified.

By default, if no options are used, the compressed file will be put in
a subdir called "condensed" in the same dir as the source file.  It
will be created if it doesn't exist.

### Run
`poetry run condenser --help`

Or if installed,

`condenser --help`

### Build
`poetry build`

### Install
`pipx install ./dist/condenser-XXXXX-py3-none-any.whl`

### Install editable
`pipx install --editable .`

### Tests
`poetry run pytest`
