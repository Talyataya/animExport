# Copyright (C) 2019 4d4a5852, 2021 Talya_taya
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

bl_info = {
    "name": "animExport: Animation to model.cfg",
    "author": "Talya_taya",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "location": "File -> Export",
    "description": "Export animations to Arma 3 model.cfg",
    "warning": "",
    "wiki_url": "https://github.com/Talyataya/animExport",
    "tracker_url": "https://github.com/Talyataya/animExport/issues",
    "category": "Import-Export",
    }

import bpy
import bpy_extras
from bpy.utils import register_class, unregister_class
from math import degrees
from mathutils import Matrix, Vector
import re
import os
import errno

def sanitize_classname(text):
    return re.sub('[^A-Za-z0-9_]', '_', text)

def create_file_name_and_path(file, selection_name, create_folder, folder_name):
    file_path = bpy.path.native_pathsep(file)
    file_parent_dir, file_fullname = os.path.split(file_path)
    if create_folder:
        file_parent_dir = os.path.join(file_parent_dir, folder_name)
    file_ext = "hpp" # file_fullname.split('.')[-1] (extra ones get .hpp regardless of requested extension as they are include files.)
    file_name = bpy.path.display_name_from_filepath(file)
    new_file_name = f"{file_name}_{selection_name}.{file_ext}"
    new_file_path = os.path.join(file_parent_dir, new_file_name)
    return new_file_name, new_file_path
    
def generate_bone_objects(armature_object_str):
    bpy.data.collections.new("animExport collection")
    try:
        armature_object = bpy.data.objects[armature_object_str]
    except KeyError:
        return 1, []
    armature = armature_object.data
    if type(armature) != bpy.types.Armature:
        return 2, []
    objects = []
    for bone in armature.bones:
        bpy.ops.mesh.primitive_plane_add(size=0, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        new_object = bpy.context.active_object
        new_object.name = bone.name
        bpy.data.collections['animExport collection'].objects.link(new_object)
        objects.append(new_object)
        
        copyTransform_constraint = new_object.constraints.new('COPY_TRANSFORMS')
        copyTransform_constraint.target = armature_object
        copyTransform_constraint.subtarget = bone.name
    return 0, objects 

def delete_bone_objects():
    try:
        collection = bpy.data.collections["animExport collection"]
        for obj in collection.objects.values():
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection, do_unlink=True)
    except KeyError:
        pass

def create_folder(path, name):
    path = os.path.split(path)[0]
    try:
        os.mkdir(os.path.join(path, name))
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            #We are allowing user to get all generated files in an existing folder.
            pass

