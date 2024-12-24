
# 🪗 Kompressor

**Compress, convert and resize images.**

By default, if the `--output` option is not used, the compressed file will be put in
a subdir called "kompressor" in the same dir as the source file.  It
will be created if it doesn't exist.

Supported formats: png, jpeg, webp.

### Renaming

Files can optionally have a string added to the end of the filename using
the `-s` and `-d` options.  The `-d` option renames the compressed image
and the `-s` option renames the source image.  These are applied whether it's 
put into a subdir or not.

Eg, with an argument of `-ORIGINAL`, this file `image.jpg` would become
`image-ORIGINAL.jpg`.


### Requirements

Three command line tools are used for the actual compression, pngquant, jpegoptim and cwebp.  Kompressor assumes they exist and are in the PATH.

They can be installed with the following commands.

**Linux**:<br>
`apt install pngquant jpegoptim webp`

**Macos**:<br>
`brew install pngquant jpegoptim webp`

Also [UV](https://docs.astral.sh/uv/) is required to build the tool.  It can be installed with pipx or curl.  See the [UV install docs](https://docs.astral.sh/uv/getting-started/installation/) for more info.

### Installation

Installation is done from the git repo.  

``` bash
cd /path/to/the/repo
uv sync
uv build
uv tool install ./dist/kompressor-XXXXX-py3-none-any.whl
# kompressor is now installed
```

### Examples

**Basic usage** - compress single or multiple images.  This will create the `kompressor` dir and put the compressed image in it.

```bash
# single image
kompressor file.png

# multiple images
kompressor file1.png file2.png file3.png
# or
kompressor *.png
```

**Renaming files** - add a string to the end of the filename.

```bash
kompressor --destination-rename "-COMPRESSED" image.png
# new compressed image: ./kompressor/image-COMPRESSED.png

kompressor --source-rename "-ORIGINAL" image.png
# new compressed image: ./kompressor/image.png
# original image:       ./image-ORIGINAL.png

kompressor --source-rename "-ORIGINAL" --destination-rename "-COMPRESSED" image.png
# new compressed image: ./kompressor/image-COMPRESSED.png
# original image:       ./image-ORIGINAL.png
```

Setting the `--output` option to `.` will put the compressed image in the same dir as the source image.  If you don't specify a rename flag, you will get an error about the file already existing.

```bash
kompressor --output . --source-rename "-ORIGINAL" image.png
# new compressed image: ./image.png
# original image:       ./image-ORIGINAL.png

kompressor --output . --source-rename "-ORIGINAL" --destination-rename "-COMPRESSED" image.png
# new compressed image: ./image-COMPRESSED.png
# original image:       ./image-ORIGINAL.png
```

To generate multiple compressed images with different quality settings, use a range.
The following example generates 3 compressed images with different quality
settings and puts them in the 'kompressor' directory.

```bash
for QUALITY in 10 50 80; do
  echo "Quality: $QUALITY --------------------";
  kompressor --quality=$QUALITY --destination-rename "-$QUALITY" *.png;
done

# ./kompressor/image-10.png
# ./kompressor/image-50.png
# ./kompressor/image-80.png
```


### Development

#### Run
`uv run kompressor --help`

#### Build
`uv build`

#### Install
`pipx install ./dist/kompressor-XXXXX-py3-none-any.whl`

`uv tool install ./dist/kompressor-XXXXX-py3-none-any.whl`

#### Install editable
`uv tool install --editable .`
