import bpy


class RigCopyBoneTransforms(bpy.types.Operator):
    """Copy bone transformms from a source armature to a target"""
    bl_idname = "pose.rig_copy_bone_transforms"
    bl_label = "Copy Bone XForms from Source to Target"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        source = context.active_object
        target = [obj for obj in context.selected_objects if obj != source][0]
        copy_bone_transforms(source, target)
        return {'FINISHED'}


class RigToggleHandFollow(bpy.types.Operator):
    """Toggle Hand Follows Torso for IK hands"""
    bl_idname = "pose.rig_toggle_hand_follow"
    bl_label = "Toggle IK hand follow torso"
    bl_context = "pose"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'POSE' and
            context.active_object.name == 'rig_ctrl')

    def execute(self, context):
        hand_ik_bones = [
            bone for bone in context.active_object.pose.bones
            if bone.name.startswith('forearm_ik')]
        constraints_toggle_child_of(hand_ik_bones)
        return {'FINISHED'}


class RigToggleHandInheritRotation(bpy.types.Operator):
    """Toggle Hands inheriting rotation"""
    bl_idname = "pose.rig_toggle_hand_inherit_rotation"
    bl_label = "Toggle Hand inherit rotation"
    bl_context = "pose"

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'POSE'and
            context.active_object.name == 'rig_ctrl')

    def execute(self, context):
        hand_bones = [
            bone for bone in context.active_object.pose.bones
            if bone.name.startswith('hand.')]
        bones_toggle_property(hand_bones, 'use_inherit_rotation')
        return {'FINISHED'}


class RigORGDeform(bpy.types.Operator):
    """Toggle Deform option on all selected bones"""
    bl_idname = "pose.rig_org_to_deform"
    bl_label = "Swap ORG/DEF deform bones"
    bl_context = "pose"

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE'

    def execute(self, context):
        bones_swap_org_def(context.selected_pose_bones)
        return {'FINISHED'}


class RigUnityUtils(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Rig to Unity"
    bl_idname = "POSE_RIG_TO_UNITY"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "POSE"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label('Bone Utilities')
        col.operator('pose.rig_org_to_deform')
        col.operator('pose.rig_copy_bone_transforms')

        col = layout.column(align=True)
        col.label('Pose Utilities')
        col.operator('pose.rig_toggle_hand_follow')
        col.operator('pose.rig_toggle_hand_inherit_rotation')


def find_or_add_constraint(bone, constraint):
    con = [con for con in bone.constraints if con.type in constraint]
    if not con:
        con = bone.constraints.new(type=constraint)
    else:
        con = con[0]
    return con


def constraints_toggle_child_of(bones):
    for bone in bones:
        child_of = find_or_add_constraint(bone, 'CHILD_OF')
        child_of.influence = 1 if child_of.influence == 0 else 0


def bones_toggle_property(bones, property_name):
    for bone in bones:
        prop_value = getattr(bone.bone, property_name)
        setattr(bone.bone, property_name, not prop_value)


def bones_swap_org_def(bones):
    for bone in bones:
        bone.bone.use_deform = not bone.bone.use_deform


def copy_bone_transforms(source, target):
    # thanks to https://blender.stackexchange.com/a/15940
    # Assume, that context.object is an armature
    context = bpy.context
    scene = context.scene

    # Store the bone data of source:
    bpy.ops.object.mode_set(mode='EDIT')
    bone_store = []
    for ebone in source.data.edit_bones:
        bone_store.append([
            ebone.name, ebone.head.copy(), ebone.tail.copy(), ebone.roll])
    bpy.ops.object.mode_set(mode='OBJECT')

    scene.objects.active = target
    bpy.ops.object.mode_set(mode='EDIT')

    # Transfer the bones to the other armature.
    # The following works because the bone data is defined in local space:

    ebones = target.data.edit_bones
    for bone_data in bone_store:
        bid = bone_data[0]
        if bid in ebones:
            ebone = ebones[bid]
            ebone.head = bone_data[1].copy()
            ebone.tail = bone_data[2].copy()
            ebone.roll = bone_data[3]

    bpy.ops.object.mode_set(mode='OBJECT')

    scene.objects.active = source


def register():
    bpy.utils.register_class(RigUnityUtils)
    bpy.utils.register_class(RigCopyBoneTransforms)
    bpy.utils.register_class(RigToggleHandFollow)
    bpy.utils.register_class(RigToggleHandInheritRotation)
    bpy.utils.register_class(RigORGDeform)


def unregister():
    bpy.utils.unregister_class(RigUnityUtils)
    bpy.utils.unregister_class(RigCopyBoneTransforms)
    bpy.utils.unregister_class(RigToggleHandFollow)
    bpy.utils.unregister_class(RigToggleHandInheritRotation)
    bpy.utils.unregister_class(RigORGDeform)

if __name__ == "__main__":
    register()
