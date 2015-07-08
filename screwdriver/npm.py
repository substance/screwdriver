import subprocess
import os
from util import read_json

def npm_install(module):
  for name, sub_module in module["modules"].iteritems():
    if sub_module["type"] == "npm":
      version = sub_module["version"]
      if os.path.exists(sub_module["path"]):
        print("   Updating %s:%s"%(sub_module["path"],version))
        cmd = ["npm", "update", "%s@%s"%(name, version)]
      else:
        print("   Installing %s:%s"%(sub_module["path"],version))
        cmd = ["npm", "install", "%s@%s"%(name, version)]
      # HACK: under Windows npm can only be run with shell (npm.cmd)
      shell = (os.name == "nt")
      p = subprocess.Popen(cmd, cwd=module["path"], shell=shell)
      p.communicate();
    elif sub_module["type"] == "git":
      npm_install(sub_module)

def npm_ls(root):
    cmd = ["npm", "ls"]
    # HACK: under Windows npm can only be run with shell (npm.cmd)
    shell = (os.name == "nt")
    p = subprocess.Popen(cmd, cwd=root, shell=shell)
    p.communicate();
