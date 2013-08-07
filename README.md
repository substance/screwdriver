Substance Screwdriver
=====================

A custom python application that serves as command line tool to manage Substance applications.


Installation
------------

Clone the Screwdriver repository into some arbitrary folder:

```bash
    $ git clone https://github.com/substance/screwdriver.git
```

Run setup:

```bash
    $ cd screwdriver
    $ sudo python setup.py install
```

Ǹow you should be able to run the Screwdriver app from command line:

```bash
    $ substance --help
```

Uninstall
---------

To be able to uninstall Substance Screwdriver you have to install it using:

```bash
    $ cd screwdriver
    $ python setup.py install --record screwdriver.files
```

Then you can remove all files using:

```bash
    $ cd screwdriver
    $ sudo rm $(cat screwdriver.files)
```

Usage
-----

### Clone a Substance application

Cloning is still done best using a conventional `git clone`. E.g.,

```bash
    $ git clone https://github.com/substance/substance.git -b 0.5.x substance-sandbox
```

Then you have to do an initial update

A Substance project has a `project.json` file which specifies dependencies and their versions.


### Updating all Sub-Modules

To update all configured branches of the sub-modules run

```bash
    $ substance --update
```

This downloads all dependencies and does an `npm` installation.

### Checking out configured Branches

To checkout all modules in that version you can run

```bash
    $ substance --checkout
```

### Pushing all Sub-Modules

To push all commits in the configured branches of the sub-modules run

```bash
    $ substance --push
```


### Batching Git-Commands

To do special `git` related things on all sub-modules it is possible to run

```bash
    $ substance --git -- [git-command-line-arguments...]
```

Notice the separation `--` which are necessary to distinct arguments passed to the ScrewDriver from `git` arguments.


Workflows
---------

### Branching

To create a feature branch it is best to switch all sub-modules simultanously.

```bash
    $ substance --branch [branch_name]
```

This creates branches and updates `project.json` to reflect these versions.
You should review the change and commit it in the new branch.
After that you can use the `push` option to push the branches.

However, in cases where you are just working on a single or only a few modules you would create the branches and adapt the `project.json` manually.


### Contributing / Forking

To contribute to Substance you should clone the Substance stack first.

Then you should create your personal fork of the module you want contribute to:
see [here](https://help.github.com/articles/fork-a-repo) for explanations.

After that you should adapt the `project.json` to use your personal fork. E.g.,

```json
{
  "modules": [
    ...
    {
      "repository": "git@github.com:oliver----/chronicle.git",
      "folder": "node_modules/substance-chronicle",
      "branch": "my_feature"
    },
    ...
  ]
}
```
