import bpy

context = bpy.context 
ops = bpy.ops
ob = context.active_object

def find_or_add_constraint(bone, constraint):
    con = [con for con in bone.constraints if con.type in constraint]
    if not con:
        con = bone.constraints.new(type=constraint)
    else: con = con[0]
    return con

if ob.type == 'ARMATURE' and ob.name == 'rig_ctrl':
    for bone in ob.data.bones:
        if bone.name.startswith('palm') or bone.name.startswith('thumb') or bone.name.startswith('f_'):
            bone.use_inherit_scale = True
        else:
            bone.use_inherit_scale = False
        bone.use_deform = False

    target = bpy.data.objects["rig_ctrl"]
    
    for bone in context.selected_pose_bones:

        # arm IK constraints    
        if bone.name.startswith('forearm.'):
            ik = find_or_add_constraint(bone, 'IK')
            ik.target = target
            ik_bone = bone.name.replace('.', '_ik.')
            pole_bone = bone.name.replace('.', '_ik_pole.')
            ik.subtarget = ik_bone
            ik.pole_target = target
            ik.pole_subtarget = pole_bone
            ik.pole_angle = -1.5708
            ik.chain_count = 2
        if bone.name.startswith('forearm_ik'):
            child_of = find_or_add_constraint(bone, 'CHILD_OF')
            child_of.target = target
            child_of.subtarget = bone.name.replace('forearm_ik', 'shoulder')
            context_copy = context.copy()
            context_copy["constraint"] = child_of
            context.active_object.data.bones.active
            ops.constraint.childof_set_inverse(context_copy, constraint="Child Of", owner='BONE')
            ops.object.editmode_toggle()
            ops.object.posemode_toggle() #HACK!
                
#        # hand constraints
#        if bone.name.startswith('hand.'):
#            copy_rot = find_or_add_constraint(bone, 'COPY_ROTATION')
#            copy_rot.target = target
#            copy_rot.subtarget = bone.name.replace('hand.', 'forearm_ik.')
#            copy_rot.target_space = copy_rot.owner_space = 'LOCAL'
        
        # leg IK constraints    
        if bone.name.startswith('shin'):
            ik = find_or_add_constraint(bone, 'IK')
            ik.target = target
            ik_bone = bone.name.replace('.', '_ik.')
            pole_bone = bone.name.replace('.', '_ik_pole.')

            ik.subtarget = ik_bone
            ik.pole_target = target
            ik.pole_subtarget = pole_bone
            ik.pole_angle = -1.5708
            ik.chain_count = 2
            
            loc_rot = find_or_add_constraint(bone, 'LIMIT_ROTATION')
            loc_rot.use_limit_y = True
            loc_rot.use_limit_z = True
            loc_rot.owner_space = 'POSE'

        # foot constraints
        if bone.name.startswith('foot.') or bone.name.startswith('toe.'):
            ik = find_or_add_constraint(bone, 'IK')
            ik.target = target
            ik_bone = bone.name.replace('.', '_ik.')
            ik.subtarget = ik_bone
            ik.chain_count = 1

if ob.type == 'ARMATURE' and ob.name == 'rig_def':
    for bone in ob.data.bones:
        if bone.name.startswith('palm') or bone.name.startswith('thumb') or bone.name.startswith('f_'):
            bone.use_inherit_scale = True
        else:
            bone.use_inherit_scale = False
    for bone in context.selected_pose_bones:
        
        target = bpy.data.objects["rig_ctrl"]
        
        # hip  constraints
        if bone.name.startswith('hips'):
            copy_loc = find_or_add_constraint(bone, 'COPY_LOCATION')
            copy_loc.target = target
            copy_loc.subtarget = bone.name
            copy_loc.target_space = copy_loc.owner_space = 'LOCAL'
            
            copy_rot = find_or_add_constraint(bone, 'COPY_ROTATION')
            copy_rot.target = target
            copy_rot.subtarget = bone.name
            copy_rot.target_space = copy_rot.owner_space = 'POSE'
        # leg constraints
        if bone.name.startswith('thigh'):
            copy_loc = find_or_add_constraint(bone, 'COPY_LOCATION')
            copy_loc.target = target
            copy_loc.subtarget = bone.name
            copy_loc.target_space = copy_loc.owner_space = 'POSE'
            
            copy_rot = find_or_add_constraint(bone, 'COPY_ROTATION')
            copy_rot.target = target
            copy_rot.subtarget = bone.name
            copy_rot.target_space = copy_rot.owner_space = 'POSE'

        # spine constraints
        if bone.name.startswith('spine') or bone.name.startswith('chest'):
            copy_rot = find_or_add_constraint(bone, 'COPY_ROTATION')
            copy_rot.target = target
            copy_rot.subtarget = bone.name
            copy_rot.target_space = copy_rot.owner_space = 'LOCAL'


        # shoulder constraints
        if bone.name.startswith('upper_arm'):
            copy_rot = find_or_add_constraint(bone, 'COPY_ROTATION')
            copy_rot.target = target
            copy_rot.subtarget = bone.name
            copy_rot.target_space = copy_rot.owner_space = 'LOCAL'
            
        
        # hand constraints
        if bone.name.startswith('palm') or bone.name.startswith('thumb.01'):
            copy_loc = find_or_add_constraint(bone, 'COPY_LOCATION')
            copy_loc.target = target
            copy_loc.subtarget = bone.name
            
        
        # head constrains
        if bone.name == 'head':
            copy_scale = find_or_add_constraint(bone, 'COPY_SCALE')
            copy_scale.target = target
            copy_scale.subtarget = bone.name
            copy_scale.target_space = copy_scale.owner_space = 'LOCAL'
            
            copy_rot = find_or_add_constraint(bone, 'COPY_ROTATION')
            copy_rot.target = target
            copy_rot.subtarget = bone.name
            copy_rot.target_space = copy_rot.owner_space = 'LOCAL'
        if bone.name == 'neck':
            copy_rot = find_or_add_constraint(bone, 'COPY_ROTATION')
            copy_rot.target = target
            copy_rot.subtarget = bone.name
            copy_rot.target_space = copy_rot.owner_space = 'LOCAL'


        # all bones get stretch to constraints
        stretch = find_or_add_constraint(bone, 'STRETCH_TO')
        stretch.target = target
        stretch.subtarget = bone.name
        stretch.head_tail = 1
        stretch.rest_length = bone.length
        stretch.volume = 'NO_VOLUME'