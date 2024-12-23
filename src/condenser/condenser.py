import pathlib
from pathlib import Path
import tempfile
import subprocess
from dataclasses import dataclass


# from IPython.core.debugger import set_trace; set_trace()


@dataclass
class ImageData:
    compressed_image: Path
    source_image: Path
    original_size: int
    compressed_size: int


def get_files_by_extension(path: str, wanted_filetypes: list[str]) -> list[Path]:
    """Return a list of image files in the given path that match the image types."""
    image_files: list[Path] = []  # extension
    for image_type in wanted_filetypes:
        image_files.extend(Path(path).glob(f"*.{image_type}"))
    return image_files


def humanize(size: int) -> str:
    """Convert a size in bytes to a human-readable format."""
    units = ["B", "K", "M", "G"]
    index = 0

    # Convert the size to a higher unit until it's less than 1024
    precise_size: float = float(size)
    while precise_size >= 1024 and index < len(units) - 1:
        precise_size = precise_size / 1024
        index += 1

    if index >= 2:
        pretty_size = round(size, 1)
    else:
        pretty_size = round(size)

    return f"{pretty_size}{units[index]}"


class Compress:
    """
    A class to compress a single image using specified quality
    settings.

    This class supports JPEG, PNG, and WEBP formats, utilizing
    external tools (jpegoptim, pngquant, webp) for compression.
    These tools must be installed and accessible in the system's
    PATH.
    """

    types: dict[str, str] = {
        "png": "png",
        "jpeg": "jpeg",
        "jpg": "jpeg",
        "webp": "webp",
    }

    def __init__(
        self, source_image: pathlib.Path, quality: int, output_dir: pathlib.Path
    ):
        self.source_image: pathlib.Path = source_image
        self.quality: int = quality
        self._output_dir: pathlib.Path = output_dir
        self._dest_rename: str = ""

    @property
    def dest_rename(self) -> str:
        return self._dest_rename

    @dest_rename.setter
    def dest_rename(self, dest_rename: str) -> None:
        self._dest_rename = dest_rename

    def _get_type(self) -> str:
        image_type: str = self.source_image.suffix
        image_type = image_type[1:].lower()  # remove the leading dot
        if image_type in self.types:
            return self.types[image_type]
        else:
            raise ValueError(f"Unsupported image type: {image_type}")

    def compress_jpeg(self, output_name: str) -> Path:
        """Compresses a JPEG image to a specified quality and moves it to the
        output directory with a new name.

        jpegoptim doesn't allow renaming of the file when compressing, so we
        need to use a temporary directory to store the compressed image before
        moving it to the output directory and renaming.

        Raises:
            subprocess.CalledProcessError: If the `jpegoptim` command fails.
        """
        with tempfile.TemporaryDirectory() as tmp:
            # fmt: off
            cmd = [
                "jpegoptim", "--quiet", "--overwrite", "--strip-exif",
                "--max", str(self.quality),
                "--dest", tmp,
                str(self.source_image),
            ]
            # fmt: on

            # compress the image to the tmp dir
            self.run_cmd(cmd)

            compressed_image: Path = Path(tmp) / self.source_image.name

            # move the compressed image to the output directory
            compressed_image = compressed_image.rename(
                self._output_dir / Path(output_name)
            )
            compressed_image = compressed_image.absolute()
            return compressed_image

    def compress_png(self, output_name: str) -> Path:
        out: Path = self._output_dir / Path(output_name)
        quality: str = f"0-{self.quality}"
        # fmt: off
        cmd = [
            "pngquant", "--force",
            "--quality", quality,
            "--output", str(out),
            str(self.source_image),
        ]
        # fmt: on
        self.run_cmd(cmd)
        return out

    def compress_webp(self, output_name: str) -> Path:
        out: Path = self._output_dir / Path(output_name)
        cmd = ["cwebp", "-q", str(self.quality), str(self.source_image), "-o", str(out)]
        self.run_cmd(cmd)
        return out

    @staticmethod
    def run_cmd(cmd: list[str]) -> None:
        cmd = [str(i) for i in cmd]
        subprocess.run(cmd, capture_output=True)

    @staticmethod
    def create_new_name(name: Path, suffix: str) -> str:
        new_name = name.stem + suffix + name.suffix
        return new_name

    def compress(self) -> ImageData:
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

        # create the output dir if it doesn't exist
        if self._output_dir:
            try:
                self._output_dir.mkdir(parents=True)
            except FileExistsError:
                # in multi-threaded environments, this directory may have been created
                pass

        # if the output_dir is not set, set it to the current dir
        if not self._output_dir:
            self._output_dir = Path(".").absolute()

        output_name: str = self.source_image.name
        # rename the output
        if self._dest_rename:
            output_name = self.create_new_name(Path(output_name), self._dest_rename)

        image_type: str = self._get_type()
        if image_type == "jpeg":
            compressed_image = self.compress_jpeg(output_name)
        elif image_type == "png":
            compressed_image = self.compress_png(output_name)
        elif image_type == "webp":
            compressed_image = self.compress_webp(output_name)
        else:
            raise ValueError(f"Unsupported image type: {image_type}")

        compressed_size: int = compressed_image.stat().st_size

        data = ImageData(
            compressed_image, self.source_image, original_size, compressed_size
        )
        return data
