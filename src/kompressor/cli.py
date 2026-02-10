import sys
import os
import click
import pathlib
import re
from pathlib import Path
import concurrent.futures
from pprint import pprint as pp  # noqa: F401
import shutil
import json
from .kompressor import Compress
from .kompressor import ImageData
from .kompressor import humanize
from typing import Any


QUALITY = 80
BAR = " | "
ARROW = " -> "
X = "x"


def get_files(ctx: Any, param: Any, value: str) -> list[pathlib.Path] | str:
    if not value and not click.get_text_stream("stdin").isatty():
        filenames = click.get_text_stream("stdin").read().strip()
        images = []
        for f in filenames.split("\n"):
            image_file = Path(f)
            if not image_file.exists():
                raise click.BadParameter(f"File '{image_file}' does not exist.")
            if not image_file.is_file():
                raise click.BadParameter(f"File '{image_file}' must be a dir.")
            images.append(image_file.absolute())
        return images
    else:
        if not value:
            param_name = param.name.upper()
            raise click.UsageError(f"Missing argument '{param_name}...'.", ctx=ctx)
        return value


CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "token_normalize_func": lambda x: x.lower(),
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "source",
    required=False,
    nargs=-1,
    callback=get_files,
    type=click.Path(resolve_path=True, path_type=Path, exists=True, dir_okay=False),
)
@click.option(
    "--output-dir",
    "-o",
    default="kompressor",
    type=str,
    help='Optional output dir, defaults to "kompressor" in each image\'s directory.',
)
@click.option(
    "--quality",
    "-q",
    type=click.IntRange(1, 100),
    default=QUALITY,
    help=f"Quality of the compressed image(s), default is {QUALITY}.",
)
@click.option(
    "--destination-rename",
    "-d",
    type=click.STRING,
    help="Rename the output images to include this string.",
)
@click.option(
    "--source-rename",
    "-s",
    type=click.STRING,
    help="Rename the original images to include this string.",
)
@click.option(
    "--convert",
    "-c",
    type=click.Choice(["jpeg", "png", "webp", "avif"]),
    help="Convert the image(s) to a different format.",
)
@click.option(
    "--dimensions",
    "-x",
    "size",
    type=str,
    help="Shrink the image(s) to the specified dimensions.  Format: w,h. Use a comma to separate the values.  If only one value is specified that will be used as the width.",
)
@click.option(
    "--table/--json",
    default=True,
    help="Output format as a table or json, default: table.",
)
@click.option(
    "--trim",
    help='Trim pixels from the edges of the image.  Format (top, right, bottom, left): "tX,rX,bX,lX".  Not all four fields are required, eg: "t1,r10',
)
@click.option(
    "--strip-exif",
    "-e",
    is_flag=True,
    help="(Experimental) Strip all exif tags.",
)
@click.option(
    "--slugify/--no-slugify",
    default=False,
    help=(
        "Slugify the new filename, except for any strings added via the -d flag."
        "If the -s flag is used, both files will be slugified.  Default: no."
    ),
)
@click.option("--compress/--no-compress", default=True)
@click.option(
    "--write-cmd/--no-write-cmd",
    default=True,
    help="Write the command used to run kompressor to a file in the output dir.  Default: yes.",
)
@click.version_option()
def kompressor(
    source: tuple[pathlib.Path, ...],
    output_dir: str,
    quality: int,
    source_rename: str | None,
    destination_rename: str | None,
    convert: str | None,
    size: str | None,
    table: bool,
    trim: str | None,
    strip_exif: bool,
    compress: bool,
    slugify: bool,
    write_cmd: bool,
) -> None:
    """🪗 Minify/resize/convert images using lossy compression.

    SOURCE can be one or more image files.

    By default, the compressed images are saved in a dir called 'kompressor',
    unless overridden with the '-o' option.  It will be created if necessary.

    Supported formats: png, jpeg, webp and avif.

    \b
    Renaming
    --------

    Files can optionally have a string added to the end of the filename using
    the '-s' and '-d' options.  The -d option renames the compressed image
    and the -s option renames the source image.

    Eg, with an argument of '-ORIGINAL', this file 'image.jpg' would become
    image-ORIGINAL.jpg.

    \b
    Requirements
    ------------

    \b
    These command line tools are required:
    `apt install pngquant jpegoptim webp`
    `brew install pngquant jpegoptim webp`
    `flox install pngquant jpegoptim libwebp`
    `npm install avif`
    """

    image_types = [".png", ".jpeg", ".jpg", ".webp"]
    image_files: list[pathlib.Path] = []
    for file in source:
        file = file.absolute()
        if file.suffix.lower() in image_types:
            image_files.append(file)

    longest_filename: int = 0
    for f in image_files:
        if len(f.name) > longest_filename:
            longest_filename = len(f.name)
    longest_filename = (
        longest_filename + len(destination_rename)
        if destination_rename
        else longest_filename
    )

    trims = {}
    if trim:
        trims = {"t": 0, "r": 0, "b": 0, "l": 0}
        values = trim.split(",")
        trims.update({i[0]: int(i[1:]) for i in values})

    # Use ThreadPoolExecutor to process images in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for image_file in image_files:
            image = Compress(image_file, quality, output_dir)
            image.do_compress = compress
            if destination_rename:
                image.dest_extra_name = destination_rename
            if source_rename:
                image.source_extra_name = source_rename
            if size:
                size = re.sub(r"\D+$", "", size)  # remove a trailing comma
                split = tuple(map(int, size.split(",")))
                width = split[0]
                height = split[1] if len(split) > 1 else 1_000_000_000
                image.size = (width, height)
            image.convert = convert
            image.trim = trims
            image.strip_exif = strip_exif
            image.slugify = slugify

            # Submit the compression task
            future = executor.submit(image.compress)
            futures.append(future)

        images_data = []
        with click.progressbar(
            futures,
            show_percent=False,
            width=0,
            fill_char=click.style("■", fg=(165, 152, 250)),
            empty_char=click.style("■", fg=(32, 35, 102)),
            bar_template="%(bar)s",
        ) as bar:
            for future in bar:
                try:
                    image_data = future.result()
                except FileNotFoundError as e:
                    click.secho(f"File not found: {e}", fg="red")
                    sys.exit(1)
                except shutil.SameFileError as e:
                    click.secho(f"{e}", fg="red")
                    click.secho(
                        'Try renaming the source image with the "-s" option.',
                        fg="bright_red",
                    )
                    sys.exit(1)
                except OSError as e:
                    click.secho(e, fg="red")
                    sys.exit(1)

                images_data.append(image_data)

        if table:
            sys.stdout.write("\033[1A")  # Move cursor up one line
            sys.stdout.write(" " * os.get_terminal_size().columns)  # Clear line
            sys.stdout.write("\033[1A")  # Move cursor up one line
            print()
            table_data, column_widths = display_info(images_data, strip_exif)
            print_table(table_data, column_widths)
        else:
            click.echo(image_data_2_json(images_data))

        if images_data and write_cmd:
            cmd_write_dir = images_data[0].compressed_image.parent
            write_command(cmd_write_dir)


