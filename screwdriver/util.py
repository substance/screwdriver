import re
import json
import os
import types
from collections import OrderedDict
from git import git_get_current_branch
from subprocess import PIPE
from exec_command import exec_command
from logger import log

PACKAGE_FILE = "package.json"

def package_file(root):
  return os.path.join(root, PACKAGE_FILE)

def read_json(filename):
  with open(filename, 'r') as f:
    try:
      data = f.read()
      return json.JSONDecoder(object_pairs_hook=OrderedDict).decode(data)
    except ValueError as ve:
      log("Could not parse file %s"%filename)
      log(ve)
      return None

REPO_ID = "([a-zA-Z0-9_-]+)"
GIT_REPO_EXPRESSION = re.compile(REPO_ID+"/"+REPO_ID+"(?:.git)?"+"(?:#"+REPO_ID+")?")
SHA1_EXPRESSION = re.compile("[a-fA-F0-9]{40}");

def get_dependencies(module, is_root):
  package_config = read_json(package_file(module["path"]))
  deps = {}
  if "dependencies" in package_config:
    for name, version in package_config["dependencies"].iteritems():
      deps[name] = version
  if is_root and "devDependencies" in package_config:
    for name, version in package_config["devDependencies"].iteritems():
      deps[name] = version
  return deps

def read_module_config(module, is_root=False):
  root = module["path"]
  if not "modules" in module:
    module["modules"] = {}
  deps = get_dependencies(module, is_root)

  for name, version in deps.iteritems():
    match = GIT_REPO_EXPRESSION.match(version)
    childConfig = {}
    module_dir = os.path.join(root, 'node_modules', name);
    if match:
      # only take over modules with a non SHA-1 version
      if os.path.exists(os.path.join(module_dir, '.git')):
        childConfig = git_get_current_branch(module_dir)
        childConfig["name"] = name
        childConfig["version"] = version
      else:
        childConfig = {
          "path": module_dir,
          "name": name,
          "version": version,
        }
      # Install repos with SHA version with npm
      if match.group(3) and SHA1_EXPRESSION.match(match.group(3)):
        childConfig["type"] = "npm"
      else:
        module_dir = os.path.join(root, 'node_modules', name);
        childConfig["type"] = "git"
        childConfig["repository"] = "%s/%s"%(match.group(1), match.group(2))
        childConfig["branch"] = match.group(3)
        childConfig["modules"] = {}
        if (os.path.exists(os.path.join(module_dir, '.git'))):
          read_module_config(childConfig, False)
        else:
          childConfig["state"] = "missing"
    else:
      childConfig = {
        "type": "npm",
        "name": name,
        "path": module_dir,
        "version": version
      }
    module["modules"][name] = childConfig

  return module

def read_project_config(root):
  config = git_get_current_branch(root)
  config["type"] = "git"
  config["modules"] = {}
  read_module_config(config, True)
  return config

def assert_module_clean(module):
  cmd = ["git", "status", "--porcelain"]
  p = exec_command(cmd, stdout=PIPE, stderr=PIPE, cwd=module["path"])
  out, err = p.communicate()
  if len(out) > 0:
    msg = "Module is not clean: %s.\nCommit and push your changes first!\n"%module["path"]
    print("")
    print("ERROR: "+msg)
    print("Uncommitted changes:")
    print(out)
    print("")
    raise Exception(msg)

  module_config = read_module_config(module)
  for name, child_module in module_config["modules"].iteritems():
    if os.path.exists(os.path.join(child_module["path"], '.git')):
      assert_module_clean(child_module)
