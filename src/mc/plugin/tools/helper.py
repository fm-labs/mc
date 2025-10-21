import subprocess
import sys


def subprocess_run(cmd_list: list, env: dict = None) -> dict:
    """
    Runs a shell command.
    Expects a list-style command, e.g., ["docker", "pull", "ubuntu"].

    Returns a dictionary with keys: output, stderr, returncode, and error (if any).
    """
    try:
        print(f"Running command: {' '.join(cmd_list)}")
        result = subprocess.run(cmd_list,
                                capture_output=True,
                                text=True,
                                check=True,
                                env=env)

        print(f"Command finished with return code {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")

        # if result.returncode != 0:
        #     return {"error": f"Command failed with return code {result.returncode}",
        #             "output": result.stdout,
        #             "stderr": result.stderr,
        #             "returncode": result.returncode}

        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.CalledProcessError as e:
        return {"error": str(e), "stdout": e.output, "stderr": e.stderr, "returncode": e.returncode}
    except Exception as e:
        return {"error": str(e)}


def subprocess_stream(cmd_list: list, fail_on_error=True, callback=None) -> int:
    """
    Runs a shell command, streaming stdout and stderr in real time.
    Expects a list-style command, e.g., ["docker", "pull", "ubuntu"].
    """
    try:
        p = subprocess.Popen(cmd_list,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                             bufsize=1,
                             universal_newlines=True)

        for line in p.stdout:
            sys.stdout.write(line)
            sys.stdout.flush() # Ensure output is displayed immediately

            if callback:
                callback(line)

        p.wait() # Wait for the subprocess to finish
        exit_code = p.returncode

        if exit_code != 0 and fail_on_error:
            raise RuntimeError(f"Command failed with exit code {exit_code}. Command: `{cmd_list}`")
        return exit_code

    except FileNotFoundError:
        print(f"Error: Command not found: {cmd_list[0]}", file=sys.stderr)
        return -1
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return -1



if __name__ == "__main__":
    # Example usage
    cmd = ["bash", "-c", "for i in {1..5}; do echo out:$i; echo err:$i 1>&2; sleep 1; done"]
    subprocess_run(cmd)
    print("--- Streaming Output ---")

    def callback(line):
        if "err" in line:
            print(f"Callback received error line: {line.strip()}")
        else:
            print(f"Callback received output line: {line.strip()}")

    subprocess_stream(cmd, callback=callback)