def write_command(output_dir: Path) -> None:
    """Write the command used to run kompressor to a file."""
    cmd_file = output_dir / ".kompressor-cmd"
    cmd = " ".join(sys.argv)
    with open(cmd_file, "w") as f:
        f.write(cmd)


def image_data_2_json(images_data: list[ImageData]) -> str:
    image_data = []
    for image in images_data:
        image_data.append(
            {
                "files": {
                    "source": str(image.source_image),
                    "compressed": str(image.compressed_image),
                },
                "bytes": {
                    "original_size": image.original_size,
                    "compressed_size": image.compressed_size,
                },
                "human": {
                    "original_size": humanize(image.original_size),
                    "compressed_size": humanize(image.compressed_size),
                },
                "original_dimensions": image.original_dimension,
                "compressed_dimensions": image.compressed_dimension,
            }
        )
    json_data: str = json.dumps(image_data)
    return json_data


def display_info(
    images_data: list[ImageData], strip_exif: bool
) -> tuple[list[list[str]], list[int]]:
    column_widths = [0 for i in range(50)]
    table_data = []
    compressed_sizes = []
    exif_status = []
    current_dir = Path().absolute()
    for image_data in images_data:
        percent = int(
            round(image_data.compressed_size * 100 / image_data.original_size, 0)
        )
        source_name = snip(image_data.source_image.name, 30, 0.3)
        compressed_partial_path = image_data.compressed_image.relative_to(current_dir)
        compressed_name = f"{compressed_partial_path.parent}/{snip(compressed_partial_path.name, 30, 0.3)}"

        text = [
            # filename
            click.style(str(source_name), fg="bright_blue"),
            ARROW,
            click.style(str(compressed_name), fg="bright_green"),
            BAR,
            # human file size
            click.style(humanize(image_data.original_size), fg="bright_blue"),
            ARROW,
            click.style(humanize(image_data.compressed_size), fg="bright_green"),
            BAR,
            # percent
            click.style(f"{percent}%", fg="bright_green"),
            BAR,
            # dimensions
            click.style(str(image_data.original_dimension[0]), fg="bright_blue"),
            X,
            click.style(str(image_data.original_dimension[1]), fg="bright_blue"),
            # exif status
        ]
        if image_data.compressed_dimension:
            compressed_sizes = [
                # changed dimensions
                ARROW,
                click.style(str(image_data.compressed_dimension[0]), fg="bright_green"),
                X,
                click.style(str(image_data.compressed_dimension[1]), fg="bright_green"),
            ]
        if strip_exif:
            exif_status = [
                # exif status
                BAR,
                click.style("Y", fg="bright_green")
                if image_data.exif_stripped
                else click.style("N", fg="bright_yellow"),
            ]
        text = text + compressed_sizes + exif_status

        table_data.append(text)

        for i, col in enumerate(text):
            if len(col) > column_widths[i]:
                column_widths[i] = len(col)
    return table_data, column_widths


def print_table(table_data: list[list[str]], column_widths: list[int]) -> None:
    for row in sorted(table_data):
        for i, col in enumerate(row):
            if i <= 3:
                click.secho(col.ljust(column_widths[i]), nl=False)
            else:
                click.secho(col.rjust(column_widths[i]), nl=False)
        print()


def snip(string: str, length: int, position: float = 0.5) -> str:
    """Split a string at the position of a separator and return the two parts.

    :param string: The string to split.
    :param length: The length of the string to return.
    :param sep: The separator to use between the two parts of the string.
    :param position: The position of the separator.
    """
    sep = "…"
    if len(string) <= length:
        return string

    sep_length = len(sep)
    sep_position = int(length * position)
    sep_position = (
        sep_position - sep_length
        if sep_position + sep_length > length
        else sep_position
    )
    start = string[:sep_position]
    end = string[sep_position + sep_length - length :]
    snipped = start + sep + end
    # return start, end
    return snipped
