import os
import subprocess
import sys
import asyncio


def rx_subprocess(cmd: list[str], cwd: str, env: dict = None, **kwargs) -> tuple[str, str, int]:
    print("Executing command:", cmd)
    print("Executing command:", " ".join(cmd))

    _env = os.environ.copy()
    _env.update(env or {})
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **kwargs
    )

    assert process.stdout is not None
    assert process.stderr is not None

    # Stream output and error in real-time
    _out = ""
    _err = ""
    while True:
        output = process.stdout.readline()
        error = process.stderr.readline()

        if output:
            print(output, end="")
            sys.stdout.flush()
            _out += output
        if error:
            print(error, end="", file=sys.stderr)
            sys.stderr.flush()
            _err += error

        if output == "" and error == "" and process.poll() is not None:
            break

    return_code = process.poll()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, cmd)

    return _out, _err, return_code


def rx_subprocess_async(cmd: list[str],
                        cwd: str | None = None,
                        env: dict | None = None) -> None:

    async def run_command():
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        assert process.stdout is not None
        assert process.stderr is not None

        # Stream output and error in real-time
        while True:
            output = await process.stdout.readline()
            error = await process.stderr.readline()

            if output:
                print(output.decode().rstrip())
                sys.stdout.flush()
            if error:
                print(error.decode().rstrip(), file=sys.stderr)
                sys.stderr.flush()

            if output == b"" and error == b"" and process.returncode is not None:
                break

        return_code = await process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd)

    asyncio.run(run_command())
