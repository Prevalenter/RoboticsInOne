"""Create a window with an attached scene that is rendered in real time."""

try:
    from .wx import Window
except ImportError:
    raise ImportError("No supported gui library was found. Install wxPython.")


from ..renderables import Renderable, Lines
from ..behaviours import Behaviour, SceneInit
from ..behaviours.mouse import MouseRotate, MouseZoom, MousePan
from ..behaviours.keyboard import CameraReport, SortTriangles


def simple_window(init, size=(512, 512), info=[]):
    """Return a window with the expected behaviours added.

    Arguments
    ---------
        init: callable that sets up the scene
        size: (w, h) the size of the window

    Returns
    -------
        Window instance
    """
    w = Window(size, info=info)
    w.add_behaviours([SceneInit(init), MouseRotate(), MouseZoom(),
                      MousePan(), CameraReport(), SortTriangles()])
    return w


def show(meshes, axes, size=(512, 580), background=(0.7, 0.7, 0.7, 1), title="Scene",
         camera_position=(-2, -2, -2), camera_target=(0, 0, 0),
         up_vector=(0, 0, 1), light=None, behaviours=[], info=[]):
    """Creates a simple window that displays the renderables.

    Arguments
    ---------
        renderables: list[Renderable] the renderables to be displayed in the
                     scene
        size: (w, h) the size of the window
        background: (r, g, b, a) the rgba tuple for the background
        title: str the title of the window
        camera_position: (x, y, z) the position of the camera
        camera_target: (x, y, z) the point that the camera looks at
        up_vector: (x, y, z) defines the floor and sky
        light: (x, y, z) defines the position of the light source
    """
    

    def init(scene):
        # scene.add(Lines.axes(size=0.06, width=0.006, origin=[0, 0, 0.245]))
        # scene.add(Lines.axes(size=0.06, width=0.006, origin=[0, 0, 0.245+0.195]))
        for r in axes+meshes:
            scene.add(r)
        scene.background = background
        scene.camera_position = camera_position
        scene.camera_target = camera_target
        scene.up_vector = up_vector
        if light is not None:
            scene.light = light

    w = simple_window(init, size=size, info=info)
    w.add_behaviours(behaviours)
    w.show(title)
