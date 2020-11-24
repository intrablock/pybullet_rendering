# pybullet_rendering
External rendering for [PyBullet](https://github.com/bulletphysics/bullet3/) simulator.

Tested on Windows10. Add VTK renderer.

See the original [README.md](oldREADME.md)

# dependency
```
pip install pybullet
pip install QPanda3D
pip install vtk
```

# build pybullet_rendering
```
git submodule update
pip install cmake
copy bullet3/examples/CommonInterfaces(Importers, SharedMemory, TinyRenderer) to ./src
copy bullet3/src/LinearMath to ./src
python setup.py build --bullet_dir './'
copy build/lib.win-amd64-3.7/pybullet_rendering/bindings.cp37-win_amd64.pyd to ./pybullet_rendering
```

# Run examples
```
python panda3d_gui.py
python performance.py
python qpanda3d_gui.py
python vtk_gui.py
```
Note: As texture is not supported by RenderingPlugin, read on your own.
objloader.py is borrowed from https://github.com/yarolig/OBJFileLoader