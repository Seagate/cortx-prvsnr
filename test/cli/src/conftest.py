import pytest

import test.cli.src.helper as h

@pytest.fixture
def run_script(mlocalhost, tmpdir_function, request):
    def _f(
        *args,
        mhost=None,
        trace=False,
        stderr_to_stdout=True,
        script_name=None,
        env=None
    ):
        if script_name is None:
            script_name = request.getfixturevalue('script_name')

        if mhost is None:
            mhost = request.getfixturevalue('mhost')

        return h.run_script(
            mhost,
            mhost.repo / 'cli/src' / script_name,
            *args,
            trace=trace,
            stderr_to_stdout=stderr_to_stdout,
            env=env
        )
    return _f
