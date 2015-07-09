Substance Screwdriver
=====================

A custom python application that serves as command line tool to better manage npm applications with
child modules. The `npm` documentation says that `npm link` should be used for that.
However, this approach is not very elegant, and particularly useless when you have different versions
of the same module in different contexts, as `npm link` works globally. Furthermore, `npm link` is not working
that well under Windows.

The `screwdriver` manages npm modules manually, cloning modules which have a git version field, and using `npm install` for others.

```
  dependencies: {
    "handlebars": "*",
    "substance": "substance/substance#master",
    "other": "substance/other#ea60d5e057bc1c6dcee62346a6433b01cbfeeb2c",
  }
```

Only those modules are considered as source modules which have non-SHA-1 branch tag. In the above example, "substance" would be cloned as a git repo, but `other` would be installed via `npm install`.


Installation
------------

Clone the Screwdriver repository into some arbitrary folder:

```bash
    $ git clone https://github.com/substance/screwdriver.git
```

Run setup:

```bash
    $ cd screwdriver
    $ sudo python setup.py install --record screwdriver.files
```

Ǹow you should be able to run the Screwdriver app from command line:

```bash
    $ screwdriver --help
```

Uninstall
---------

You can remove all files using:

```bash
    $ cd screwdriver
    $ sudo rm $(cat screwdriver.files)
```

Branch and Merge Workflow
-------------------------

1. `git checkout -b :branch_name`

2. Adapt `package.json` if you want to switch to a dev branch of a module (optional)

3. `screwdriver --update` (necessary after switching a branch of a module)

4. Do development

5. Bump module shas (optional)

6. Merge changes back into master

7. Commit and push changes

8. `screwdriver --update` (necessary if you were on a branch of a module)
