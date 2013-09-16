#!/usr/bin/python
import argparse
import os
import sys
import subprocess
from distutils import file_util, dir_util

from util import read_json, project_file, module_file
from git import git_pull, git_push, git_checkout, git_command, git_status, git_fetch
from npm import npm_publish, npm_install, node_server
from version import increment_version, bump_version, create_package, create_tag, \
  save_current_version, restore_last_version, create_branch

def get_module_config(root, module):
  folder = os.path.join(root, module["folder"])
  filename = module_file(folder)
  if not os.path.exists(filename):
    return None
  return read_json(filename)

def iterate_modules(root, config):
  for m in config["modules"]:
    conf = get_module_config(root, m)
    if conf == None: continue
    folder = os.path.join(root, m["folder"])
    yield [m, folder, conf]


def get_configured_deps(folder, conf):
  result = {}
  if "dependencies" in conf:
    for dep, version in conf["dependencies"].iteritems():
      if version != "":
        result[dep] = version

  if "devDependencies" in conf:
    for dep, version in conf["dependencies"].iteritems():
      if version != "":
        result[dep] = version

  return result

class ScrewDriver(object):

  def __init__(self, root_dir):
    self.root_dir = root_dir
    self.project_config = None

  def get_project_config(self):
    if self.project_config == None:
      self.project_config = read_json(project_file(self.root_dir))

    return self.project_config

  def update(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      module_dir = os.path.join(self.root_dir, m["folder"])
      git_status(self.root_dir, m)
      if os.path.exists(module_dir):
        git_fetch(self.root_dir, m)
        git_checkout(self.root_dir, m)
      git_pull(self.root_dir, m)

    # 2. Install all shared node modules
    node_modules = config["node_modules"] if "node_modules" in config else {}
    for __, folder, conf in iterate_modules(self.root_dir, config):
      node_modules.update(get_configured_deps(folder, conf))

    npm_install(self.root_dir, node_modules)

  def branch(self, args):
    config = self.get_project_config()
    branch_name = args["branch"][0]
    create_branch(self.root_dir, config, branch_name)

  def status(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      git_status(self.root_dir, m)

  def pull(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      git_fetch(self.root_dir, m)
      git_pull(self.root_dir, m)

  def push(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      git_push(self.root_dir, m)

  def checkout(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      git_checkout(self.root_dir, m, args)

  def git(self, args):
    config = self.get_project_config()
    argv = args["argv"]
    for m in config["modules"]:
      git_command(self.root_dir, m, argv)

  def publish(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      npm_publish(self.root_dir, m, args)

  def increment_versions(self, args=None):
    config = self.get_project_config()
    level = args["increment_version"]
    for __, folder, conf in iterate_modules(self.root_dir, config):
      increment_version(folder, conf, level)

  def package(self, args=None):
    config = self.get_project_config()
    tag = args["package"]

    # prepare a lookup table for module versions
    table = {}
    for m, __, conf in iterate_modules(self.root_dir, config):
      table[conf["name"]] = m

    if "node_modules" in config:
      table.update(config["node_modules"])

    for __, folder, conf in iterate_modules(self.root_dir, config):
      if "npm" in config:
        conf.update(config["npm"])
      create_package(folder, conf, table, tag)

  def tag(self, args=None):
    config = self.get_project_config()
    tag = args["tag"]

    table = {}
    for folder, conf in iterate_modules(self.root_dir, config):
      table[conf["name"]] = conf
    if "node_modules" in config:
      table.update(config["node_modules"])

    for folder, conf in iterate_modules(self.root_dir, config):
      if "npm" in config:
        conf.update(config["npm"])
      create_tag(folder, conf, table, tag)

  def bump(self, args=None):
    config = self.get_project_config()
    for folder, conf in iterate_modules(self.root_dir, config):
      bump_version(folder, conf)

  def serve(self, args=None):
    node_server(self.root_dir)

  def bundle(self, args=None):
    config = self.get_project_config()

    if "bundle" in config:
      print("Bundling....");
      bundle_config = config["bundle"]
      dist_folder = os.path.join(self.root_dir, bundle_config["dist_folder"])
      output_file = os.path.join(dist_folder, bundle_config["name"]) + ".js"

      if not os.path.exists(dist_folder):
        print("Creating bundle folder: %s" %dist_folder)
        os.makedirs(dist_folder)

      print("Creating bundled script...")
      # browserifying
      browserify_options = []
      cmd = ["browserify", bundle_config["source"], "-o", output_file] + browserify_options
      print(" ".join(cmd))
      p = subprocess.Popen(cmd, cwd=self.root_dir)
      p.communicate()

      # uglifying
      uglifyjs_options = ["-c", "-m"]
      cmd = ["uglifyjs", output_file, "-o", output_file] + uglifyjs_options
      print(" ".join(cmd))
      p = subprocess.Popen(cmd, cwd=self.root_dir)
      p.communicate()

      # assets
      print("Copying assets...")
      for entry in bundle_config["assets"]:
        source = os.path.join(self.root_dir, entry)
        dest = os.path.join(dist_folder, entry)
        if os.path.isdir(source):
          dir_util.copy_tree(source, dest)
        else:
          file_util.copy_file(source, dest)

    else:
      print("No bundle configuration available...");
