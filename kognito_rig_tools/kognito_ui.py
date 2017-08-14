import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
from mathutils.geometry import normal, intersect_point_line


class FKIKSwitcher(bpy.types.Operator):
    """
    Universal IKFK methods coupled with explict rig bone/constraint definitions
    """

    bl_idname = 'pose.kognito_fkik'
    bl_label = 'Kognito Rig FK IK Switch'
    bl_description = 'Kognito rig FK IK seamless switcher'
    
    ik = bpy.props.BoolProperty(default=True)
    side = bpy.props.EnumProperty(
        items=[('left', 'left', 'left'), ('right', 'right', 'right')])

    # should later use some kind of preset/config system
    chain = ['upper_arm', 'forearm', 'hand']
    iks = ['forearm_ik_pole', 'forearm_ik']
    suffixes = {'left': '.L', 'right': '.R'}
    prop = ['props', 'IK_arms']
    layers = {'left': [6, 5], 'right': [9, 8]}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'POSE' and 'kognito_rig' in context.object.keys()
            )

    def fk_match(self, ob, chain, iks):
        for bone in chain:
            pose_bone = ob.pose.bones[bone]
            bake_rotation_scale(pose_bone)

    def ik_match(self, ob, chain, iks):
        target = ob.pose.bones[iks[-1]]
        source = ob.pose.bones[chain[-1]]
        use_tail = False
        loc_copy(source, target, use_tail)
        rot_copy(source, target)
        #use the pole angle to figure out the rest
        constraints = (
            c for c in ob.pose.bones[chain[-2]].constraints if c.type == 'IK'
            )
        for constraint in constraints:
            pole_angle = constraint.pole_angle
            print(pole_angle)
        pole_position(
            [ob.pose.bones[b] for b in chain],
            ob.pose.bones[iks[0]],
            pole_angle)
        for bone in chain:
            ob.pose.bones[bone].matrix_basis = Matrix()
        
    def execute(self, context):
        ob = context.object
        suffix = self.suffixes[self.side]
        chain = ["{}{}".format(c, suffix) for c in self.chain]
        iks = ["{}{}".format(c, suffix) for c in self.iks]
        prop_holder = ob.pose.bones[self.prop[0]]
        prop = '{}{}'.format(self.prop[1], suffix)
        influence = prop_holder[prop]
        if self.ik:
            ob.data.layers[self.layers[self.side][-1]] = True
            ob.data.layers[self.layers[self.side][0]] = False
            # prop_holder[prop] = 1.0; return {'CANCELLED'} # comment out for proper operation
            self.ik_match(ob, chain, iks)
            prop_holder[prop] = 1.0
        else:
            ob.data.layers[self.layers[self.side][-1]] = False
            ob.data.layers[self.layers[self.side][0]] = True
            self.fk_match(ob, chain, iks)
            prop_holder[prop] = 0.0
        return {'FINISHED'}


def bake_rotation_scale(bone):
    """ bake constrained transform into bone rot/scale """
    data_bone = bone.id_data.data.bones[bone.name]
    bone_mat = data_bone.matrix_local
    parentless_mat = bone_mat.inverted() * bone.matrix
    if not bone.parent:
        rot_mat = scale_mat = parentless_mat
    else:
        parentposemat = bone.parent.matrix
        parentbonemat = data_bone.parent.matrix_local
        parented_mat = (
            (parentbonemat.inverted() * bone_mat).inverted() *
            parentposemat.inverted() *
            bone.matrix
            )
        rot_mat = (
            parented_mat if data_bone.use_inherit_rotation else parentless_mat)
        scale_mat = (
            parented_mat if data_bone.use_inherit_scale else parentless_mat)
        
    if bone.rotation_mode == 'AXIS_ANGLE':
        bone.rotation_axis_angle= rot_mat.to_quaternion().to_axis_angle()
    elif bone.rotation_mode == 'QUATERNION':
        bone.rotation_quaternion = rot_mat.to_quaternion()
    else:
        bone.rotation_euler = rot_mat.to_euler(
            bone.rotation_mode, bone.rotation_euler)
    bone.scale = scale_mat.to_scale()
    
    
def loc_copy(source, target, use_tail):
    data_target = target.id_data.data.bones[target.name]
    target_mat = data_target.matrix_local
    if not data_target.use_local_location:
        target_mat = Matrix.Translation(target_mat.to_translation())
    if use_tail:
        location = source.tail
    else:
        location = source.matrix.to_translation()
    if target.parent:
        parentposemat = bone.parent.matrix
        parentbonemat = data_bone.parent.matrix_local
        target.location = (
            (parentbonemat.inverted() * target_mat).inverted() *
            parentposemat.inverted() *
            location
            )
    else:
        target.location = target_mat.inverted() * location

        
def rot_copy(source, target):
    """ duplicates code from loc_copy, should be refactored """
    data_target = target.id_data.data.bones[target.name]
    target_mat = data_target.matrix_local
    parentless_mat = target_mat.inverted() * source.matrix
    if not target.parent:
        mat = parentless_mat
    else:
        parentposemat = target.parent.matrix
        parentbonemat = data_target.parent.matrix_local
        parented_mat = (
            (parentbonemat.inverted() * bone_mat).inverted() *
            parentposemat.inverted() *
            source.matrix
            )
        mat = (
            parented_mat if data_bone.use_inherit_rotation else parentless_mat)
    if target.rotation_mode == 'AXIS_ANGLE':
        target.rotation_axis_angle= mat.to_quaternion().to_axis_angle()
    elif target.rotation_mode == 'QUATERNION':
        target.rotation_quaternion = mat.to_quaternion()
    else:
        target.rotation_euler = mat.to_euler(
            target.rotation_mode, target.rotation_euler)   
        