def export_anim(file, generate_multiple_files, obj, obj_index=0, source_name='', source_address='clamp', parent_name='',
                frame_start=0, frame_end=0, min_value=0.0, max_value=1.0,
                precision=7, create_folder=True, folder_name=''):
    frames = range(frame_start, 1 + frame_end)
    last = None
    i = 0
    selection_name = obj.name
    parent_object = None
    parent_matrix = Matrix()
    if parent_name != '':
        try:
            parent_object = bpy.context.scene.objects[parent_name]
        except KeyError:
            return (-1, 0)
    file_path = file
    if generate_multiple_files:
        file_name, file_path = create_file_name_and_path(file, selection_name, create_folder, folder_name)
        with open(file, f"{'w' if obj_index == 0 else 'a'}") as main_cfg:
            prefix = ""
            if create_folder:
                prefix = f"{folder_name}\\"
            main_cfg.write(f"#include \"{prefix}{file_name}\"\n")
    new_line_char = "\n"
    with open(file_path, 'w') as cfg:
        for f in frames:
            bpy.context.scene.frame_set(f)
            if parent_object is not None:
                parent_matrix = parent_object.matrix_world
            curr = parent_matrix.inverted() @ obj.matrix_world
            if last is not None:
                p = curr.to_translation()
                q = (curr @ last.inverted()).to_quaternion()
                d = p - last.to_translation()
                length = d.length
                if round(length, precision) == 0:
                    d = Vector((1, 0, 0))
                dn = d.normalized()
                q_axis = q.axis.normalized()
                q_angle = degrees(q.angle)
                if round(q_angle, precision) == 0:
                    q_axis = Vector((1, 0, 0))
                curr_min_value = min_value + i*(max_value - min_value)/(len(frames) - 1)
                curr_max_value = min_value + (i + 1)*(max_value - min_value)/(len(frames) - 1)
                cfg.write(f"class {sanitize_classname(source_name)}_{sanitize_classname(selection_name)}_trans_{i} {{\n"
                          f"    type       = direct;\n"
                          f"    source     = {source_name};\n"
                          f"{f'    sourceAddress = {source_address};{new_line_char}' if source_address != 'clamp' else ''}"
                          f"    selection  = {selection_name};\n"
                          f"    axisPos[]  = {{0, 0, 0}};\n"
                          f"    axisDir[]  = {{{dn.x:.{precision}f}, {dn.z:.{precision}f}, {dn.y:.{precision}f}}};\n"
                          f"    angle      = 0;\n"
                          f"    axisOffset = {length:.{precision}f};\n"
                          f"    minValue   = {curr_min_value:.{precision}f};\n"
                          f"    maxValue   = {curr_max_value:.{precision}f};\n"
                          f"}};\n"
                          f"class {sanitize_classname(source_name)}_{sanitize_classname(selection_name)}_rot_{i} {{\n"
                          f"    type       = direct;\n"
                          f"    source     = {source_name};\n"
                          f"{f'    sourceAddress = {source_address};{new_line_char}' if source_address != 'clamp' else ''}"
                          f"    selection  = {selection_name};\n"
                          f"    axisPos[]  = {{{p.x:.{precision}f}, {p.z:.{precision}f}, {p.y:.{precision}f}}};\n"
                          f"    axisDir[]  = {{{q_axis.x:.{precision}f}, {q_axis.z:.{precision}f}, {q_axis.y:.{precision}f}}};\n"
                          f"    angle      = {q_angle:.{precision}f};\n"
                          f"    axisOffset = 0;\n"
                          f"    minValue   = {curr_min_value:.{precision}f};\n"
                          f"    maxValue   = {curr_max_value:.{precision}f};\n"
                          f"}};\n")
                i += 1
            last = curr.copy()
    return (0, i)

