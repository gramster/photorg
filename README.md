# photorger

To install, you need a working Python environment with pip. Then clone this repo and in the root run:

    PBR_VERSION=1.0.0 python -m pip install .

There are a bunch of command line arguments that will control the behavior; use:

    photorger --help
    
to see them. There are three main commands: `info`, `move` and `clean`, to get EXIF info, move files into folders based on creation date, and remove duplicates, respectively. `clean` and `move` can be destructive and result in the loss of files for which I take no responsibility; use at your own risk. You can use `--pretend` to see what actions would be taken in a trial run. It should be the case that at the very least no file will be deleted unless there is at least one byte-for-byte duplicate elsewhere, but I make no guarantee of that claim.

    photorger info <fname>
    
will dump EXIF tags from a file.

    photorger clean --source=<folder> --dest=<folder>
    
will remove any files in the source folder that have duplicates in the dest folder. The source and dest folders can be disjoint, or the source folder can be a subfolder of the dest folder.

    photorger clean --source=<folder>
    
is similar but searches just a single folder tree, and in this case if it finds a set of duplicates it will keep the file(s) that are in folders with a YYYY/MM/DD format; this behavior can be changed with other arguments. After running this with no argument or with the arguments you prefer, you will likely still have duplicates, but you can run it again with a `--force` argument which will then use lexical ordering on the file paths to determine a single file in each duplicate group to keep, eliminating all other duplicates.

    photorger move --source=<folder> --dest=<folder>
    
will try to figure out the dates photo files in the source directory were taken and move them to folders of the form YYYY/MM/DD/fname in the dest directory (both arguments are optional and will default to the current working directory). It will use EXIF tags if present, else will try infer the date from the file name. If it tries to move a file and the target file already exists, it will just delete the source file (if identical) or move and rename it (if not identical).

It can move files across file systems; if a simple rename fails it will fall back to copy/delete.

This works for Unix-style paths only, so Mac/Linux and not Windows. 

I take no responsibility for any loss or damage from using this script. Use --pretend until you have some confidence that it is not going to ruin your life.

