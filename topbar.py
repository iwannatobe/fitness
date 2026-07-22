from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp
from config import theme
from utils.instrument import StatusLamp
import sounds


class HamburgerButton(Button):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(44), dp(44)),
                         background_normal="", background_color=(0, 0, 0, 0), **kwargs)
        self._line_color = theme.TEXT_SECONDARY
        self.bind(pos=self._draw, size=self._draw)
        self.bind(on_press=self._on_down, on_release=self._on_up)

    def _on_down(self, *_):
        sounds.play_click()
        self._line_color = sounds.lighten(theme.TEXT_SECONDARY)
        self._draw()

    def _on_up(self, *_):
        self._line_color = theme.TEXT_SECONDARY
        self._draw()

    def _draw(self, *args):
        self.canvas.after.clear()
        x = self.x + self.width * 0.18
        w = self.width * 0.64
        h = dp(2)
        gap = dp(5)
        cy = self.y + self.height / 2
        with self.canvas.after:
            Color(*self._line_color)
            for i in range(3):
                Rectangle(pos=(x, cy + (i - 1) * (h + gap)), size=(w, h))


class BusMeter(Widget):
    """A restrained system-bus scan window for the persistent topbar status."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._phase = 0
        self._pulse = Clock.schedule_interval(self._advance, 0.32)
        with self.canvas:
            self._bg_color = Color(*theme.DISPLAY_GLASS)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            self._edge_color = Color(*theme.METAL_DARK)
            self._edge = Line(rectangle=(*self.pos, *self.size), width=dp(0.8))
            self._segments = []
            for _ in range(10):
                color = Color(*theme.VFD_BLUE_DIM)
                rect = Rectangle(pos=self.pos, size=(0, 0))
                self._segments.append((color, rect))
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _advance(self, _dt):
        self._phase = (self._phase + 1) % len(self._segments)
        self._draw()
        return True

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._edge.rectangle = (*self.pos, *self.size)
        gap = dp(2)
        segment_w = max(dp(2), (self.width - gap * 9 - dp(6)) / len(self._segments))
        segment_h = max(dp(2), self.height - dp(6))
        x = self.x + dp(3)
        y = self.y + dp(3)
        for index, (color, rect) in enumerate(self._segments):
            distance = (index - self._phase) % len(self._segments)
            if distance == 0:
                color.rgba = theme.VFD_CYAN
            elif distance in (1, len(self._segments) - 1):
                color.rgba = theme.VFD_CYAN_DIM
            elif index % 3 == 0:
                color.rgba = theme.VFD_BLUE_DIM
            else:
                color.rgba = theme.METAL_DARK
            rect.pos = (x, y)
            rect.size = (segment_w, segment_h)
            x += segment_w + gap

    def on_parent(self, _widget, parent):
        if parent is None:
            self.stop()

    def stop(self):
        if self._pulse is not None:
            self._pulse.cancel()
            self._pulse = None


class SystemBus(BoxLayout):
    """Persistent compact equipment-status group for the right side of TopBar."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", size_hint=(None, None),
                         size=(dp(158), dp(44)), padding=[dp(5), dp(3)],
                         spacing=dp(2), **kwargs)
        with self.canvas.before:
            Color(*theme.PANEL)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*theme.METAL)
            self._border = Line(rectangle=(*self.pos, *self.size), width=dp(0.8))
            Color(*theme.GLASS_HIGHLIGHT)
            self._highlight = Rectangle(pos=self.pos, size=(self.width, dp(1)))
        self.bind(pos=self._draw_frame, size=self._draw_frame)

        top = BoxLayout(size_hint_y=None, height=dp(10), spacing=dp(4))
        bus_label = Label(text="SYSTEM BUS", color=theme.METAL_LIGHT, font_size=dp(8),
                          halign="left", valign="middle")
        bus_label.bind(size=bus_label.setter("text_size"))
        top.add_widget(bus_label)
        mode_label = Label(text="V1.8", color=theme.VFD_BLUE, font_size=dp(8),
                           size_hint_x=None, width=dp(28), halign="right", valign="middle")
        mode_label.bind(size=mode_label.setter("text_size"))
        top.add_widget(mode_label)
        self.add_widget(top)

        rails = BoxLayout(size_hint_y=None, height=dp(11), spacing=dp(3))
        for label_text, color, breathe in (
                ("LNK", theme.VFD_BLUE, False),
                ("DAT", theme.VFD_CYAN, True),
                ("SYN", theme.LED_GREEN, False)):
            rail = BoxLayout(spacing=dp(2))
            label = Label(text=label_text, color=theme.TEXT_MUTED, font_size=dp(8),
                          size_hint_x=None, width=dp(18), halign="left", valign="middle")
            label.bind(size=label.setter("text_size"))
            rail.add_widget(label)
            rail.add_widget(StatusLamp(color=color, breathe=breathe,
                                       size=(dp(20), dp(3)),
                                       pos_hint={"center_y": 0.5}))
            rails.add_widget(rail)
        self.add_widget(rails)

        scan_row = BoxLayout(size_hint_y=None, height=dp(11), spacing=dp(4))
        scan_label = Label(text="BUS", color=theme.TEXT_MUTED, font_size=dp(8),
                           size_hint_x=None, width=dp(18), halign="left", valign="middle")
        scan_label.bind(size=scan_label.setter("text_size"))
        scan_row.add_widget(scan_label)
        scan_row.add_widget(BusMeter())
        self.add_widget(scan_row)

    def _draw_frame(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rectangle = (*self.pos, *self.size)
        self._highlight.pos = (self.x + dp(2), self.top - dp(2))
        self._highlight.size = (max(0, self.width - dp(4)), dp(1))

    def on_parent(self, _widget, parent):
        if parent is not None:
            return
        for widget in self.walk():
            if isinstance(widget, BusMeter):
                widget.stop()
            elif isinstance(widget, StatusLamp):
                widget.stop()


class TopBar(BoxLayout):
    def __init__(self, title_text, on_menu=None, **kwargs):
        super().__init__(size_hint_y=None, height=dp(54), padding=[dp(8), dp(4)], **kwargs)
        with self.canvas.before:
            Color(*theme.CHASSIS)
            self._rect = Rectangle(size=self.size, pos=self.pos)
            Color(*theme.METAL_DARK)
            self._metal = Rectangle(size=self.size, pos=self.pos)
            Color(*theme.HAIRLINE)
            self._line = Rectangle(pos=(self.x, self.y), size=(self.width, dp(1)))
        self.bind(size=self._update_rect, pos=self._update_rect)
        if on_menu:
            burger = HamburgerButton()
            burger.bind(on_release=lambda _: on_menu())
            self.add_widget(burger)
        else:
            self.add_widget(BoxLayout(size_hint=(None, None), size=(dp(44), dp(44))))
        english, _, chinese = title_text.partition("\n")
        title = Label(text=(f"[color=66ccff][size=11sp]{english}[/size][/color]\n"
                            f"[b]{chinese or english}[/b]"), markup=True,
                      font_size=dp(theme.FONT_BODY), color=theme.TEXT_PRIMARY,
                      halign="left", valign="middle")
        title.bind(size=title.setter("text_size"))
        self.add_widget(title)
        self.add_widget(SystemBus())

    def _update_rect(self, *args):
        self._rect.size = self.size
        self._rect.pos = self.pos
        self._metal.pos = (self.x + dp(2), self.y + dp(2))
        self._metal.size = (max(0, self.width - dp(4)), max(0, self.height - dp(4)))
        self._line.pos = (self.x, self.y)
        self._line.size = (self.width, dp(1))
