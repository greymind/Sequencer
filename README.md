# Greymind Sequencer for Maya
Helps manage animations and related actions in Maya.

## Installation
Place this file in the (Documents\maya\<maya version>\scripts) folder.

## Usage
To invoke this script, use the following commands in the python mode of the script editor:

```python
import Sequencer as Seq
reload(Seq)
Seq.Run()
```

You may middle-mouse drag these lines to the shelf to create a shortcut toolbar button.

## FBX Functionality
You need the fbxmaya plugin loaded for FBX functionality.
Note that the operating FBX file mode is FBX200611 ASCII.

You will have to first set up your preferred export settings and then use the Sequencer's
export functionality. Safest way to do so is to export the full file once to a temporary
file with the FBX settings set correctly and verify.

## Fixing Issues
If you need to clean up Sequencer, issue the following command in the MEL mode of the script editor:

```python 
delete SequencerData;
```