# animExport
animExport is a Blender Addon for exporting animation into a format usable in Arma 3 model.cfg files.
anim2cfg is taken as foundation and animExport is built on top of it to provide ease of use.

## Features
* Export of the (matrix_world) location/rotation of the active object(s) or bone(s) of an armature according to active animation.
* The location/rotation of the object may be animated/constrained.
* Export relative to a parent object is possible.

## Installation

Blender:
* 'Edit' -> 'Preferences'
* Select the 'Add-ons' tab
* 'Install...'
* Navigate to the 'animExport.py' file and select it
* Install it by pressing 'Install Add-on from File...'
* Enable the addon by setting the checkmark in front of it

## Known Issues
* the export of n frames resulting in only n-1 animation pairs is not a bug but by design

please report any other issue at https://github.com/talyataya/animExport/issues

## Usage ##
Blender:
* Choose the animation you want to export, make sure it is active animation by verifying through playback.
* If Armature mode will not be used, select object(s) in the Outliner.
* Go to 'File' -> 'Export' -> 'Arma 3 model.cfg (.cfg/.hpp)'
* Set the export options
    * 'Parent Object': Animations will be exported relative to this object. When not set the origin will be used.
	* 'Armature Object': If set, armature of this object will be used instead of selected object(s). Bone names are used as selection names.
    * 'Start Frame': Starting frame to export.
    * 'End Frame': End frame to export.
    * 'Selection Names': Selection names to be used in the model.cfg. Defaults to the name of the objects. Automatically retrieved from chosen objects in the Outliner.
    * 'Source Name': Source name to be used in the model.cfg.
    * 'minValue': minValue to be used in the model.cfg for the first animation.
    * 'maxValue': maxValue to be used in the model.cfg for the last animation.
    * 'Precision': Number of decimal places.
	* 'Add Folder': Whether or not a folder will be created for additional files.(If only one object/bone exists, no folder will be created.)
	* 'Folder Name': Name of the generated folder. If unset, Source name will be used as folder name. If folder with same name exists, that folder will be used.
* Navigate the directory tree and set/select the file name (existing files will be OVERWRITTEN)
* 'Export model.cfg'

In a text editor of your choice:
* Prepare a basic model.cfg with all the necessary skeletonBones
	You can use https://github.com/Talyataya/skelExport to extract skeletonBones, make sure you disable parent extraction.
* #include the exported file(s) within the Animations class of your model.cfg