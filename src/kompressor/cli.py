import json
import sys
import click
import pathlib
from pathlib import Path
from .kompressor import Compress, ImageData  # type: ignore
from .kompressor import humanize
import concurrent.futures
from pprint import pprint as pp  # noqa: F401
from typing import Any


QUALITY = 80

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "token_normalize_func": lambda x: x.lower(),
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "source",
    required=True,
    nargs=-1,
    type=click.Path(resolve_path=True, path_type=Path, exists=True, dir_okay=False),
)
@click.option(
    "--output-dir",
    "-o",
    default="kompressor",
    type=click.Path(resolve_path=True, path_type=Path, file_okay=False),
    help='Optional output dir, defaults to "kompressor".',
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
    type=click.Choice(["jpeg", "png", "webp"]),
    help="Convert the image(s) to a different format.",
)
@click.option(
    "--dimensions",
    "-x",
    "size",
    type=(int, int),
    default=(0, 0),
    help="Resize the image(s) to the specified dimensions.",
)
@click.option(
    "--human/--json",
    default=True,
    help="Output format in human readable or json, default: human.",
)
@click.version_option()
def kompressor(
    source: tuple[pathlib.Path, ...],
    output_dir: pathlib.Path,
    quality: int,
    source_rename: str | None,
    destination_rename: str | None,
    convert: str | None,
    size: tuple[int, int],
    human: bool,
) -> None:
    """🪗 Minify/resize/convert images using lossy compression.

    SOURCE can be one or more image files.

    By default, the compressed images are saved in a dir called 'kompressor',
    unless overridden with the '-o' option.  It will be created if nessesary.

    Supported formats: png, jpeg, webp.

    To generate compressed images with different quality settings, use a range.
    The following example generates 3 compressed images with different quality
    settings and puts them in the 'kompressor' directory.

    \b
    for QUALITY in 10 50 80; do
      echo "Quality: $QUALITY --------------------";
      kompressor --quality=$QUALITY --destination-rename "-$QUALITY" *.png;
    done

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

    # Use ThreadPoolExecutor to process images in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for image_file in image_files:
            image = Compress(image_file, quality, output_dir)
            if destination_rename:
                image.dest_extra_name = destination_rename
            if source_rename:
                image.source_extra_name = source_rename
            image.size = size
            image.convert = convert

            # Submit the compression task
            future = executor.submit(image.compress)
            futures.append(future)

        images_data = []
        for future in concurrent.futures.as_completed(futures):
            try:
                image_data = future.result()
            except FileNotFoundError as e:
                click.secho(f"Command not found: {e}", fg="red")
                sys.exit(1)
            except OSError as e:
                click.secho(e, fg="red")
                sys.exit(1)

            images_data.append(image_data)

        if human:
            display_info(images_data)
        else:
            image_data_dict = json.dumps(image_data_2_dict(images_data))
            click.echo(image_data_dict)


def image_data_2_dict(images_data: list[ImageData]) -> dict[str, Any]:
    image_data_dict = {}
    for image in images_data:
        image_data_dict[image.compressed_image.name] = {
            "bytes": {
                "original_size": image.original_size,
                "compressed_size": image.compressed_size,
            },
            "human": {
                "original_size": humanize(image.original_size),
                "compressed_size": humanize(image.compressed_size),
            },
            "dimensions": image.sizes,
        }
    return image_data_dict


def display_info(images_data: list[ImageData]) -> None:
    column_widths = [0 for i in range(50)]
    table_data = []
    arrow = " -> "
    x = " x "
    for image_data in images_data:
        text = [
            image_data.compressed_image.name,
            "   ",
            humanize(image_data.original_size),
            arrow,
            humanize(image_data.compressed_size),
            " | ",
            str(image_data.original_size),
            arrow,
            str(image_data.compressed_size),
        ]
        if len(image_data.sizes) == 1:
            sizes = [
                " | ",
                str(image_data.sizes[0][0]),
                x,
                str(image_data.sizes[0][1]),
            ]
        else:
            sizes = [
                " | ",
                str(image_data.sizes[0][0]),
                x,
                str(image_data.sizes[0][1]),
                arrow,
                str(image_data.sizes[1][0]),
                x,
                str(image_data.sizes[1][1]),
            ]
        text = text + sizes

        table_data.append(text)
        for i, col in enumerate(text):
            if len(col) > column_widths[i]:
                column_widths[i] = len(col)
    print_table(table_data, column_widths)


def print_table(table_data: list[list[str]], column_widths: list[int]) -> None:
    for row in table_data:
        for i, col in enumerate(row):
            if i == 0:
                click.secho(col.ljust(column_widths[i]), nl=False)
            else:
                click.secho(col.rjust(column_widths[i]), nl=False)
        print()
