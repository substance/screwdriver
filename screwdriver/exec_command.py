import subprocess
import os

def exec_command(cmd, stdout=None, stderr=None, cwd=None, shell=None):
  startupinfo = None
  if os.name == 'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
  return subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=cwd, startupinfo=startupinfo, shell=shell)
