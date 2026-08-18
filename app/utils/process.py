import subprocess


def get_command_output(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )

    return (result.stderr or "") + "\n" + (result.stdout or "")
