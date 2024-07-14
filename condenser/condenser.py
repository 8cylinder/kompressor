#!/usr/bin/env python3
import sys
import os
import shlex
import pathlib
from pathlib import Path
import tempfile
import click
from pprint import pprint as pp
#from PIL import Image
import subprocess
from typeguard import typechecked
import concurrent.futures


# from IPython.core.debugger import set_trace; set_trace()


@typechecked
def get_files_by_extension(path: os.PathLike, image_types: list) -> list:
    """Return a list of image files in the given path that match the image types."""
    image_files = []  # extension
    for image_type in image_types:
        image_files.extend(Path(path).glob(f'*.{image_type}'))
    return image_files


@typechecked
def humanize(bytes: int) -> str:
    """Convert a size in bytes to a human-readable format."""
    units = ['bytes', 'KB', 'MB', 'GB']
    index = 0

    # Convert the size to a higher unit until it's less than 1024
    while bytes >= 1024 and index < len(units) - 1:
        bytes = round(bytes / 1024)
        index += 1

    # Format the size to 2 decimal places
    bytes = round(bytes, 2)

    return f'{bytes} {units[index]}'


@typechecked
class Compress:
    """
    A class to compress image files using specified quality
    settings.

    This class supports JPEG, PNG, and WEBP formats, utilizing
    external tools (jpegoptim, pngquant, webp) for compression.
    These tools must be installed and accessible in the system's
    PATH.

    Attributes:
        source_image (Path): Path to the source image.
        quality (int): Compression quality setting.
        output_dir (Path): Directory for the compressed image.
        types (dict): Mapping of file extensions to formats.

    Methods:
        compress(): Compresses the source image and saves it.
                    Returns original and compressed sizes.
        _get_type(): Determines the image format.
        run_cmd(cmd: str): Executes a shell command.
    """
    types: dict[str, str] = {
        'png':  'png',
        'jpeg': 'jpeg',
        'jpg':  'jpeg',
        'webp': 'webp',
    }

    def __init__(self, source_image: pathlib.Path, quality: int = 70):
        self.source_image: pathlib.Path = source_image
        self.quality: int = quality
        self._output_dir: pathlib.Path | None = None
        self._source_rename: str = ''
        self._dest_rename: str = ''

    # output dir
    @property
    def output_dir(self) -> pathlib.Path:
        return self._output_dir

    @output_dir.setter
    def output_dir(self, output_dir: pathlib.Path) -> None:
        self._output_dir = output_dir

    # source rename string
    @property
    def source_rename(self) -> str:
        return self._source_rename

    @source_rename.setter
    def source_rename(self, source_rename: str) -> None:
        self._source_rename = source_rename

    # dest rename string
    @property
    def dest_rename(self) -> str:
        return self._dest_rename

    @dest_rename.setter
    def dest_rename(self, dest_rename: str) -> None:
        self._dest_rename = dest_rename

    # -----------------------------------------

    def _get_type(self) -> str:
        type: str = self.source_image.suffix
        type = type[1:]  # remove the leading dot
        if type in self.types:
            return self.types[type]
        else:
            raise ValueError(f'Unsupported image type: {type}')

    def compress_jpeg(self, output_name: str) -> pathlib.Path:
        """
        Compresses a JPEG image to a specified quality and moves it to the output
        directory with a new name.

        Parameters:
            output_name (str): The new name for the compressed image file. This name
                               is used when moving the file to the output directory.

        Returns:
            pathlib.Path: The path to the compressed image in the output directory.

        Raises:
            subprocess.CalledProcessError: If the `jpegoptim` command fails.
        """
        with tempfile.TemporaryDirectory() as tmp:
            cmd: list = [
                'xjpegoptim', '--quiet', '--overwrite', '--strip-exif', '--max', self.quality,
                '--dest', tmp, self.source_image
            ]
            # compress the image to the tmp dir
            self.run_cmd(cmd)

            compressed_image: pathlib.Path = Path(tmp) / self.source_image.name

            # move the compressed image to the output directory
            compressed_image: pathlib.Path = compressed_image.rename(self._output_dir / Path(output_name))
            return compressed_image

    def compress_png(self, output_name: str) -> pathlib.Path:
        out: pathlib.Path = self._output_dir / Path(output_name)
        quality: str = f'0-{self.quality}'
        cmd = ['pngquant', '--force', '--quality', quality, '--output', out, self.source_image]
        self.run_cmd(cmd)
        return out


    def compress_webp(self, output_name: str) -> None:
        print('compress_webp')
        # cmd = ['webp', '-q', self.quality, self.source_image, '-o', self.output_dir]

    def run_cmd(self, cmd: list):
        cmd: list[str] = [str(i) for i in cmd]
        # merged_cmd: str = shlex.join(cmd)
        # print(merged_cmd)
        # return

        result: subprocess.CompletedProcess = subprocess.run(cmd, capture_output=True)

        # try:
        #     result: subprocess.CompletedProcess = subprocess.run(cmd, capture_output=True)
        # except subprocess.CalledProcessError as e:
        #     raise FileNotFoundError(f'Command not found: {cmd}, {e}')
        # except FileNotFoundError as e:
        #     raise FileNotFoundError(f'xxxFile not found: {cmd}, {e}')
        # print('>>>', result)

    @staticmethod
    def create_new_name(name: pathlib.Path, suffix: str):
        new_name = name.stem + suffix + name.suffix
        return new_name

    def compress(self):
        """
        Compresses the source image using the specified quality setting.

        This method determines the image type (JPEG, PNG, or WEBP) of the
        source image, applies the appropriate compression command, and
        saves the compressed image to the output directory.

        The compression process is performed using external tools
        (`jpegoptim` for JPEGs, `pngquant` for PNGs, and `webp` for WEBP
        images), which must be installed and accessible in the system's
        PATH.

        The method calculates the original and compressed sizes of the
        image, returning both values for further use.

        Raises:
            ValueError: If the image type is unsupported or if the external
                        compression tool encounters an error.
            Exception: If the subprocess call to the external compression tool fails.

        Returns:
            tuple: A tuple containing the original size and compressed
                   size of the image, both in bytes.
        """

        # SVG cleaner - https://github.com/scour-project/scour

        original_size: int = self.source_image.stat().st_size

        # if nothing is set, default to 'condensed' dir
        if not self._source_rename and not self._dest_rename and not self._output_dir:
            self._output_dir = Path('condensed')

        # create the output dir if it doesn't exist
        if self._output_dir and not self._output_dir.exists():
            self._output_dir.mkdir(parents=True)

        # if the output_dir is not set, set it to the current dir
        if not self._output_dir:
            self._output_dir = Path('.').absolute()

        output_name: str = self.source_image.name
        # rename the output if requested and base it off the original name without the
        # self._source_rename value.
        if self._dest_rename:
            if self._source_rename in output_name:
                output_name = output_name.replace(self._source_rename, '')
            output_name = self.create_new_name(Path(output_name), self._dest_rename)

        image_type: str = self._get_type()

        # pp({
        #     'source rename': self._source_rename,
        #     'dest rename': self._dest_rename,
        #     'output dir': self._output_dir,
        #     'source image': self.source_image,
        #     'output name': output_name,
        #     'image type': image_type,
        # })

        if image_type == 'jpeg':
            compressed_image = self.compress_jpeg(output_name)
        elif image_type == 'png':
            compressed_image = self.compress_png(output_name)
        elif image_type == 'webp':
            compressed_image = self.compress_webp(output_name)
        else:
            raise ValueError(f'Unsupported image type: {image_type}')

        # rename source if requested, but only if it hasn't already been renamed.
        if self.source_rename and not self.source_rename in self.source_image.name:
            new_source_name: str = self.create_new_name(self.source_image, self.source_rename)
            self.source_image = self.source_image.rename(new_source_name)

        compressed_size: int = compressed_image.stat().st_size

        return compressed_image, original_size, compressed_size
