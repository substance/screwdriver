#!/usr/bin/python
import os

from util import read_json, read_project_config, read_module_config
from git import git_pull, git_push, git_checkout, git_status, git_fetch, git_current_sha, git_get_current_branch
from npm import npm_install, npm_ls

def get_configured_deps(conf, devDependencies=False):
  result = {}
  if "dependencies" in conf:
    for dep, version in conf["dependencies"].iteritems():
      if version != "":
        result[dep] = version

  if devDependencies and "devDependencies" in conf:
    for dep, version in conf["devDependencies"].iteritems():
      if version != "":
        result[dep] = version

  return result

class ScrewDriver(object):

  def __init__(self, root_dir):
    self.root_dir = root_dir
    self.project_config = None

  def get_project_config(self, reload=False):
    if self.project_config == None or reload == True:
      self.project_config = read_project_config(self.root_dir)
    return self.project_config

  def _update_git_modules(self, config, args):
    for name, module in config["modules"].iteritems():
      if module["type"] == "git":
        if "state" in module and module["state"] == "missing":
          # clone the repository
          git_pull(module)
          read_module_config(module["path"], module, False)
          if len(module["modules"]) > 0:
            self._update(module, args)
        else:
          # pull the repo
          git_fetch(module)
          git_checkout(module)
          git_pull(module)

  def update(self, args=None):
    # Update the root folder first
    root_config = git_get_current_branch(self.root_dir)
    if not root_config:
      print("Not a git repository")
    else:
      git_fetch(root_config)
      git_checkout(root_config)
      git_pull(root_config)
    config = self.get_project_config(reload=True)
    self._update_git_modules(config, args)
    npm_install(config)
    npm_ls(root_config["path"])

  def install(self, args=None):
    config = self.get_project_config(reload=True)
    npm_install(config)
    npm_ls(config["path"])

  def pull(self, args=None):
    # Update the root folder first
    root_config = git_get_current_branch(self.root_dir)
    if not root_config:
      print("Not a git repository")
    else:
      git_fetch(root_config)
      git_pull(root_config)
    config = self.get_project_config()
    self._update_git_modules(config, args)

  def checkout(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      git_checkout(self.root_dir, m)
