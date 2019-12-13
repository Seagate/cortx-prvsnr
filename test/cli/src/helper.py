def run_script(mhost, script_path, *args, trace=False, stderr_to_stdout=True):
    return mhost.run(
        "bash {} {} {} {}"
        .format(
            '-x' if trace else '',
            script_path,
            ' '.join([*args]),
            '2>&1' if stderr_to_stdout else ''
        ), force_dump=trace
    )
