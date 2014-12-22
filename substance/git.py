import subprocess
from subprocess import Popen, PIPE
import os
from gitstatus import gitstatus

def _Popen(cmd, stdout=None, stderr=None, cwd=None):
  startupinfo = None
  if os.name == 'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
  return subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=cwd, startupinfo=startupinfo)

def git_pull(root, module):
  module_dir = os.path.join(root, module["folder"])

  if not os.path.exists(module_dir):
    print("Cloning sub-module: %s" %module["folder"])
    parent_dir, name = os.path.split(module_dir)

    if not os.path.exists(parent_dir):
      print("Creating folder: %s" %parent_dir)
      os.makedirs(parent_dir)

    cmd = ["git", "clone", "-b", module["branch"], module["repository"], name]
    p = subprocess.Popen(cmd, cwd=parent_dir)
    p.communicate()

  else:
    cmd = ["git", "pull", "origin", module["branch"]]
    print("Pulling sub-module: %s, (%s)" %(module["folder"], " ".join(cmd)))
    p = subprocess.Popen(cmd, cwd=module_dir)
    p.communicate()

def git_push(root, module, options):
  module_dir = os.path.join(root, module["folder"])
  if 'remote' in options:
    remote = options['remote']
  else:
    remote = 'origin'

  # only push if there are local changes
  stat = gitstatus(module_dir)

  if (stat['ahead'] > 0):
    print( "Pushing sub-module %s to %s" %( module["folder"], remote) )
    cmd = ["git", "push", remote, module["branch"]]
    p = subprocess.Popen(cmd, cwd=module_dir)
    p.communicate()
  else:
    print("Sub-module %s is already up-to-date."%( module["folder"] ))

def git_checkout(root, module):
  module_dir = os.path.join(root, module["folder"])
  branch = module["branch"]

  print("git checkout", branch)
  cmd = ["git", "checkout", branch]
  p = subprocess.Popen(cmd, cwd=module_dir)
  p.communicate()

def git_fetch(root, module):
  module_dir = os.path.join(root, module["folder"])
  branch = module["branch"]
  cmd = ["git", "fetch", "origin"]
  p = subprocess.Popen(cmd, cwd=module_dir)
  p.communicate()

def git_command(root, module, argv):
  module_dir = os.path.join(root, module["folder"])
  cmd = ["git"] + argv
  print("%s $ git command: %s"%(module["folder"], cmd))
  p = subprocess.Popen(cmd, cwd=module_dir)
  p.communicate()

def git_status(root, module, porcelain=True):
  cmd = ["git", "status"]
  if porcelain:
    cmd.append("--porcelain")
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=os.path.join(root, module["folder"]))
  out, err = p.communicate()

  name = os.path.basename(module["folder"])
  if name == ".":
    name = "Mama Mia!"

  if len(out) > 0:

    print("%s" %name)
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
  print("###### %s"%branch)
  remote_name = _Popen([git_command,'config','branch.%s.remote' % branch], stdout=PIPE, cwd=root_dir).communicate()[0].strip()
  if not remote_name:
    return None
  return {
    "folder": root_dir,
    "remote": remote_name,
    "branch": branch
  }

def git_current_sha(root, module):
  module_dir = os.path.join(root, module["folder"])
  cmd = ["git", "rev-parse", "HEAD"]
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=module_dir)
  out, err = p.communicate()
  return out.strip()