class ANIMEXPORT_OT_ModelCfgExport(bpy.types.Operator,
                                 bpy_extras.io_utils.ExportHelper):
    bl_idname = "animexport.modelcfgexport"
    bl_label = "Export model.cfg"
    bl_description = "Export model.cfg"
    filename_ext = ".hpp"
    filter_glob: bpy.props.StringProperty(
        default="*.cfg;*.hpp",
        options={'HIDDEN'})
    source_name: bpy.props.StringProperty(
        name="Source Name",
        description="Source name to be used in the model.cfg",
        default='')
    source_address: bpy.props.EnumProperty(
        items=[("clamp", "Clamp", "", 1),
               ("loop", "Loop", "", 2),
               ("mirror", "Mirror", "", 3)],
        name="Source Address",
        description="Does the animation loop or not?",
        default="clamp")
    parent_name: bpy.props.StringProperty(
        name="Parent Object",
        description=("Animations will be exported relative to this object.\n"
                     "When not set the origin will be used"),
        default='')
    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        description="Starting frame to export",
        default=0)
    frame_end: bpy.props.IntProperty(
        name="End Frame",
        description="End frame to export",
        default=0)
    min_value: bpy.props.FloatProperty(
        name = "minValue",
        description="minValue to be used in the model.cfg for the first animation",
        default=0.0)
    max_value: bpy.props.FloatProperty(
        name = "maxValue",
        description="maxValue to be used in the model.cfg for the last animation",
        default=1.0)
    precision: bpy.props.IntProperty(
        name="Precision",
        description="Number of decimal places",
        min=0,
        default=7)
    create_folder: bpy.props.BoolProperty(
        name="Create Folder",
        description="Creates a folder for additionally created files",
        default=True)
    folder_name: bpy.props.StringProperty(
        name="Folder Name",
        description=("Folder's name. If unset, uses Source Name instead.\n"
                     "If a folder with same name exists in directory,\n"
                     "files will be put there instead"),
        default='')
    armature_object: bpy.props.StringProperty(
    name="Armature Object",
    description="If set, animations will be exported using this object's armature, ignoring selected objects",
    default='')

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        return super().invoke(context, event)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column()
        col.prop_search(self, "parent_name", scene, "objects")
        col.prop_search(self, "armature_object", scene, "objects")
        col.prop(self, "frame_start")
        col.prop(self, "frame_end")
        col.label(text="model.cfg")
        col.label(text="Selected objects will be exported to respective files.")
        col.prop(self, "source_name")
        col.prop(self, "source_address")
        col.prop(self, "min_value")
        col.prop(self, "max_value")
        col.prop(self, "precision")
        col.prop(self, "create_folder")
        col_sub = col.column()
        col_sub.enabled = self.create_folder
        col_sub.prop(self, "folder_name")
        col_info = col.column()
        col_info.label(text="")
        col_info.label(text="Selection Based Inputs:")
        col_info.label(text="Active animation(visible) will be exported.")
        col_info.label(text="If Armature Object unset, selected objects in Outliner will be exported.")

    def execute(self, context):
        try:
            current_frame = bpy.context.scene.frame_current
            is_armature_mode = self.armature_object != ""
            if is_armature_mode:
                status, objects = generate_bone_objects(self.armature_object)
                if status == 1:
                    self.report({'ERROR'}, "Armature object does not exist.")
                    return {'FINISHED'}
                if status == 2:
                    self.report({'ERROR'}, "Failed to generate objects from bones. Make sure the object contains a valid armature.")
                    return {'FINISHED'}
            else:
                objects = bpy.context.selected_objects
                
            if len(objects) > 0:
                folder_name = self.folder_name
                source_name = self.source_name
                if source_name == '':
                    source_name = 'foobar'
                    
                generate_multiple_files = len(objects) > 1
                if generate_multiple_files and self.create_folder:
                    if folder_name == '':
                        folder_name = source_name
                    create_folder(self.filepath, folder_name)
                for obj_index, obj in enumerate(objects):
                    result, nAnims = export_anim(self.filepath,
                                                 generate_multiple_files,
                                                 obj,
                                                 obj_index,
                                                 source_name=source_name,
                                                 source_address=self.source_address,
                                                 parent_name=self.parent_name,
                                                 frame_start=self.frame_start,
                                                 frame_end=self.frame_end,
                                                 min_value=self.min_value,
                                                 max_value=self.max_value,
                                                 precision=self.precision,
                                                 create_folder=self.create_folder,
                                                 folder_name=folder_name
                                                 )
                    if result == 0:
                        self.report({'INFO'}, f"{nAnims + 1} frames exported as {nAnims} animation pairs")
                    elif result != 0:
                        self.report({'ERROR'}, "Unknown Error")
            else:
                if is_armature_mode:
                    error_message = "Failed to generate objects from bones. Selected object's armature does not contain any bones."
                else:
                    error_message = "You did not select any objects. Make sure you have objects selected in the Outliner(Shift + F9) and try again."
                self.report({'ERROR'}, error_message)
        except:
            raise
        finally:
            if is_armature_mode:
                delete_bone_objects()
            bpy.context.scene.frame_set(current_frame)
        return {'FINISHED'}

def ModelCfgExportMenuFunc(self, context):
    self.layout.operator(ANIMEXPORT_OT_ModelCfgExport.bl_idname,
                         text="Arma 3 model.cfg (.cfg/.hpp)")

classes = (
    ANIMEXPORT_OT_ModelCfgExport,
    )

def register():
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_file_export.append(ModelCfgExportMenuFunc)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(ModelCfgExportMenuFunc)
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == '__main__':
    register()
