import subprocess
import json

def get_mod_info(file):
    # Execute modinfo on the file to gather metadata
    modinfo_command = ['modinfo', '--json', file]
    try:
        modinfo_output = subprocess.check_output(modinfo_command)
        return json.loads(modinfo_output)
    except subprocess.CalledProcessError:
        return None
