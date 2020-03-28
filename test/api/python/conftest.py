from pathlib import Path
import pytest


@pytest.fixture(scope='session')
def test_output_dir(project_path):
    return Path(__file__).resolve().parent / 'files'
