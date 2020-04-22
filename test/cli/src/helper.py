

def run_script(
    mhost, script_path, *args, trace=False, stderr_to_stdout=True, env=None
):
    if env and type(env) is dict:
        env = ' '.join(["{}={}".format(k, v) for k, v in env.items()])

    return mhost.run(
        "{} bash {} {} {} {}"
        .format(
            env if env else '',
            '-x' if trace else '',
            script_path,
            ' '.join([*args]),
            '2>&1' if stderr_to_stdout else ''
        ), force_dump=trace
    )
