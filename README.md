# kbpcb Post Processor
The output of [mrkeeb's kbpcb](http://kbpcb.mrkeebs.com/) labels components according to their function.
This is useful for visually keeping track of which key is which, but KiCad requires that all component references have a numeric suffix to be annotated correctly.
Importing the output directly and attempting to work with it will cause things to break as soon as KiCad trys to reannotate anything.

This script will update the names of all the relevant components so that the files can be further modified and implemented in your design.

## Usage
* Copy the `.sch` and `.kicad_pcb` files of from the kbpcb output to this folder.
* Run `python3 post_process.py`
* If you are using the kbpcb output as your starting point for your project, copy the files back into the kbpcb output folder.
* If you want to use these files in an existing project, copy them to your project folder, and rename them accordingly
    * The `.sch` file can be named anything, as long as it matches whatever file name you use for the hierarchical sheet inside the root schematic of your project.
    * the `.kicad_pcb` file should be renamed to be the same as your root `.sch` file.
* Open your project in KiCad
* Open the `.sch` file and annotate it.
    * You may get warnings about duplicate timestamps, this is normal.
* Open the PCB file from Eeschema
* Click the `Update PCB from Schematic` button
* Set the Match Method to `Re-associate footprints by reference`
    * If you don't do this KiCad may delete components that have already been laid out and force you to place them manually
* Click `Update PCB`
* After this you should be able to work on the project normally
    * `Keep existing symbol to footprint associations` should work correctly now.

## Notes
The code isn't particularly clean, it's a simple enough script that I'm not bothering to optimize it.