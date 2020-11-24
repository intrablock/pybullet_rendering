# zy1112: read objfile to get texture

import argparse
import numpy as np
import pybullet as pb
import pybullet_data

from pybullet_utils.bullet_client import BulletClient
import sys
sys.path.append('../../')
from pybullet_rendering import RenderingPlugin, BaseRenderer, ShapeType
from pybullet_rendering.render.utils import shape_filename

import vtk
import time


def Quat2WXYZ(_quat):
    # input _quat: [w,x,y,z]
    # output EulerAngle: [W,X,Y,Z]
    # Rotate in degrees about an arbitrary axis specified by the last three arguments.
    quat = vtk.vtkQuaternionf(*_quat)
    r = [0,0,0]
    a = quat.GetRotationAngleAndAxis(r)
    # print(a, r)
    a = vtk.vtkMath.DegreesFromRadians(a)
    return [a, *r]

def GetTexture(file_name):
    r = vtk.vtkImageReader2Factory.CreateImageReader2(file_name)
    # r = vtk.vtkPNGReader()
    r.SetFileName(file_name)
    r.Update()

    t = vtk.vtkTexture()
    t.SetInputConnection(r.GetOutputPort())
    # t.SetBlendingMode(vtk.vtkTexture.VTK_TEXTURE_BLENDING_MODE_NONE)

    # dims = r.GetOutput().GetDimensions()
    # print(dims)
    return t

from objloader import OBJ
def readOBJ(file_name):
    obj = OBJ(file_name)
    # print(obj.mtl)
    for name, mtl in obj.mtl.items():
        if 'texture_Kd' in mtl:
            return mtl['texture_Kd']
    return ''


class VtkRenderer(BaseRenderer):

    def __init__(self):
        BaseRenderer.__init__(self)  # <- important

        client = BulletClient(pb.DIRECT)
        client.setAdditionalSearchPath(pybullet_data.getDataPath())
        self.client = client

        # bind external renderer
        plugin = RenderingPlugin(client, self)

        # setup scene
        self.nodes = {}

        self.render = vtk.vtkRenderer()
        self.renWin = vtk.vtkRenderWindow()
        self.renWin.AddRenderer(self.render)
        colors = vtk.vtkNamedColors()
        self.render.SetBackground(colors.GetColor3d("cobalt_green"))
        
        self.setupScene(client)
        # self.setupLights()
        self.time = 0

        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(self.renWin)

        # Enable user interface interactor
        iren.Initialize()
        iren.AddObserver('TimerEvent', self.stepSimulationTask)
        iren.CreateRepeatingTimer(50)
        self.iren = iren

        camera = self.render.GetActiveCamera()
        camera.SetPosition([0,-3,3])
        # camera.SetFocalPoint(v)
        # camera.SetViewUp(v)
        camera.SetViewAngle(40)
        # camera.SetClippingRange(v)
        # self.setupLights()

    def setupLights(self):
        # Set up the lighting.
        #
        # light = vtk.vtkLight()
        # light.SetFocalPoint(1.875, 0.6125, 0)
        # light.SetPosition(0.875, 1.6125, 1)
        # self.render.AddLight(light)
        self.render.UseImageBasedLightingOn()
        

    def setupScene(self, client):
        """Init pybullet scene"""
        table = client.loadURDF("table/table.urdf")
        client.resetBasePositionAndOrientation(
            table, [0.4, 0.04, -0.7], [0, 0, 0, 1])

        human = client.loadURDF("humanoid/humanoid.urdf", globalScaling=.25, 
                                basePosition=(0, -.6, .15), baseOrientation=(1,0,0,1))
        kuka = client.loadSDF("kuka_iiwa/kuka_with_gripper2.sdf")[0]
        client.resetBasePositionAndOrientation(
            kuka, [0.0, 0.0, 0.0], [0, 0, 0, 1])

        Q = [
            0.006418, 0.413184, -0.011401, -1.589317, 0.005379, 1.137684, -0.006539, 0.000048,
            -0.299912, 0.000000, -0.000043, 0.299960, 0.000000, -0.000200
        ]
        for i, q in enumerate(Q):
            client.setJointMotorControl2(bodyIndex=kuka,
                                        jointIndex=i,
                                        controlMode=pb.POSITION_CONTROL,
                                        targetPosition=q,
                                        targetVelocity=0,
                                        force=100,
                                        positionGain=0.01,
                                        velocityGain=1)


    def stepSimulationTask(self, obj, event):
        """Update light position
        """
        if time.time() - self.time > 1 / 30.:
            self.client.stepSimulation()
            # this call trigger updateScene (if necessary) and draw methods
            self.client.getCameraImage(1, 1)
            self.time = time.time()
            # print(self.time)
            self.renWin.Render()


    def update_scene(self, scene_graph, materials_only):
        """Update a scene using scene_graph description

        Arguments:
            scene_graph {SceneGraph} -- scene description
            materials_only {bool} -- update only shape materials
        """
        for k, v in scene_graph.nodes.items():
            # print(k,len(v.shapes))

            mtx = vtk.vtkMatrix4x4()
            self.nodes[k] = mtx

            for j, pb_shape in enumerate(v.shapes):
                filename = shape_filename(pb_shape)
                if not filename:
                    continue
                # print(k, j, filename)

                mapper = vtk.vtkPolyDataMapper()
                if filename.endswith('.stl'):
                    reader = vtk.vtkSTLReader()
                    reader.SetFileName(filename)
                    mapper.SetInputConnection(reader.GetOutputPort())
                elif filename.endswith('.obj'):
                    reader = vtk.vtkOBJReader()
                    reader.SetFileName(filename)
                    mapper.SetInputConnection(reader.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                pose = pb_shape.pose
                # print(pose.origin, pose.scale)
                actor.SetPosition(*pose.origin)

                quat = Quat2WXYZ(pose.quat)
                actor.RotateWXYZ(*quat)

                actor.SetScale(*pose.scale)
                actor.SetUserMatrix(mtx)

                material = pb_shape.material
                # print(material.diffuse_texture)
                actor.GetProperty().SetAmbientColor(material.specular_color)
                actor.GetProperty().SetDiffuseColor(material.diffuse_color[:3])
                actor.GetProperty().SetSpecularColor(material.specular_color)
                # actor.GetProperty().SetOpacity(1)

                # texture_id = material.diffuse_texture
                # # set texture
                # if texture_id > -1:
                #     tex = scene_graph.texture(texture_id)
                #     t = GetTexture(tex.filename)
                
                if filename.endswith('.obj'):
                    tkd = readOBJ(filename)
                    if tkd:
                        t = GetTexture(tkd)
                        actor.SetTexture(t)


                self.render.AddActor(actor)


    def render_frame(self, scene_state, scene_view, frame):
        """Render a scene at scene_state with a scene_view settings

        Arguments:
            scene_state {SceneState} --  scene state, e.g. transformations of all objects
            scene_view {SceneView} -- view settings, e.g. camera, light, viewport parameters
            frame {FrameData} -- output image buffer, ignore
        """

        for k, mtx in self.nodes.items():
            pose = scene_state.pose(k)
            # print(pose.origin)
            mtx.DeepCopy(pose.matrix)
            mtx.Transpose()

        # self.setBackgroundColor(*scene_view.bg_color)
        return False

ren = VtkRenderer()
ren.iren.Start()