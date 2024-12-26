
# 🪗 Kompressor

**Compress, convert and resize images.**


### Features

**Rename** — Modify the image name in multiple ways.  Add a string to
the source image, the compressed image, or both and put them in the
current dir or a subdir.

**Compress** — Compress the images on a 1-100 scale, with a default of 80.

**Resize** — Set a max width and height for the image.  The image will
be resized to fit within the bounds while maintaining the aspect
ratio.

**Trim** — Trim pixels from the sides of the image, by specifiying a
number of pixels from each site.  This is particularly usefull for
removing bad lines from the edges of images.

**Convert** — Convert the image to a different format.  Supported
formats are png, jpeg and webp.


### Renaming

Files can optionally have a string added to the end of the filename using
the `-s` and `-d` options.  The `-d` option renames the compressed image
and the `-s` option renames the source image.  These are applied whether it's
put into a subdir or not.

Eg, with an argument of `-ORIGINAL`, this file `image.jpg` would become
`image-ORIGINAL.jpg`.


### Requirements

Three command line tools are used for the actual compression,
pngquant, jpegoptim and cwebp.  Kompressor assumes they exist and are
in the PATH.

They can be installed with the following commands.

**Linux**:<br>
`apt install pngquant jpegoptim webp`

**Macos**:<br>
`brew install pngquant jpegoptim webp`

Also [UV](https://docs.astral.sh/uv/) is required to build the tool.
It can be installed with pipx or curl.  See the [UV install
docs](https://docs.astral.sh/uv/getting-started/installation/) for
more info.


### Installation

Installation is done from the git repo.

``` bash
cd /path/to/the/repo
uv sync
uv build
uv tool install ./dist/kompressor-XXXXX-py3-none-any.whl
# kompressor is now installed
```


### Usage

By default, if the `--output` option is not used, the compressed file
will be put in a subdir called "kompressor" in the same dir as the
source file.  It will be created if it doesn't exist.

Supported formats: png, jpeg, webp.

**Basic usage** — compress single or multiple images.  This will
create the `kompressor` dir and put the compressed image in it.

```bash
# single image
kompressor file.png

# multiple images
kompressor file1.png file2.png file3.png
# or
kompressor *.png
```

**Renaming files** — add a string to the end of the filename.

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

Setting the `--output` option to `.` will put the compressed image in
the same dir as the source image.  If you don't specify a rename flag,
you will get an error about the file already existing.

```bash
kompressor --output . --source-rename "-ORIGINAL" image.png
# new compressed image: ./image.png
# original image:       ./image-ORIGINAL.png

kompressor --output . --source-rename "-ORIGINAL" --destination-rename "-COMPRESSED" image.png
# new compressed image: ./image-COMPRESSED.png
# original image:       ./image-ORIGINAL.png
```

To generate multiple compressed images with different quality
settings, use a range.  The following example generates 3 compressed
images with different quality settings and puts them in the
'kompressor' directory.

```bash
for QUALITY in 10 50 80; do
  kompressor --quality=$QUALITY --destination-rename "-$QUALITY" *.png;
done

# ./kompressor/image-10.png
# ./kompressor/image-50.png
# ./kompressor/image-80.png
```

**Trim** — Cromp the image by removing a number of pixels from each
side.  The format for trimmng is `t10,r10,b10,l10`.  This trims 10
pixes from the top, right, bottom and left sides.  Use a comma to
separate the values.  Not all fields are required.

```bash
# trim 10 pixels from the top, right, bottom and left sides
kompressor --trim t10,r10,b10,l10 image.png
# trim 1 pixel from the top and 3 from the right side
kompressor --trim t1,r3 image.png
```

**Resize** — Scale the image to fit within the bounds of the width and
height.  The aspect ratio is maintained.

```bash
kompressor --resize 1000x1000 image.png
```

**Convert** — Convert the image to a different format.  Supported
formats are png, jpeg and webp.

```bash
# convert image.png to image.webp
kompressor --convert webp image.png
# new compressed image: ./kompressor/image.webp
# original image:       ./image.png

kompressor --convert png image.jpg -o .
# new compressed image: ./image.png
# original image:       ./image.jpg
```


### Output

Output can be human readable or json using the `--human` (default) or `--json` flag.

``` bash
uv run kompressor image-*.png  -c webp -d '-NEW' -x 1000 1000
```

```
image-01.png -> kompressor/image-01-NEW.webp | 208K ->  49K |  213367 ->  50642 | 1538 x  985 -> 1000 x  640
image-02.png -> kompressor/image-02-NEW.webp | 208K ->  49K |  213367 ->  50642 | 1538 x  985 -> 1000 x  640
image-03.png -> kompressor/image-03-NEW.webp | 6.3M -> 118K | 6644905 -> 120922 | 2080 x 1880 -> 1000 x  904
image-04.png -> kompressor/image-04-NEW.webp | 213K ->  52K |  217785 ->  53054 | 1538 x  985 -> 1000 x  640
image-05.png -> kompressor/image-05-NEW.webp | 6.5M -> 165K | 6775038 -> 168756 | 2080 x 1880 -> 1000 x  904
image-06.png -> kompressor/image-06-NEW.webp | 205K ->  49K |  209788 ->  49906 | 1538 x  985 -> 1000 x  640
image-07.png -> kompressor/image-07-NEW.webp | 6.1M ->  72K | 6374536 ->  73738 | 2080 x 1880 -> 1000 x  904
image-08.png -> kompressor/image-08-NEW.webp |  12K ->   3K |   11974 ->   2902 |  392 x  146 ->  392 x  146
image-09.png -> kompressor/image-09-NEW.webp |  17K ->   6K |   17827 ->   6478 |  430 x  146 ->  430 x  146
image-10.png -> kompressor/image-10-NEW.webp |  18K ->   5K |   18089 ->   5148 |  420 x  146 ->  420 x  146
image-11.png -> kompressor/image-11-NEW.webp |   3K ->   3K |    3467 ->   3568 |  380 x  146 ->  380 x  146
image-12.png -> kompressor/image-12-NEW.webp |   9K ->   3K |    9257 ->   2624 |  276 x  146 ->  276 x  146
image-13.png -> kompressor/image-13-NEW.webp |   4K ->   4K |    4509 ->   4224 | 1000 x 1000 -> 1000 x 1000
```

Using the `--json` flag, output will look like this.  Note I'm using
[jq](https://jqlang.github.io/jq/) to format the output.

``` bash
uv run kompressor image-{3,4}.png -x 100 100 --json | jq
```
``` json
[
  {
    "files": {
      "source": "/path/to/images/image-4.png",
      "compressed": "/path/to/images/kompressor/image-4.png"
    },
    "bytes": {
      "original_size": 217785,
      "compressed_size": 1561
    },
    "human": {
      "original_size": "213K",
      "compressed_size": "2K"
    },
    "original_dimensions": [
      1538,
      985
    ],
    "compressed_dimensions": [
      100,
      64
    ]
  },
  {
    "files": {
      "source": "/path/to/images/image-3.png",
      "compressed": "/path/to/images/kompressor/image-3.png"
    },
    "bytes": {
      "original_size": 6644905,
      "compressed_size": 7233
    },
    "human": {
      "original_size": "6.3M",
      "compressed_size": "7K"
    },
    "original_dimensions": [
      2080,
      1880
    ],
    "compressed_dimensions": [
      100,
      90
    ]
  }
]
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
