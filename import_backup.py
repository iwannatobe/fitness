"""Import historical data from a JSON backup via a file chooser."""

import os
from datetime import date

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView

from config import theme
import database as db
from utils.platform import get_db_path
import sounds

_BACKUP_DIR = os.path.dirname(get_db_path())


class ImportBackupDialog(ModalView):
    """Modal chooser: pick a fitness_backup.json and restore it."""

    def __init__(self, on_done=None, **kwargs):
        super().__init__(size_hint=(0.94, 0.9), **kwargs)
        self.background = ""
        self.background_color = (0, 0, 0, 0)
        self._on_done = on_done
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*theme.CHASSIS)
            self._bg = Rectangle(pos=root.pos, size=root.size)
            Color(*theme.METAL_LIGHT)
            self._line = Line(rectangle=(*root.pos, *root.size), width=dp(1))
        root.bind(
            pos=lambda _, p: (setattr(self._bg, "pos", p),
                              setattr(self._line, "rectangle", (*p, root.width, root.height))),
            size=lambda _, s: (setattr(self._bg, "size", s),
                               setattr(self._line, "rectangle", (*root.pos, s[0], s[1]))),
        )
        root.padding = [dp(14), dp(12)]
        root.spacing = dp(8)

        hdr = BoxLayout(size_hint_y=None, height=dp(38))
        hdr.add_widget(Label(text="[b]IMPORT HISTORY[/b]\n导入历史数据", markup=True,
                             color=theme.VFD_CYAN, font_size=dp(13),
                             halign="left", valign="middle"))
        close = Button(text="✕", size_hint_x=None, width=dp(36),
                       background_normal="", background_color=(0, 0, 0, 0),
                       color=theme.TEXT_MUTED, font_size=dp(18))
        close.bind(on_release=lambda _: self.dismiss())
        hdr.add_widget(close)
        root.add_widget(hdr)

        tip = Label(text="选择之前导出的备份文件（fitness_backup.json）以恢复数据。\n重复的记录会自动跳过。",
                    color=theme.TEXT_MUTED, font_size=dp(11), size_hint_y=None,
                    height=dp(34), halign="left", valign="middle")
        tip.bind(size=tip.setter("text_size"))
        root.add_widget(tip)

        rootpath = _BACKUP_DIR if os.path.isdir(_BACKUP_DIR) else os.path.expanduser("~")
        self._fc = FileChooserListView(filters=["*.json"],
                                       rootpath=rootpath,
                                       multiselect=False, size_hint=(1, 1))
        root.add_widget(self._fc)

        self._status = Label(text="", color=theme.TEXT_MUTED, font_size=dp(11),
                             size_hint_y=None, height=dp(20), halign="left", valign="middle",
                             markup=True)
        self._status.bind(size=self._status.setter("text_size"))
        root.add_widget(self._status)

        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        cancel = Button(text="取消", background_normal="",
                        background_color=theme.METAL_DARK,
                        color=theme.TEXT_PRIMARY, font_size=dp(14))
        cancel.bind(on_release=lambda _: self.dismiss())
        btns.add_widget(cancel)
        import_btn = Button(text="导入", background_normal="",
                            background_color=theme.VFD_CYAN,
                            color=(0.05, 0.05, 0.08, 1), font_size=dp(14), bold=True)
        import_btn.bind(on_release=lambda _: self._do_import())
        btns.add_widget(import_btn)
        root.add_widget(btns)

        self.add_widget(root)
        sounds.bind_feedback(root)

    def _do_import(self):
        sel = self._fc.selection
        if not sel:
            self._status.text = "[color=ff4444]请先选择一个备份文件[/color]"
            return
        path = sel[0]
        try:
            result = db.import_backup_file(path)
            msg = f"[color=88ffaa]导入完成：新增 {result['imported']} 条，跳过重复 {result['skipped']} 条[/color]"
            self._status.text = msg
            self._status.color = theme.TEXT_PRIMARY
            if self._on_done:
                self._on_done()
        except Exception as e:
            self._status.text = f"[color=ff4444]导入失败：{e}[/color]"
            self._status.color = theme.TEXT_PRIMARY
