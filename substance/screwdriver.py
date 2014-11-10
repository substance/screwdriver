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
      for m in self.project_config["modules"]:
        m['repoName'] = os.path.basename(m['repository'])

    return self.project_config

  def update(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      module_dir = os.path.join(self.root_dir, m["folder"])
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
      git_push(self.root_dir, m, args)

  def checkout(self, args=None):
    config = self.get_project_config()
    for m in config["modules"]:
      git_checkout(self.root_dir, m)

  def git(self, args):
    config = self.get_project_config()
    argv = args["argv"]
    for m in config["modules"]:
      git_command(self.root_dir, m, argv)

  def replaceModuleVariables(self, m, s):
    s = s.replace('{{repoName}}', m['repoName'])
    s = s.replace('{{branch}}', m['branch'])
    return s

  def prepareArgs(self, m, argv):
    result = [self.replaceModuleVariables(m, a) for a in argv]
    return result

  def each(self, args):
    config = self.get_project_config()
    argv = args["argv"]
    for m in config["modules"]:
      module_dir = os.path.join(self.root_dir, m["folder"])
      cmd = self.prepareArgs(m, argv)
      print( "Executing command on sub-module %s: %s" %( m["folder"], ' '.join(cmd) ) )
      p = subprocess.Popen(cmd, cwd=module_dir)
      out, err = p.communicate()
      if out:
        print(out)
      if err:
        print("Error: %s"%err)

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
    release = (args["package"] == "release")
    tag = args["tag"] if "tag" in args else None

    # prepare a lookup table for module versions
    table = {}
    for m, __, conf in iterate_modules(self.root_dir, config):
      # add the registered module version
      # this is used for releases
      m["version"] = conf["version"];
      table[conf["name"]] = m

    if "node_modules" in config:
      table.update(config["node_modules"])

    for __, folder, conf in iterate_modules(self.root_dir, config):
      if "npm" in config:
        conf.update(config["npm"])
      create_package(folder, conf, table, tag=tag, release=release)

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
    node_server(self.root_dir, args)

  def bundle(self, args=None):
    config = self.get_project_config()

    options = []
    if args["bundle"] != None:
      options = args["bundle"].split(",");
      options = [o.strip() for o in options]

    if "bundle" in config:
      bundle_config = config["bundle"]

      print("Bundling....");
      name = bundle_config["name"]
      dist_folder = os.path.abspath(os.path.join(self.root_dir, bundle_config["folder"]))
      bundled_script = os.path.abspath(os.path.join(dist_folder, name) + ".js")
      boot_script = os.path.abspath(bundle_config["source"])

      ignores = []
      if "ignores" in bundle_config:
        ignores = bundle_config["ignores"]

      if not os.path.exists(dist_folder):
        print("Creating bundle folder: %s" %dist_folder)
        os.makedirs(dist_folder)

      print("Creating bundled script...")
      # browserifying
      browserify_options = []

      for fileName in ignores:
        browserify_options.append('-i')
        browserify_options.append(fileName)

      # enable source maps in nominify mode
      if "sourcemap" in options:
        browserify_options.append('-d')

      cmd = ["browserify", boot_script, "-o", bundled_script] + browserify_options

      print(" ".join(cmd))
      p = subprocess.Popen(cmd, cwd=self.root_dir)
      p.communicate()

      # uglifying
      if not "nominify" in options:
        uglifyjs_options = ["-c", "-m"]
        cmd = ["uglifyjs", bundled_script, "-o", bundled_script] + uglifyjs_options
        print(" ".join(cmd))
        p = subprocess.Popen(cmd, cwd=self.root_dir)
        p.communicate()

      # process the template index file
      if "index" in bundle_config:
        index_file = os.path.abspath(os.path.join(self.root_dir, bundle_config["index"]))
        if os.path.exists(index_file):
          output_index_file = os.path.abspath(os.path.join(dist_folder, "index.html"))
          index_content = ""
          with open(index_file, "r") as f:
            index_content = f.read()
          include_style = "<link href='%s' rel='stylesheet' type='text/css'/>"%(name + ".css")
          include_script = "<script src='%s'></script>"%(name + ".js")
          index_content = index_content.replace("#####styles#####", include_style)
          index_content = index_content.replace("#####scripts#####", include_script)
          with open(output_index_file, "w") as f:
            f.write(index_content)

      # Stitch all CSS files and store it into <folder>/<name>.css
      print("Creating a unified style sheet...")

      styles = config["styles"]
      stitched_styles = []
      for _, p in styles.iteritems():
        css_file = os.path.join(self.root_dir, p)
        with open(css_file, "r") as f:
          stitched_styles.append(f.read())
      if len(stitched_styles) > 0:
        stitched_styles = "\n".join(stitched_styles)
        stitched_file = os.path.join(dist_folder, name) + ".css"
        with open(stitched_file, "w") as f:
          f.write(stitched_styles)

      # Copy all assets
      print("Copying assets...")

      assets = config["assets"]
      for alias, p in assets.iteritems():
        source = os.path.join(self.root_dir, p)
        dest = os.path.join(dist_folder, alias)

        parent = os.path.dirname(dest)
        if not os.path.exists(parent):
          os.makedirs(parent)

        if os.path.isdir(source):
          dir_util.copy_tree(source, dest)
        else:
          file_util.copy_file(source, dest)

    else:
      print("No bundle configuration available...");
