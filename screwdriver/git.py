import subprocess
from subprocess import Popen, PIPE
import os
from gitstatus import gitstatus
from logger import log

def _Popen(cmd, stdout=None, stderr=None, cwd=None):
  startupinfo = None
  if os.name == 'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
  return subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=cwd, startupinfo=startupinfo)

def git_pull(module):
  module_dir = module["path"]
  if not os.path.exists(module_dir):
    log("Cloning module: %s" %module_dir)
    parent_dir, name = os.path.split(module_dir)

    if not os.path.exists(parent_dir):
      log("Creating folder: %s" %parent_dir)
      os.makedirs(parent_dir)

    cmd = ["git", "clone", "git@github.com:"+module["repository"], name]
    p = subprocess.Popen(cmd, cwd=parent_dir)
    p.communicate()

    cmd = ["git", "checkout", module["branch"]]
    p = subprocess.Popen(cmd, cwd=os.path.join(parent_dir, name))
    p.communicate()

  else:
    cmd = ["git", "pull", "origin", module["branch"]]
    log("Pulling module: %s, (%s)" %(module_dir, " ".join(cmd)))
    p = subprocess.Popen(cmd, cwd=module_dir)
    p.communicate()

def git_push(module, options={}):
  module_dir = module["path"]
  if 'remote' in options:
    remote = options['remote']
  else:
    remote = 'origin'

  # only push if there are local changes
  stat = gitstatus(module_dir)

  if (stat['ahead'] > 0):
    log( "Pushing module %s to %s" %(module_dir, remote) )
    cmd = ["git", "push", remote, module["branch"]]
    p = subprocess.Popen(cmd, cwd=module_dir)
    p.communicate()
  else:
    log("Module %s is already up-to-date."%module_dir)

def git_checkout(module):
  module_dir = module["path"]
  branch = module["branch"]
  log("Checking out '%s' in %s"%(branch, module_dir))
  cmd = ["git", "checkout", branch]
  p = subprocess.Popen(cmd, cwd=module_dir)
  p.communicate()

def git_fetch(module):
  module_dir = module["path"]
  branch = module["branch"]
  cmd = ["git", "fetch", "origin"]
  p = subprocess.Popen(cmd, cwd=module_dir)
  p.communicate()

def git_status(module, porcelain=True):
  cmd = ["git", "status"]
  if porcelain:
    cmd.append("--porcelain")
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=module["path"])
  out, err = p.communicate()
  if len(out) > 0:
    print("%s" %module["path"])
    print("--------\n")
    print(out)

def git_get_current_branch(root_dir):
  git_command = 'git'
  gitsym = _Popen([git_command, 'symbolic-ref', 'HEAD'], stdout=PIPE, stderr=PIPE, cwd=root_dir)
  branch, error = gitsym.communicate()
  error_string = error.decode('utf-8')
  if 'fatal: Not a git repository' in error_string:
    return None
  branch = branch.decode('utf-8').strip()[11:]
  if not branch: # not on any branch
    return None
  remote_name = _Popen([git_command,'config','branch.%s.remote' % branch], stdout=PIPE, cwd=root_dir).communicate()[0].strip()
  if not remote_name:
    return None
  return {
    "path": root_dir,
    "remote": remote_name,
    "branch": branch
  }

def git_current_sha(module):
  module_dir = module["path"]
  cmd = ["git", "rev-parse", "HEAD"]
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=module_dir)
  out, err = p.communicate()
  return out.strip()
