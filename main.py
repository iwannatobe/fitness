from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
import os

def _try_font(name, filename):
    paths = [
        os.path.join(os.path.dirname(__file__), "assets", "fonts", filename),
        os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", filename),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts", filename),
    ]
    for p in paths:
        if os.path.exists(p):
            LabelBase.register(name=name, fn_regular=p)
            return True
    return False

_try_font("Roboto", "roboto_regular.ttf")
_try_font("Symbols", "symbols.ttf")

class FitnessApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.08, 0.1, 1)
        import traceback, io, sys
        try:
            import theme
            import database as db
            from main_layout import MainLayout
            db.init_db()
            root = MainLayout()
            root.init_ui()
            return root
        except Exception:
            buf = io.StringIO()
            traceback.print_exc(file=buf)
            msg = buf.getvalue()
            for p in [os.path.join(os.path.dirname(__file__), "crash.log"),
                      "/data/local/tmp/fitness_crash.log",
                      "/sdcard/Android/data/org.fitness.fitnessapp/files/crash.log"]:
                try:
                    with open(p, "w") as f:
                        f.write(msg)
                except:
                    pass
            lbl = Label(text=msg, font_size=14, color=(1,0,0,1), halign="left", valign="top",
                        text_size=(Window.width-20, None), size_hint_y=None)
            lbl.bind(texture_size=lambda *_: setattr(lbl, "height", lbl.texture_size[1]))
            sv = ScrollView(size_hint=(1,1))
            sv.add_widget(lbl)
            return sv

if __name__ == "__main__":
    FitnessApp().run()
