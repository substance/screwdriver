import re
import json
import os
import types
from collections import OrderedDict
from git import git_get_current_branch

PACKAGE_FILE = "package.json"

def package_file(root):
  return os.path.join(root, PACKAGE_FILE)

def read_json(filename):
  with open(filename, 'r') as f:
    try:
      data = f.read()
      return json.JSONDecoder(object_pairs_hook=OrderedDict).decode(data)
    except ValueError as ve:
      print("Could not parse file %s"%filename)
      print(ve)
      return None

def write_json(filename, data):
  with open(filename, 'w') as f:
    json.dump(data, f, indent=2, separators=(',', ': '))

REPO_ID = "([a-zA-Z0-9_-]+)"
GIT_REPO_EXPRESSION = re.compile(REPO_ID+"/"+REPO_ID+"(?:.git)?"+"(?:#"+REPO_ID+")?")
SHA1_EXPRESSION = re.compile("[a-fA-F0-9]{40}");

def read_module_config(root, config, is_root):
  package_config = read_json(package_file(root))
  deps = {}
  if "dependencies" in package_config:
    for name, version in package_config["dependencies"].iteritems():
      deps[name] = version
  if "devDependencies" in package_config:
    for name, version in package_config["devDependencies"].iteritems():
      deps[name] = version

  for name, version in deps.iteritems():
    match = GIT_REPO_EXPRESSION.match(version)
    childConfig = {}
    module_dir = os.path.join(root, 'node_modules', name);
    if match:
      # only take over modules with a non SHA-1 version
      if match.group(3) and SHA1_EXPRESSION.match(match.group(3)):
        childConfig = {
          "type": "npm",
          "name": name,
          "path": module_dir,
          "version": version
        }
      else:
        module_dir = os.path.join(root, 'node_modules', name);
        childConfig = {
          "type": "git",
          "name": name,
          "path": module_dir,
          "repository": match.group(1) + "/" + match.group(2) + ".git",
          "branch": match.group(3),
          "modules": {}
        }
        if (os.path.exists(module_dir)):
          read_module_config(module_dir, childConfig, False)
        else:
          childConfig["state"] = "missing"
    else:
      childConfig = {
        "type": "npm",
        "name": name,
        "path": module_dir,
        "version": version
      }
    config["modules"][name] = childConfig

def read_project_config(root):
  config = git_get_current_branch(root)
  config["type"] = "git"
  config["modules"] = {}
  read_module_config(root, config, True)
  return config
