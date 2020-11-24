from os.path import dirname, join, relpath
import pybullet_rendering as pr
import pybullet_data

__all__ = ['shape_filename']


def shape_filename(shape):
    if shape.type == pr.ShapeType.Mesh:
        return shape.mesh.filename

    packagedir = dirname(pr.__path__[0])
    if shape.type == pr.ShapeType.Cube:
        return join(packagedir, 'share', 'primitives', 'cube.stl')
    elif shape.type == pr.ShapeType.Sphere:
        return join(packagedir, 'share', 'primitives', 'sphere.stl')
    elif shape.type == pr.ShapeType.Cylinder:
        return join(packagedir, 'share', 'primitives', 'cylinder.stl')
    elif shape.type == pr.ShapeType.Capsule:
        return join(packagedir, 'share', 'primitives', 'cylinder.stl')
    return ''


def shape_filename_relpath(shape):
    if shape.type == pr.ShapeType.Mesh:
        # path = shape.mesh.filename
        # pos = path.find('pybullet_data')
        # if pos > 0:
        #     path = path[pos+14:]
        path = relpath(shape.mesh.filename, pybullet_data.getDataPath())
        # print(path)
        return path
    return shape_filename(shape)

