import subprocess

print(f"commits total: {subprocess.check_output(['git', 'rev-list', '--count', 'main'], text=True).strip()}")