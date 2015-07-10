#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""This module defines a Print function to use with python 2.x or 3.x., so we can use the prompt with older versions of Python too

It's interface is that of python 3.0's print. See
http://docs.python.org/3.0/library/functions.html?highlight=print#print

Shamelessly ripped from http://www.daniweb.com/software-development/python/code/217214/a-print-function-for-different-versions-of-python
"""

# change those symbols to whatever you prefer
symbols = {'ahead of': '↑·', 'behind': '↓·', 'prehash':':'}

import os
import subprocess
from subprocess import Popen, PIPE
import sys
import json

def gitstatus(folder, git_command='git', plain_only=False):

  def _Popen(cmd, stdout=None, stderr=None):
    startupinfo = None
    if os.name == 'nt':
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=folder, startupinfo=startupinfo)

  if (plain_only):
    status_plain = _Popen([git_command, 'status'], stdout=PIPE).communicate()[0]
    return {
      "status": status_plain
    }

  gitsym = _Popen([git_command, 'symbolic-ref', 'HEAD'], stdout=PIPE, stderr=PIPE)
  branch, error = gitsym.communicate()

  error_string = error.decode('utf-8')

  if 'fatal: Not a git repository' in error_string:
    return None

  branch = branch.decode('utf-8').strip()[11:]

  res, err = _Popen([git_command, 'diff', '--name-status'], stdout=PIPE, stderr=PIPE).communicate()
  err_string = err.decode('utf-8')

  if 'fatal' in err_string:
    return None

  changed_files = [namestat[0] for namestat in res.splitlines()]
  staged_files = [namestat[0] for namestat in _Popen([git_command,'diff', '--staged','--name-status'], stdout=PIPE).communicate()[0].splitlines()]
  nb_changed = len(changed_files) - changed_files.count('U')
  nb_U = staged_files.count('U')
  nb_staged = len(staged_files) - nb_U
  staged = nb_staged
  conflicts = nb_U
  changed = nb_changed
  status = _Popen([git_command,'status','-s','-uall'], stdout=PIPE).communicate()[0]
  status_lines = status.splitlines()
  untracked_lines = [a for a in map(lambda s: s.decode('utf-8'), status_lines) if a.startswith("??")]
  nb_untracked = len(untracked_lines)
  untracked = nb_untracked
  stashes = _Popen([git_command,'stash','list'], stdout=PIPE).communicate()[0].splitlines()
  nb_stashed = len(stashes)
  stashed = nb_stashed

  if not nb_changed and not nb_staged and not nb_U and not nb_untracked and not nb_stashed:
    clean = True
  else:
    clean = False

  remote = ''

  tag, tag_error = _Popen([git_command, 'describe', '--exact-match'], stdout=PIPE, stderr=PIPE).communicate()

  if not branch: # not on any branch
    if tag: # if we are on a tag, print the tag's name
      branch = tag
    else:
      branch = symbols['prehash'] + _Popen([git_command,'rev-parse','--short','HEAD'], stdout=PIPE).communicate()[0].decode('utf-8')[:-1]
  else:
    remote_name = _Popen([git_command,'config','branch.%s.remote' % branch], stdout=PIPE).communicate()[0].strip()
    if remote_name:
      merge_name = _Popen([git_command,'config','branch.%s.merge' % branch], stdout=PIPE).communicate()[0].strip()
    else:
      remote_name = "origin"
      merge_name = "refs/heads/%s" % branch

    if remote_name == '.': # local
      remote_ref = merge_name
    else:
      remote_ref = 'refs/remotes/%s/%s' % (remote_name, merge_name[11:])
    revgit = _Popen([git_command, 'rev-list', '--left-right', '%s...HEAD' % remote_ref], stdout=PIPE, stderr=PIPE)
    revlist = revgit.communicate()[0]
    if revgit.poll(): # fallback to local
      revlist = _Popen([git_command, 'rev-list', '--left-right', '%s...HEAD' % merge_name], stdout=PIPE, stderr=PIPE).communicate()[0]
    behead = revlist.splitlines()
    ahead = len([x for x in behead if x[0]=='>'])
    behind = len(behead) - ahead
    if behind:
      remote += '%s%s' % (symbols['behind'], behind)
    if ahead:
      remote += '%s%s' % (symbols['ahead of'], ahead)

  if remote == "":
    remote = '.'

  result = {
    "branch": str(branch),
    "ahead": ahead,
    "behind": behind,
    "staged": staged,
    "conflicts": conflicts,
    "changed": changed,
    "untracked": untracked,
    "stashed": stashed,
    "clean": clean,
    "status": status
  }
  return result

if __name__ == "__main__":
  stat = gitstatus(os.getcwd())
  print(json.dumps(stat))