def genericmat(bone, mat, ignoreparent):
    '''
    Puts the matrix mat from armature space into bone space
    '''
    data_bone = bone.id_data.data.bones[bone.name]
    bonemat_local = data_bone.matrix_local #self rest matrix
    if bone.parent:
        parentposemat = bone.parent.matrix
        parentbonemat = data_bone.parent.matrix_local
    else:
        parentposemat = None
        parentbonemat = None
    if parentbonemat == None or ignoreparent:
        newmat = bonemat_local.inverted() * mat
    else:
        bonemat = parentbonemat.inverted() * bonemat_local
        newmat = bonemat.inverted() * parentposemat.inverted() * mat
    return newmat

    
def pole_position(chain, pole, pole_angle):
    """
    pole target based on roll angle of chain base
    """
    #Poll target for elbow is on the + X axis, for the knee we need to lock
    #the elbow to rotate along one axis only
    vec = Vector((4, 0.0, 0.0))
    vec.rotate(Euler((0, -pole_angle, 0)))
    offmatelbow = Matrix.Translation(vec)
    
    offmatarm = chain[0].matrix * offmatelbow


    pole.location = genericmat(pole,
       offmatarm, False).to_translation()
    return
    
    
    
    
    
    coordinate_system = chain[0].matrix
    line_points = [
        chain[0].matrix.to_translation(),
        chain[-2].tail]
    mid_point =chain[-2].matrix.to_translation()
    center, dummy = intersect_point_line(mid_point, line_points[0], line_points[1])
    radius = (mid_point - center).length
    vector = Vector((1.2 * radius, 0, 0))
    vector = Vector((.5, 0,0))
    # rotation = Quaternion(Vector((0, 1, 0)), pole_angle)
    # vector.rotate(rotation)
    pole.location = coordinate_system * vector


class KognitoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Rig Control"
    bl_idname = "VIEW_3D_PT_KOGNITO"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Kognito"
    bl_context = "posemode"
    
    @classmethod
    def poll(cls, context):
        return 'kognito_rig' in context.object.keys()

    def draw(self, context):
        layout = self.layout
        ob = context.object
        switcher = FKIKSwitcher.bl_idname
        props = ob.pose.bones["props"]
        box = layout.box()
        box.label("IK/FK arms:")
        def fk_ik_controls(layout, side, prop):

            def clicker(layout, side, state, icon):
                clicker = layout.operator(switcher, text="", icon=icon)
                clicker.side, clicker.ik = side, state

            row = layout.row(align=True)
            clicker(row, side, False, 'TRIA_LEFT')
            row.prop(props, prop,text=side)
            clicker(row, side, True, 'TRIA_RIGHT')

        fk_ik_controls(box, 'right', '["IK_arms.R"]')
        fk_ik_controls(box, 'left', '["IK_arms.L"]')
        box = layout.box()
        box.label("Show/Hide:")

        row=box.row(align=True)
        row.scale_y = 2
        row.prop(ob.data, "layers", index=0, text="Head FK", toggle=True)

        col = box.column(align=True)
        row = col.row(align=True)
        row.label("  Face:")
        row = col.row(align=True)
        row.prop(ob.data, "layers", index=23, text="main", toggle=True)
        row = col.row(align=True)
        row.prop(ob.data, "layers", index=24, text="tweak", toggle=True)

        col = box.column(align=True)
        row = col.row(align=True)
        row.label("  Arms:")
        row = col.row(align=True)
        row.prop(ob.data, "layers", index=9, text="FK Right", toggle=True)
        row.prop(ob.data, "layers", index=6, text="FK Left", toggle=True)
        row = col.row(align=True)
        row.prop(ob.data, "layers", index=8, text="IK Right", toggle=True)
        row.prop(ob.data, "layers", index=5, text="IK Left", toggle=True)

        col = box.column(align=True)
        row = col.row(align=True)
        row.label("  Fingers:")
        row = col.row(align=True)
        row.prop(ob.data, "layers", index=4, text="Main", toggle=True)
        row = col.row(align=True)
        row.prop(ob.data, "layers", index=3, text="Tweak", toggle=True)

        row=box.row(align=True)
        row.scale_y = 2
        row.prop(ob.data, "layers", index=2, text="Torso FK", toggle=True)


        col = box.column(align=True)
        row = col.row(align=True)
        row.label("  Legs:")
        row = col.row(align=True)
        row.scale_y = 2
        row.prop(ob.data, "layers", index=15, text="IK Right", toggle=True)
        row.prop(ob.data, "layers", index=12, text="IK Left", toggle=True)


def register():
    bpy.utils.register_class(KognitoPanel)
    bpy.utils.register_class(FKIKSwitcher)


def unregister():
    bpy.utils.unregister_class(KognitoPanel )
    bpy.utils.unregister_class(FKIKSwitcher)


register()

