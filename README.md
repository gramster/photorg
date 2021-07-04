# photorg

To install, you need a working Python environment. Then clone this repo and in the root run:

    PBR_VERSION=1.0.0 pip install .

To run:

    photorg info <fname>
    
will dump EXIF tags from a file.

    photorg clean --source=<folder> --dest=<folder>
    
will remove any files in the source folder that have duplicates in the dest folder.

    photorg move
    
will try to figure out the dates a photo was taken and move it to a folder of the form YYYY/MM/DD/file.

There are a bunch of command line arguments that will control the behavior; use:

    photorg --help
    
to see them.

This works for Unix-style paths only, so Mac/Linux and not Windows. 

I take no responsibility for any loss or damage from using this script. Use --pretend until you have some confidence that it is not going to ruin your life.

