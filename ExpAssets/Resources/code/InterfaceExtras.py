__author__ = "Austin Hurst"

import sdl2
from sdl2.ext import cursor_hidden, show_cursor, hide_cursor

from klibs import STROKE_INNER
from klibs import P
from klibs.KLBoundary import BoundaryInspector, RectangleBoundary, CircleBoundary
from klibs.KLGraphics import fill, blit, flip, clear, rgb_to_rgba
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics.KLNumpySurface import NumpySurface as NpS
from klibs.KLCommunication import message
from klibs.KLEventQueue import flush, pump
from klibs.KLUserInterface import get_clicks, mouse_clicked, ui_request, key_pressed
from klibs.KLUtilities import mouse_pos
from klibs.KLUtilities import line_segment_len as lsl

from utils import draw_borders

MED_GREY = (128, 128, 128, 255)
LIGHT_GREY = (192, 192, 192, 255)
TRANSLUCENT_GREY = (192, 192, 192, 64)
TRANSLUCENT_BLUE = (0, 0, 128, 128)



class Aesthetics(object):
    """The aesthetic attributes to use for drawing an interface item.

    Args:
        color (tuple, optional): The RGBA color to use for the lines of the UI
            element. If not specified, `P.default_color` will be used.
        fill (tuple, optional): The RGBA color to use for the fill of the UI element.
            If not specified, no fill color will be used.
        thickness (int, optional): The thickness (in pixels) for the lines of the UI
            element. The default varies based on the element the aesthetic is used with.
        hover (tuple, optional): The translucent RGBA color to use for hover elements
            in the UI element. Defaults to translucent light grey.
        fontstyle (str, optional): The font style to use for rendering text within the
            UI element. Defaults to the 'default' font style.
        
    """
    def __init__(self, color=None, fill=None, thickness=None, hover=None, fontstyle=None):
        # Handle colours and thicknesses
        self._color = rgb_to_rgba(color) if color else P.default_color
        self._fill = rgb_to_rgba(fill) if fill else None
        self._thickness = int(thickness) if thickness else None
        self._hover = rgb_to_rgba(color) if hover else TRANSLUCENT_GREY
        self._fontstyle = fontstyle if fontstyle else 'default'

    @property
    def color(self):
        return self._color

    @property
    def fill(self):
        return self._fill

    @property
    def thickness(self):
        return self._thickness

    @property
    def hover(self):
        return self._hover

    @property
    def fontstyle(self):
        return self._fontstyle



class Button(object):
    
    def __init__(self, msg, width, height=None, aes=None, registration=5, location=None):

        # Initialize UI aesthetics
        if not aes:
            aes = Aesthetics(thickness=0)
        if aes.thickness is None:
            aes._thickness = 0
        
        self.width = width
        self.height = height if height else width
        self.msg = message(msg, aes.fontstyle)

        self.button = None
        if aes.thickness or aes.fill:
            outline = [aes.thickness, aes.color, STROKE_INNER]
            self.button = kld.Rectangle(self.width, self.height, stroke=outline, fill=aes.fill)
        else:
            self.button = kld.Rectangle(self.width, self.height)
        self.hover = kld.Rectangle(self.width, self.height, fill=aes.hover)
        
        self._registration = registration
        self._location = location if location else P.screen_c
        self._init_bounds()
    
    
    def _init_bounds(self):
        if self.registration in [7, 4, 1]:
            self.x_offset = self.width // 2
        elif self.registration in [9, 6, 3]:
            self.x_offset = -self.width // 2
        else:
            self.x_offset = 0   
        if self.registration in [7, 8, 9]:
            self.y_offset = self.height // 2
        elif self.registration in [1, 2, 3]:
            self.y_offset = -self.height // 2
        else:
            self.y_offset = 0       

        self.midpoint = (self.location[0]+self.x_offset, self.location[1]+self.y_offset)
        self.x1 = self.midpoint[0] - self.width // 2
        self.y1 = self.midpoint[1] - self.height // 2
        self.x2 = self.midpoint[0] + self.width // 2
        self.y2 = self.midpoint[1] + self.height // 2
        self.bounds = RectangleBoundary("button", (self.x1, self.y1), (self.x2, self.y2))
        
        
    def draw(self):
        if self.button:
            blit(self.button, 5, self.midpoint)
        blit(self.msg, 5, self.midpoint)
        mp = mouse_pos()
        if self.bounds.within(mp):
            blit(self.hover, 5, self.midpoint)
        
    def listen(self, queue):
        return mouse_clicked(within=self.bounds, queue=queue)
                
    @property
    def location(self):
        return self._location
        
    @location.setter
    def location(self, loc):
        self._location = loc
        self._init_bounds()
        
    @property
    def registration(self):
        return self._registration
        
    @registration.setter
    def registration(self, reg):
        self._registration = reg
        self._init_bounds()



