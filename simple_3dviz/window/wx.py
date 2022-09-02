import moderngl
import numpy as np
import wx
import wx.glcanvas
from wx import html, stc
import os.path as osp

from ..behaviours import Behaviour
from ..scenes import Scene
from .base import BaseWindow
from ..renderables import Mesh, Lines

dir_abs_path = osp.dirname(osp.abspath(__file__))

class Window(BaseWindow):
    _FRAME_STYLE = wx.DEFAULT_FRAME_STYLE & ~(
        wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
    )


    class _Frame(wx.Frame):
        """A simple frame for our wxWidgets app."""
        def __init__(self, window, size, title):
            super(Window._Frame, self).__init__(
                None,
                style=Window._FRAME_STYLE
            )
            self._window = window
            self.SetTitle(title)
            self.SetClientSize(size)
            self.Center()
            self.view = Window._Canvas(self._window, self)
            self.Bind(wx.EVT_CLOSE, self._on_close)

            icon = wx.Icon()
            icon.CopyFromBitmap(wx.Bitmap(osp.join(dir_abs_path, "../../icons/ico.bmp"), wx.BITMAP_TYPE_ANY))
            # icon.LoadFile("icons/sm.ico", wx.BITMAP_TYPE_ANY)
            self.SetIcon(icon)
            self.SetBackgroundColour( wx.Colour( 255, 255, 255 ) )

            bSizer1 = wx.BoxSizer( wx.VERTICAL )

            
            bSizer1.Add( self.view, 5, wx.EXPAND |wx.ALL, 0 )

            bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

            self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Color", wx.DefaultPosition, wx.DefaultSize, 0 )
            self.m_staticText1.Wrap( -1 )

            bSizer2.Add( self.m_staticText1, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

            self.m_colourPicker2 = wx.ColourPickerCtrl( self, wx.ID_ANY, '#708090', wx.DefaultPosition, wx.DefaultSize, wx.CLRP_DEFAULT_STYLE )
            self.m_colourPicker2.SetColour('#708090')
            bSizer2.Add( self.m_colourPicker2, 0, wx.ALL, 5 )

            self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"Alpha", wx.DefaultPosition, wx.DefaultSize, 0 )
            self.m_staticText2.Wrap( -1 )

            bSizer2.Add( self.m_staticText2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

            self.m_slider2 = wx.Slider( self, wx.ID_ANY, 20, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
            bSizer2.Add( self.m_slider2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

            self.m_checkBox1 = wx.CheckBox( self, wx.ID_ANY, u"CoM", wx.DefaultPosition, wx.DefaultSize, 0 )
            self.m_checkBox1.SetValue(True)
            bSizer2.Add( self.m_checkBox1, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


            bSizer1.Add( bSizer2, 0, wx.EXPAND, 0 )


            self.SetSizer( bSizer1 )
            self.Layout()

            self.Centre( wx.BOTH )

            self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnColor, self.m_colourPicker2)
            self.Bind(wx.EVT_SCROLL, self.OnSlider, self.m_slider2)
            self.Bind(wx.EVT_CHECKBOX, self.OnCheker, self.m_checkBox1)


        def OnColor(self, e):
            color = self.m_colourPicker2.GetColour()[:3]
            color = [ c/255.0 for c in color]
            for render in self._window._scene._renderables:
                if isinstance(render, Mesh):
                    render.colors = color + [self.m_slider2.GetValue()/100.0]
            
            self.view._on_paint(None)

        def OnSlider(self, e):
            color = self.m_colourPicker2.GetColour()[:3]
            print(color)
            color = [ c/255.0 for c in color]
            print(color)
            for render in self._window._scene._renderables:
                if isinstance(render, Mesh):
                    render.colors = color + [self.m_slider2.GetValue()/100.0]
            self.view._on_paint(None)

        def OnCheker(self, e):
            return


        def _on_close(self, event):
            # If close was called before then close
            if self._window._closing:
                self.view._on_close(event)
                self.Destroy()

            # otherwise just set the window to closing
            self._window._closing = True

    class _Canvas(wx.glcanvas.GLCanvas):
        def __init__(self, window, parent):
            super(Window._Canvas, self).__init__(
                parent,
                attribList=[
                    wx.glcanvas.WX_GL_CORE_PROFILE,
                    wx.glcanvas.WX_GL_RGBA,
                    wx.glcanvas.WX_GL_DOUBLEBUFFER,
                    wx.glcanvas.WX_GL_DEPTH_SIZE,
                    24
                ]
            )
            self._window = window
            self._window._get_frame = self._get_frame
            self._context = wx.glcanvas.GLContext(self)
            self._mgl_context = None
            self._ticker = wx.Timer(self)

            self.Bind(wx.EVT_PAINT, self._on_paint)
            self.Bind(wx.EVT_TIMER, self._on_tick, self._ticker)
            self.Bind(wx.EVT_MOUSE_EVENTS, self._on_mouse)
            self.Bind(wx.EVT_KEY_DOWN, self._on_keyboard)
            self.Bind(wx.EVT_KEY_UP, self._on_keyboard)

        def _get_frame(self):
            framebuffer = self._mgl_context.detect_framebuffer()
            return np.frombuffer(
                framebuffer.read(components=4),
                dtype=np.uint8
            ).reshape(*(framebuffer.size + (4,)))[::-1]

        def _on_close(self, event):
            self._ticker.Stop()
            self.Unbind(wx.EVT_TIMER)

        def _on_paint(self, event):
            self.SetCurrent(self._context)
            if self._window._scene is None:
                self._mgl_context = moderngl.create_context()
                self._mgl_context.enable(moderngl.BLEND)
                self._mgl_context.blend_func = (
                    # moderngl.SRC_ALPHA,
                    # moderngl.ONE_MINUS_SRC_ALPHA
                    moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA,
                    # moderngl.FUNC_ADD, moderngl.FUNC_ADD
                    # moderngl.ONE, moderngl.ONE
                )
                self._window._scene = Scene(
                    size=(self.Size.width, self.Size.height),
                    background=(0,)*4,
                    ctx=self._mgl_context
                )
                self._ticker.Start(16)

            self._window._draw()
            self.SwapBuffers()

        def _on_tick(self, event):
            if self._window._behave(event):
                self.Refresh()
            if self._window._closing:
                self.GetParent()._on_close(None)
            self._window._mouse.wheel_rotation = 0
            self._window._keyboard.keys_up.clear()

        def _on_mouse(self, event):
            state = wx.GetMouseState()
            self._window._mouse.location = (state.GetX(), state.GetY())
            self._window._mouse.left_pressed = state.LeftIsDown()
            self._window._mouse.middle_pressed = state.MiddleIsDown()
            if abs(event.GetWheelRotation()) > 0:
                self._window._mouse.wheel_rotation += (
                    event.GetWheelRotation()/event.GetWheelDelta()
                )

        def _on_keyboard(self, event):
            down = event.GetEventType() == wx.EVT_KEY_DOWN.typeId
            key = chr(event.GetUnicodeKey())
            alt = event.AltDown() == down
            ctrl = event.ControlDown() == down
            cmd = event.CmdDown() == down
            meta = event.MetaDown() == down
            keys = set(
                [key] if key != "\00" else [] +
                (["<alt>"] if alt else []) +
                (["<ctrl>"] if ctrl else []) +
                (["<cmd>"] if cmd else []) +
                (["<meta>"] if meta else [])
            )

            if down:
                self._window._keyboard.keys_down.update(keys)
            else:
                self._window._keyboard.keys_up.update(
                    keys | self._window._keyboard.keys_down
                )
                self._window._keyboard.keys_down.difference_update(keys)

    def __init__(self, size=(512, 512)):
        super(Window, self).__init__(size)
        self._scene = None
        self._mouse = Behaviour.Mouse(None, None, None, None)
        self._keyboard = Behaviour.Keyboard([], [])
        self._closing = False

    def _behave(self, event):
        # Make the behaviour parameters
        params = Behaviour.Params(
            self,
            self._scene,
            self._get_frame,
            self._mouse,
            self._keyboard,
            self._closing
        )

        # Run the behaviours
        remove = []
        for i, b in enumerate(self._behaviours):
            b.behave(params)
            if params.done:
                remove.append(i)
                params.done = False
            if params.stop_propagation:
                break

        # Remove the ones that asked to be removed
        for i in reversed(remove):
            self._behaviours.pop(i)

        # If we are closing, remove all behaviours
        if self._closing:
            self._behaviours.clear()

        # Return whether we should paint again
        return params.refresh

    def _draw(self):
        self._scene.render()

    def show(self, title="Scene"):
        # app = wx.App(False)
        frame = self._Frame(self, self.size, title)
        frame.Show()
        # app.MainLoop()
