import sys
import pytest
from click.testing import CliRunner
from pathlib import Path
from condenser.cli import condenser
from condenser.condenser import get_files_by_extension
from condenser.condenser import humanize
from condenser.condenser import Compress
import tempfile
import shutil
from PIL import Image


@pytest.fixture
def runner():
    return CliRunner()


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


def test_get_files_by_extension(tmp_path: Path):
    # Setup test environment: Create sample files
    wanted_types: List[str] = ['jpg', 'png']
    test_extensions: List[str] = ['jpg', 'jpeg', 'png', 'gif', 'txt']
    expected_files: list[Path] = []
    for ext in test_extensions:
        file: Path = tmp_path / f"test_file.{ext}"
        file.touch()  # This creates the file
        if ext in wanted_types:  # Assuming we're filtering for these
            expected_files.append(file)
    print(expected_files)

    # Invoke the function
    result_files: List[str] = get_files_by_extension(tmp_path, wanted_types)

    # Convert result to Path objects for comparison
    result_paths: List[Path] = [Path(f) for f in result_files]

    print("Expected files:", expected_files)
    print("Result files:", result_paths)

    # Verify the results: Check if the returned files match the expected files
    assert set(result_paths) == set(expected_files), \
        "The function should return the correct files matching the specified test_extensions"


@pytest.fixture
def sample_images_setup():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup sample image files

        sample_image_path = Path(tmpdir) / "sample.jpg"
        with open(sample_image_path, "wb") as f:
            f.write(b"\x00" * 1024)  # Create a dummy file of 1KB

        yield sample_image_path, Path(tmpdir)


def test_compress_method(sample_image_setup):
    sample_image, output_dir = sample_image_setup
    quality = 70

    compressor = Compress(source_image=sample_image, quality=quality)
    compressor.output_dir = output_dir

    compressed_image_path, original_size, compressed_size = compressor.compress()

    # Verify the compressed image exists
    assert compressed_image_path.exists(), "Compressed image file should exist."

    # Verify the compressed image is smaller than the original
    assert compressed_size < original_size, "Compressed image should be smaller than the original."


def test_get_type_method():
    # Assuming JPEG format for simplicity
    compressor = Compress(source_image=Path("sample.jpg"), quality=70)
    assert compressor._get_type() == "jpeg", "Should identify JPEG format correctly."


def test_output_dir_property():
    compressor = Compress(source_image=Path("sample.jpg"), quality=70)
    test_dir = Path("/path/to/output")
    compressor.output_dir = test_dir
    assert compressor.output_dir == test_dir, "Output directory should be set correctly."


# def test_your_command():
#     runner = CliRunner()
#     result = runner.invoke(your_command, ['--option', 'value'])
#     assert result.exit_code == 0
#     assert 'Expected output' in result.output
#
#
# @pytest.fixture
# def sample_image(tmp_path):
#     # Create a temporary image file to use as a test input
#     sample_image_path = tmp_path / "sample.jpg"
#     sample_image_path.write_bytes(b"Fake image data")
#     return sample_image_path
#
#
# def test_condenser_no_args(runner):
#     """Test running the condenser command without arguments."""
#     result = runner.invoke(condenser)
#     assert result.exit_code != 0
#     assert "Error: Missing argument 'SOURCE...'" in result.output
#
#
# def test_condenser_help_option(runner):
#     """Test the --help option."""
#     result = runner.invoke(condenser, ['--help'])
#     assert result.exit_code == 0
#     assert "Usage:" in result.output
#     assert "--output-dir" in result.output
#     assert "--quality" in result.output
#
#
# def test_image_compression(runner, sample_image, tmp_path):
#     """Test actual image compression."""
#     output_dir = tmp_path / "output"
#     output_dir.mkdir()
#     result = runner.invoke(condenser, [str(sample_image), '--output-dir', str(output_dir)])
#     # Assuming the command exits successfully, you might need to adjust based on actual behavior
#     assert result.exit_code == 0
#     # Check if the output directory contains the compressed file
#     assert any(output_dir.iterdir()), "Output directory should contain at least one file after compression."
