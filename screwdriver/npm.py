from subprocess import PIPE
import os
import re
from util import read_json, package_file, get_dependencies, GIT_REPO_EXPRESSION
from logger import log
from exec_command import exec_command

# ^1.2.3  ~= 1.x.x
# ~1.2.3  ~= 1.2.x
# *

VERSION_EXPRESSION = re.compile("(?P<mod>~|\^)?(?P<major>\d+)\.(?P<minor>\d+|x)\.(?P<patch>\d+|x)(?P<suffix>.*)")

class SemanticVersion():
  def __init__(self, versionStr):
    self.major = "x"
    self.minor = "x"
    self.patch = "x"
    self.suffix = "x"
    if versionStr != "*":
      match = VERSION_EXPRESSION.match(versionStr)
      if (not match):
        raise RuntimeError("Could not parse version string: %s"%versionStr)
      mod = match.group('mod')
      if mod == "^":
        self.major = match.group('major')
      elif mod == "~":
        self.major = match.group('major')
        self.minor = match.group('minor')
      else:
        self.major = match.group('major')
        self.minor = match.group('minor')
        self.patch = match.group('patch')
        self.suffix = match.group('suffix')
    # log("### SemanticVersion %s: %s %s %s %s"%(versionStr, self.major, self.minor, self.patch, self.suffix))

  def isFullfilledBy(self, other):
    if self.major == "x":
      return True
    elif other.major != self.major:
      return False
    if self.minor == "x":
      return True
    elif other.minor != self.minor:
      return False
    if self.patch == "x":
      return True
    elif other.patch != self.patch:
      return False
    if self.suffix == "x":
      return True
    elif other.suffix != self.suffix:
      return False
    return True

def npm_install(root, module):
  if module["type"] == "npm":
    name = module["name"]
    version = module["version"]
    m = GIT_REPO_EXPRESSION.match(version)
    if not m and os.path.exists(module["path"]):
      package_config = read_json(package_file(module["path"]))
      actual_version = SemanticVersion(package_config["version"])
      expected_version = SemanticVersion(module["version"])
      if expected_version.isFullfilledBy(actual_version):
        log("Module '%s' is already up-to-date: %s"%(module["name"],version))
        return
      log("Updating %s:%s"%(module["name"],version))
      cmd = ["npm", "update", "%s@%s"%(name, version)]
    else:
      log("Installing %s:%s"%(module["name"],version))
      cmd = ["npm", "install", "%s@%s"%(name, version)]
    # HACK: under Windows npm can only be run with shell (npm.cmd)
    shell = (os.name == "nt")
    p = exec_command(cmd, cwd=root, stdout=PIPE, stderr=PIPE, shell=shell)
    out, error = p.communicate();
    if error != None:
      print(error)
  elif module["type"] == "git":
    for name, sub_module in module["modules"].iteritems():
      npm_install(module["path"], sub_module)

def npm_ls(root):
    cmd = ["npm", "ls"]
    # HACK: under Windows npm can only be run with shell (npm.cmd)
    shell = (os.name == "nt")
    p = subprocess.Popen(cmd, cwd=root, shell=shell)
    p.communicate();
