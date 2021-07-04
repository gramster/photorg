# photorg

To install, you need a working Python environment with pip. Then clone this repo and in the root run:

    PBR_VERSION=1.0.0 python -m pip install .

To run:

    photorg info <fname>
    
will dump EXIF tags from a file.

    photorg clean --source=<folder> --dest=<folder>
    
will remove any files in the source folder that have duplicates in the dest folder. The source and dest folders can be disjoint, or the source folder can be a subfolder of the dest folder. It would make no sense the other way around. Note that it can take a long time before this command starts producing log messages, as it collects data on all the files first.

    photorg move
    
will try to figure out the dates photo files were taken and move them to folders of the form YYYY/MM/DD/fname. It will use EXIF tags if present, else will try infer from the file name. If it tries to move a file and the target file already exists, it will just delete the source file (if identical) or move and rename it (if not identical).

It can move files across file systems; if a simple rename fails it will fall back to copy/delete.

There are a bunch of command line arguments that will control the behavior; use:

    photorg --help
    
to see them.

This works for Unix-style paths only, so Mac/Linux and not Windows. 

I take no responsibility for any loss or damage from using this script. Use --pretend until you have some confidence that it is not going to ruin your life.

