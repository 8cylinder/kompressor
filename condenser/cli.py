import sys
import click
import pathlib
from pathlib import Path
from condenser.condenser import Compress
from condenser.condenser import humanize
from typeguard import typechecked
import concurrent.futures

CONTEXT_SETTINGS = {
    'help_option_names':    ['-h', '--help'],
    'token_normalize_func': lambda x: x.lower(),
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('source',
                type=click.Path(resolve_path=True, path_type=Path, exists=True, dir_okay=False),
                required=True,
                nargs=-1)
@click.option('--output-dir', '-o', type=click.Path(resolve_path=True, path_type=Path, file_okay=False),
              help="Optional output dir.")
@click.option('--quality', '-q', type=click.IntRange(1, 100), default=70)
@click.option('--source-rename', '-s', type=click.STRING,
              help="Rename the source images to include this string.")
@click.option('--output-rename', '-r', type=click.STRING,
              help="Rename the output images to include this string.")
@typechecked
def condenser(
        source: tuple[pathlib.Path, ...],
        output_dir: pathlib.Path | None,
        quality: int,
        source_rename: str | None,
        output_rename: str | None,
) -> None:
    """Minify images to a smaller size using lossy compression.

    SOURCE can be a single image or a dir.

    Supported formats: png, jpeg, webp.

    \b
    These command line tools are required:
    `apt install pngquant jpegoptim webp`
    """
    image_types = ['.png', '.jpeg', '.jpg', '.webp']

    image_files: list[pathlib.Path] = []
    for file in source:
        file = file.absolute()
        if file.suffix in image_types:
            image_files.append(file)

    longest: int = 0
    for f in image_files:
        if len(f.name) > longest:
            longest = len(f.name)

    # Use ThreadPoolExecutor to process images in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for image_file in image_files:
            image = Compress(image_file, quality)
            if output_dir:
                image.output_dir = output_dir.absolute()
            if source_rename:
                image.source_rename = source_rename
            if output_rename:
                image.dest_rename = output_rename

            # Submit the compression task
            future = executor.submit(image.compress)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            try:
                image_data = future.result()
            except FileNotFoundError as e:
                print(f'Command not found: {e}')
                sys.exit(1)

            print(
                image_data.compressed_image.name.ljust(longest),
                humanize(image_data.original_size).rjust(6),
                '->',
                humanize(image_data.compressed_size).rjust(6),
            )
