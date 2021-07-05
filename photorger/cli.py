#!/usr/bin/env python
# coding: utf-8

"""Photorger.

Usage:
  photorger.py info <filename>...
  photorger.py move [--source=<sourcepath>] [--dest=<destpath>] [--noclean] [--nodeep] [--nocache] [--norecurse] [--norename] [--copy] [--pretend] [--verbose]
  photorger.py clean [--source=<sourcepath>] [--dest=<destpath>] [--nodeep] [--nocache] [--norecurse] [--pretend]
  photorger.py clean [--source=<sourcepath>] [--oldest|--newest] [--shortest|--longest] [--nodeep] [--nocache] [--norecurse] [--force] [--pretend]

  photorger.py (-h | --help)
  photorger.py --version

Options:
  -h --help              Show this screen.
  --version              Show version.
  --source=<sourcepath>  Root directory of folder to process (default to current).
  --target=<destpath>    Root directory of destination folder (default to current).
  --noclean              Don't remove duplicates
  --nodeep               Use just size and date or hash comparison when detecting duplicates (not content).
  --nocache              Don't save completed item status to cache.
  --norecurse            Don't recurse into child folders.
  --norename             Don't move files (with rename) if the target has a file with same name already.
  --copy                 Create copies of original files rather than moving them.
  --pretend              Show what would be done but don't actually do it.
  --verbose              Print a result line even for files that are not moved.
  --oldest               Keep oldest file(s) in duplicate group.
  --newest               Keep newest file(s) in duplicate group.
  --shortest             Keep file(s) with shortest paths in duplicate group.
  --longest              Keep file(s) with longest paths in duplicate group.
  --force                Keep at most one instance of a duplicate set even when delete rules aren't unambiguous.
"""

import os
from docopt import docopt
from .photorger import *


def main():
    global source, target,  pretend, copy, verbose, force
    global newest, oldest, shortest, longest
    global norecurse, noclean, nodeep, nocache, norename
    arguments = docopt(__doc__, version='Photorger 1.0')
    source = arguments['--source']
    target = arguments['--dest']
    if source is None:
        source = os.getcwd()
    else:
        source = os.path.abspath(source)
    if target is None:
        if not arguments['clean']:
            target = os.getcwd()
    else :
        target = os.path.abspath(target)
    norecurse = arguments['--norecurse']  # TODO: make sure this behaves as expected and processes right folder
    noclean = arguments['--noclean']
    pretend = arguments['--pretend']
    nocache = arguments['--nocache']
    nodeep = arguments['--nodeep']
    norename = arguments['--norename']
    copy = arguments['--copy']
    verbose = arguments['--verbose']
    newest = arguments['--newest']
    oldest = arguments['--oldest']
    shortest = arguments['--shortest']
    longest = arguments['--longest']
    force = arguments['--force']

    if arguments["info"]:
        info_main(arguments['<filename>'][0])

    if arguments["clean"]:
        # Delete files from source folder that have copies in target folder
        clean_main()

    if arguments["move"]:
        move_main()
        save_cache() 


if __name__ == '__main__':
    main()
