import os
from gitstatus import gitstatus
from logger import log
from exec_command import exec_command
from subprocess import PIPE

def print_error(msg, error):
  print("###################   ERROR   ###################")
  print(msg)
  print(error)

def git_pull(module):
  module_dir = module["path"]
  if not os.path.exists(module_dir):
    log("Cloning module: %s" %module_dir)
    parent_dir, name = os.path.split(module_dir)
    if not os.path.exists(parent_dir):
      log("Creating folder: %s" %parent_dir)
      os.makedirs(parent_dir)
    # TODO: it should be configurable whether the default should be https or ssh
    #cmd = ["git", "clone", "-q", "git@github.com:"+module["repository"], name]
    cmd = ["git", "clone", "-q", "https://github.com/"+module["repository"]+".git", name]
    p = exec_command(cmd, stdout=PIPE, stderr=PIPE, cwd=parent_dir)
    out, error = p.communicate()
    if error != "":
      msg = "Could not clone repository: %s"%module["repository"]
      print_error(msg, error)
      raise Exception(msg)
    git_checkout(module)
  else:
    # Note: for example, when a branch exists only locally we can't pull as there is no remote
    if module["remote"] == None:
      log("Warning: repository is not connected to remote.%s"%module)
    else:
      git_fetch(module)
      git_checkout(module)
      cmd = ["git", "pull", "-q", "origin", module["branch"]]
      log("Pulling module: %s, (%s)" %(module_dir, " ".join(cmd)))
      p = exec_command(cmd, stdout=PIPE, stderr=PIPE, cwd=module_dir)
      out, error = p.communicate()
      if error != "":
        msg = "Could not pull from repository: %s"%module
        print_error(msg, error)
        raise Exception(msg)

def git_checkout(module):
  module_dir = module["path"]
  branch = module["branch"]
  log("Checking out '%s' in %s"%(branch, module_dir))
  cmd = ["git", "checkout", "-q", branch]
  p = exec_command(cmd, stdout=PIPE, stderr=PIPE, cwd=module_dir)
  out, error = p.communicate()
  if error != "":
    msg = "Could not checkout branch: %s"%module["branch"]
    print_error(msg, error)
    raise Exception(msg)

def git_fetch(module):
  module_dir = module["path"]
  branch = module["branch"]
  cmd = ["git", "fetch", "origin"]
  p = exec_command(cmd, stdout=PIPE, stderr=PIPE, cwd=module_dir)
  out, error = p.communicate()
  if error != "":
    msg = "Could not fetch from repository: %s"%module
    print_error(msg, error)
    raise Exception(msg)

def git_status(module, porcelain=True):
  cmd = ["git", "status"]
  if porcelain:
    cmd.append("--porcelain")
  p = exec_command(cmd, stdout=PIPE, cwd=module["path"])
  out, err = p.communicate()
  if len(out) > 0:
    print("%s" %module["path"])
    print("--------\n")
    print(out)

def git_get_current_branch(root_dir):
  git_command = 'git'
  gitsym = exec_command([git_command, 'symbolic-ref', 'HEAD'], stdout=PIPE, stderr=PIPE, cwd=root_dir)
  branch, error = gitsym.communicate()
  error_string = error.decode('utf-8')
  if 'fatal: Not a git repository' in error_string:
    raise Exception('Not a git repository!')
  branch = branch.decode('utf-8').strip()[11:]
  if not branch: # not on any branch
    raise Exception('Could not extract current branch name.')
  remote_name = exec_command([git_command,'config','branch.%s.remote' % branch], stdout=PIPE, cwd=root_dir).communicate()[0].strip()
  if remote_name == "":
    remote_name = None
  return {
    "path": root_dir,
    "remote": remote_name,
    "branch": branch
  }

def git_current_sha(module):
  module_dir = module["path"]
  cmd = ["git", "rev-parse", "HEAD"]
  p = exec_command(cmd, stdout=PIPE, cwd=module_dir)
  out, err = p.communicate()
  return out.strip()
