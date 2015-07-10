#!/usr/bin/python
import os
import shutil

from util import read_json, read_project_config, read_module_config, assert_module_clean
from git import git_pull, git_checkout, git_status, git_fetch, git_current_sha, git_get_current_branch
from npm import npm_install, npm_ls
from logger import log, indent, dedent

class ScrewDriver(object):

  def __init__(self, root_dir):
    self.root_dir = root_dir
    self.project_config = None

  def get_project_config(self, reload=False):
    if self.project_config == None or reload == True:
      self.project_config = read_project_config(self.root_dir)
    return self.project_config

  # Traverses dependencies found in package.json
  # - npm installs a module if it has a fixed version (semver or git repo with sha) and it is not there already
  # - npm updates a module if the installed module is not a git repo and has a diverging version
  # - replaces a module with an npm install if the installed module is a git repo and has a clean git status (otherwise error)
  # - git clones a module if it has a git repo with a non-sha tag and it is not there already
  # - replaces a module with a git clone if it was installed with npm before (not a git clone)
  # - git pulls a module if it is there as a git repo and is on the correct branch
  # - git checkout the correct branch if

  def _update_modules(self, config, args):
    indent()
    for name, module in config["modules"].iteritems():
      if module["type"] == "npm":
        if "no-npm" in args:
          continue
        if os.path.exists(module["path"]) and os.path.exists(os.path.join(module["path"], '.git')):
          log("Found git repository for %s. Will replace it with 'npm install'."%module["path"])
          # check if it is deeply clean
          assert_module_clean(module)
          # remove the module directory (otherwise we can not run npm install)
          log("...removing repository")
          shutil.rmtree(module["path"])
        # install (or update)
        npm_install(config["path"], module)
      elif module["type"] == "git":
        if not os.path.exists(module["path"]):
          git_pull(module)
          read_module_config(module, False)
        elif not os.path.exists(os.path.join(module["path"], '.git')):
          log("Found npm installed module for %s. Will replace it with 'git clone'."%module["path"])
          # remove the existing one
          log("...removing module")
          shutil.rmtree(module["path"])
          # and reinstall using git clone
          git_pull(module)
          read_module_config(module, False)
        else:
          # TODO: could this be done via one call?
          git_pull(module)
        # update recursively
        self._update_modules(module, args)
    dedent()

  def update(self, args=None):
    # Update the root folder first
    root_config = git_get_current_branch(self.root_dir)
    if not root_config:
      log("Not a git repository")
    else:
      git_pull(root_config)
    config = self.get_project_config(reload=True)
    self._update_modules(config, args)

  def pull(self, args={}):
    # Update the root folder first
    root_config = git_get_current_branch(self.root_dir)
    if not root_config:
      log("Not a git repository")
    else:
      git_pull(root_config)
    config = self.get_project_config()
    args["no-npm"] = True
    self._update_modules(config, args)

  def checkout(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      git_checkout(m)
