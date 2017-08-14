import bpy

rig = bpy.data.objects['rig_def']
ctr = bpy.data.objects['rig_ctrl']

def face_link():
    deform_face_layer = 16
    for bone in rig.pose.bones:
        dbone = rig.data.bones[bone.name]
        if dbone.layers[16]:
            print(bone.name)
            ctr_bone = bone.name.replace('GEO_','')
            cons = bone.constraints.new('COPY_TRANSFORMS')
            cons.target = ctr
            cons.subtarget = ctr_bone

if __name__ == "__main__": 
    face_link()