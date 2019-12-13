import pytest

import test.cli.src.helper as h

@pytest.fixture
def run_script(mlocalhost, tmpdir_function, request, script_name):
    def _f(*args, mhost=None, trace=False, stderr_to_stdout=True):
        if mhost is None:
            mhost = request.getfixturevalue('mhost')

        return h.run_script(
            mhost,
            mhost.repo / 'cli/src' / script_name,
            *args,
            trace=trace,
            stderr_to_stdout=stderr_to_stdout
        )
    return _f