class LikertType(BoundaryInspector):
    """A Likert-type rating scale for collecting numeric responses.

    Args:
        first (int): The lowest digit on the scale.
        last (int): The highest digit on the scale.
        width (int): The full width of the scale.
        height (int): The height of each circle on the scale.

    """
    def __init__(
        self, first, last, width, height, aes=None, registration=None, location=None
    ):

        BoundaryInspector.__init__(self)

        self.range = range(first, last+1, 1)
        self.count = len(self.range)
        self.response = None
        
        self.height = height
        self.width = width
        self.circle_size = self.height
        self.gap = (width - self.circle_size * self.count) / (self.count - 1)
        
        self._location = location if location else P.screen_c
        self._registration = registration if registration else 5
        self._init_bounds()

        # Initialize UI aesthetics
        if not aes:
            aes = Aesthetics(thickness=0)
        if aes.thickness is None:
            aes._thickness = 0

        numlist = []
        for num in self.range:
            num_txt = message("{0}".format(num), aes.fontstyle, blit_txt=False)
            numlist.append((num, num_txt))
        self.numbers = dict(numlist)

        self.circle = None
        if aes.fill or aes.thickness > 0:
            outline = [aes.thickness, aes.color, STROKE_INNER]
            self.circle = kld.Ellipse(self.circle_size-4, stroke=outline, fill=aes.fill)
        self.selected = kld.Ellipse(self.circle_size-4, fill=aes.hover)
        self.mouseover = self.selected

    def _init_bounds(self):
        if self.registration in [7, 4, 1]:
            self.x_offset = self.width // 2
        elif self.registration in [9, 6, 3]:
            self.x_offset = -self.width // 2
        else:
            self.x_offset = 0   
        if self.registration in [7, 8, 9]:
            self.y_offset = self.height // 2
        elif self.registration in [1, 2, 3]:
            self.y_offset = -self.height // 2
        else:
            self.y_offset = 0       

        self.midpoint = (
            self.location[0] + self.x_offset, self.location[1] + self.y_offset
        )
        self.x1 = self.midpoint[0] - self.width // 2
        self.y1 = self.midpoint[1] - self.height // 2
        self.x2 = self.midpoint[0] + self.width // 2
        self.y2 = self.midpoint[1] + self.height // 2

        for num in self.range:
            pos = self._num_to_pos(num)
            bounds = CircleBoundary(str(num), pos, (self.circle_size * 0.6))
            self.add_boundary(bounds)
    
    def _num_to_pos(self, num):
        n = self.range.index(num)
        x_pos = self.x1 + int(self.circle_size * (n + 0.5)) + int(self.gap * n)
        y_pos = self.y1 + int(self.circle_size * 0.5)
        return (x_pos, y_pos)

    def render(self):
        # Render all items in scale
        for num in self.range:
            pos = self._num_to_pos(num)
            if self.circle:
                blit(self.circle, location=pos, registration=5)
            blit(self.numbers[num], location=pos, registration=5)
        # If a response has been made, show it
        if self.response != None:
            pos = self._num_to_pos(self.response)
            blit(self.selected, location=pos, registration=5)
        # If hovering over an item, highlight it
        num = self.which_boundary(mouse_pos())
        if num != None:
            blit(self.mouseover, 5, self._num_to_pos(int(num)))

    def listen(self, queue):
        for e in queue:
            if e.type == sdl2.SDL_MOUSEBUTTONDOWN:
                pos = (e.button.x * P.screen_scale_x, e.button.y * P.screen_scale_y)
                num = self.which_boundary(pos)
                if num != None:
                    self.response = int(num)
                    return (self.response, e.button.timestamp)
        return None
    
    @property
    def location(self):
        return self._location
        
    @property
    def registration(self):
        return self._registration



class LikertPrompt(object):
    """Creates a Likert-type prompt with a numeric scale and question.

    Args:
        first (int): The first number in the Likert scale.
        last (int): The last number in the Likert scale.
        question: A message containing the text to present on screen with the
            scale.
        width (int): The width of the full Likert scale in pixels (e.g.
            int(P.screen_x * 0.7)).
        origin (tuple): The coordinates at which to place the top-middle
            of the probe (e.g. (P.screen_c[0], int(P.screen_y * 0.3))).

    """
    def __init__(self, first, last, question, width, origin, aes=None):

        self.q = question
        self.width = width

        height = width / (last - first + 2)
        loc = (origin[0], origin[1] + height // 2)
        self.scale = LikertType(
            first, last, width, height, aes, registration=8, location=origin
        )
        self.q_loc = (origin[0], origin[1] - height // 2)

    def collect(self):
        """Displays the probe and waits for a response.
        """
        cursor_was_hidden = cursor_hidden()
        show_cursor()
        
        fill()
        draw_borders(P.border_size)
        blit(self.q, location=self.q_loc, registration=2)
        self.scale.render()
        flip()
        onset = sdl2.SDL_GetTicks()

        resp = None
        while not resp:
            q = pump()
            resp = self.scale.listen(q)
            ui_request(queue=q)
            fill()
            draw_borders(P.border_size)
            blit(self.q, location=self.q_loc, registration=2)
            self.scale.render()
            flip()

        response, timestamp = resp
        self.scale.response = None # reset for next time
        if cursor_was_hidden:
            hide_cursor()
        
        return (response, (timestamp - onset) / 1000)
