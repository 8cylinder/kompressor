import pytest
from click.testing import CliRunner
from pathlib import Path
from condenser.condenser import get_files_by_extension
from condenser.condenser import humanize
from condenser.condenser import Compress
import tempfile
from pprint import pprint as pp
import uuid
from typeguard import typechecked
from condenser.generate_image import generate_test_image


# pytest
# pytest -rP

@pytest.fixture
def runner():
    return CliRunner()


@typechecked
def test_humanize_formatting():
    numbers: dict[str, int] = {
        "1 bytes": 1,
        "10 bytes": 10,
        "100 bytes": 100,
        "1000 bytes": 1000,
        "10 KB": 10_000,
        "98 KB": 100_000,
        "977 KB": 1_000_000,
        "10 MB": 10_000_000,
        "954 MB": 1_000_000_000,
    }
    for expected, number in numbers.items():
        assert humanize(number) == expected, f"Should format {number} as {expected}"


@pytest.fixture
@typechecked
def sample_images_setup():
    with tempfile.TemporaryDirectory() as tmpdir:
        id = str(uuid.uuid4()).split('-')[-1]
        sample_images: dict[str, str] = {
            f'sample-{id}.jpg': 'JPEG',
            f'sample-{id}.png': 'PNG',
            f'sample-{id}.webp': 'WEBP',
        }
        sample_non_images: list[str] = [f'sample-{id}.txt']
        created_files: dict[str, Path] = {}

        for image_name, format in sample_images.items():
            sample_image_path = Path(tmpdir) / image_name
            image = generate_test_image()
            image.save(sample_image_path, format)
            created_files[format] = sample_image_path

        for non_image_name in sample_non_images:
            sample_non_image_path = Path(tmpdir) / non_image_name
            with open(sample_non_image_path, 'w') as f:
                f.write('This is a text file.')
            created_files['TXT'] = sample_non_image_path

        pp(['created_files:', created_files])

        yield created_files, Path(tmpdir)


@typechecked
def test_get_files_by_extension(sample_images_setup):
    created_files, tmpdir = sample_images_setup
    wanted_types: list[str] = ['xxx', 'jpg', 'jpeg', 'png', 'webp']
    found_files: list[Path] = get_files_by_extension(tmpdir, wanted_types)
    expected_files: list[Path] = [created_files[i] for i in created_files if i.lower() in wanted_types]

    assert set(found_files) == set(expected_files), \
        "The function should return the correct files matching the specified test_extensions"


@typechecked
def test_each_image_type(sample_images_setup):
    """Test compression effectiveness across different image types.

    Iterates through a set of image types (JPEG, PNG, WEBP), compressing each
    one at a low quality setting. It verifies that:
    - The compressed image file is created.
    - The compressed image is saved in the 'condensed' directory.
    - The compressed image's size is less than the original's size.

    Parameters:
    - sample_images_setup: A pytest fixture preparing a set of images and
      directories for the test.

    Asserts:
    - Compressed image file's existence.
    - Correct output directory for the compressed image.
    - Reduced file size of the compressed image compared to the original.
    """
    for image_type in ['JPEG', 'PNG', 'WEBP']:
        created_files, tmpdir = sample_images_setup

        source_image: Path = created_files[image_type]
        quality: int = 10
        image: Compress = Compress(source_image, quality)
        data = image.compress()

        pp({
            'source_image': data.source_image,
            'output_dir': image.output_dir,
            'compressed_image': data.compressed_image,
            'source size': data.original_size,
            'compressed size': data.compressed_size,
        })

        assert data.compressed_image.exists(), "The compressed image should exist."
        assert data.compressed_image.parent.parts[-1] == "condensed", \
            "The compressed image should be created in the specified output directory."
        assert data.compressed_size < data.original_size, \
            "The compressed image should have a smaller file size than the original image."


@typechecked
def test_rename(sample_images_setup):
    """Test the renaming functionality for both source and destination images
    during compression.

    This test ensures that the `Compress` class correctly applies the specified
    `source_rename` and `dest_rename` suffixes to the source and compressed
    images, respectively. It verifies that:
    - The compressed image exists in the specified output directory.
    - The compressed image's file size is smaller than the original image's size.
    - The source image's name includes the `source_rename` suffix.
    - The compressed image's name includes the `dest_rename` suffix.
    """
    created_files, tmpdir = sample_images_setup

    source_image: Path = created_files['JPEG']
    quality: int = 50
    image: Compress = Compress(source_image, quality)

    subdir: str = 'alternative-output-dir'
    image.output_dir = Path(subdir)

    source_rename: str = '-SOURCE-RENAMED'
    image.source_rename = source_rename

    dest_rename: str = '-DEST-RENAMED'
    image.dest_rename = dest_rename

    data = image.compress()

    pp({
        'source_image': data.source_image,
        'output_dir': image.output_dir,
        'compressed_image': data.compressed_image,
        'source size': data.original_size,
        'compressed size': data.compressed_size,
    })

    assert data.compressed_image.exists(), "The compressed image should exist."
    assert data.compressed_image.parent.parts[-1] == subdir, \
        "The compressed image should be created in the specified output directory."
    assert data.compressed_size < data.original_size, \
        "The compressed image should have a smaller file size than the original image."
    assert source_rename in data.source_image.name, \
        "The source image should have the specified source rename in its name."
    assert dest_rename in data.compressed_image.name, \
        "The compressed image should have the specified destination rename in its name."
