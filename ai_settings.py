"""AI 设置弹窗：输入 API key / base url / model / system prompt，保存 + 测试连接。"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from config import theme
from llm_config import LLMConfig
import llm_client
import sounds

# 供应商预设：name -> {"base":..., "models":[...]}；None 表示自定义
# OpenCode 是聚合端点，已包含 minimax/kimi/glm/deepseek/qwen/mimo 全家
_OPENCODE_BASE = "https://opencode.ai/zen/go"
PROVIDERS = {
    "DeepSeek": {"base": "https://api.deepseek.com",
                 "models": ["deepseek-v4-flash", "deepseek-v4-pro"]},
    "OpenCode": {"base": _OPENCODE_BASE, "models": [
        "mimo-v2-omni", "mimo-v2-pro", "mimo-v2.5-pro", "mimo-v2.5",
        "glm-5.2", "glm-5.1", "glm-5",
        "deepseek-v4-pro", "deepseek-v4-flash",
        "kimi-k2.7-code", "kimi-k2.6", "kimi-k2.5",
        "qwen3.7-max", "qwen3.7-plus", "qwen3.6-plus", "qwen3.5-plus",
        "minimax-m3", "minimax-m2.7", "minimax-m2.5",
        "hy3-preview",
    ]},
    "MiMo": {"base": _OPENCODE_BASE, "models": [
        "mimo-v2-omni", "mimo-v2-pro", "mimo-v2.5-pro", "mimo-v2.5",
    ]},
    "MiMo直连": {"base": "https://api.xiaomimimo.com/v1",
                 "models": ["mimo-v2.5-pro", "mimo-v2.5"],
                 "labels": {"mimo-v2.5-pro": "mimo-v2.5-pro [仅文本]",
                            "mimo-v2.5": "mimo-v2.5 [图/音/视]"}},
    "自定义": None,
}


class AISettingsPopup(ModalView):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(0.92, 0.9), **kwargs)
        self.background = ""
        self.background_color = (0, 0, 0, 0)
        self._cfg = LLMConfig.load()
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*theme.SURFACE)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[dp(14)])
            Color(*theme.BORDER)
            self._line = Line(
                rounded_rectangle=(root.x, root.y, root.width, root.height, dp(14)),
                width=dp(1),
            )
        root.bind(
            pos=lambda _, p: (setattr(self._bg, "pos", p),
                               setattr(self._line, "rounded_rectangle",
                                       (p[0], p[1], root.width, root.height, dp(14)))),
            size=lambda _, s: (setattr(self._bg, "size", s),
                               setattr(self._line, "rounded_rectangle",
                                       (root.x, root.y, s[0], s[1], dp(14)))),
        )
        root.padding = [dp(16), dp(14)]
        root.spacing = dp(10)

        hdr = BoxLayout(size_hint_y=None, height=dp(30))
        hdr.add_widget(Label(text="[b]AI 设置[/b]", markup=True,
                             color=theme.GOLD, font_size=dp(18),
                             halign="left", valign="middle"))
        close = Button(text="[font=Symbols]✕[/font]", markup=True,
                       size_hint_x=None, width=dp(36),
                       background_normal="", background_color=(0, 0, 0, 0),
                       color=theme.TEXT_MUTED, font_size=dp(18))
        close.bind(on_release=lambda _: self.dismiss())
        hdr.add_widget(close)
        root.add_widget(hdr)

        preset_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(5))
        for name in PROVIDERS:
            b = Button(text=name, markup=True, font_size=dp(11),
                       background_normal="", background_color=theme.SURFACE_HIGH,
                       color=theme.TEXT_SECONDARY)
            b.bind(on_release=lambda _, n=name: self._apply_preset(n))
            preset_row.add_widget(b)
        root.add_widget(preset_row)

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        form = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        form.bind(minimum_height=form.setter("height"))

        self._key = self._field("API Key", self._cfg.api_key, password=True, hint="sk-...")
        self._base = self._field("Base URL", self._cfg.api_base_url, hint="https://api.deepseek.com")
        self._model_box, self._model_btns, self._selected_model = self._build_model_box()
        form.add_widget(self._key)
        form.add_widget(self._base)
        form.add_widget(self._model_box)
        self._sys = self._field("System Prompt", self._cfg.system_prompt,
                                multiline=True, height=dp(90),
                                hint="你是一个健身助手...")
        form.add_widget(self._sys)
        scroll.add_widget(form)
        root.add_widget(scroll)
        self._init_model_for_current()

        self._status = Label(text="", color=theme.TEXT_MUTED, font_size=dp(11),
                             halign="left", valign="middle", size_hint_y=None,
                             height=dp(18), markup=True)
        self._status.bind(size=self._status.setter("text_size"))
        root.add_widget(self._status)

        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        test_btn = Button(text="测试连接", background_normal="",
                          background_color=theme.SURFACE_HIGH,
                          color=theme.TEXT_PRIMARY, font_size=dp(14))
        test_btn.bind(on_release=lambda _: self._test())
        btn_row.add_widget(test_btn)
        save_btn = Button(text="保存", background_normal="",
                          background_color=theme.GOLD,
                          color=(0.05, 0.05, 0.08, 1), font_size=dp(14))
        save_btn.bind(on_release=lambda _: self._save())
        btn_row.add_widget(save_btn)
        root.add_widget(btn_row)

        self.add_widget(root)
        sounds.bind_feedback(root)

    def _field(self, title, value, password=False, multiline=False, height=dp(48), hint=""):
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        height=height + dp(16), spacing=dp(2))
        lbl = Label(text=title, color=theme.TEXT_MUTED, font_size=dp(11),
                    halign="left", valign="middle", size_hint_y=None, height=dp(14))
        lbl.bind(size=lbl.setter("text_size"))
        box.add_widget(lbl)
        ti = TextInput(text=value, multiline=multiline, password=password,
                       font_size=dp(13), foreground_color=theme.TEXT_PRIMARY,
                       background_normal="", background_color=theme.SURFACE_LIGHT,
                       cursor_color=theme.GOLD, padding=[dp(8), dp(4)],
                       hint_text=hint, hint_text_color=theme.TEXT_MUTED)
        box.add_widget(ti)
        return box

    def _build_model_box(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        spacing=dp(2))
        box.bind(minimum_height=box.setter("height"))
        lbl = Label(text="Model", color=theme.TEXT_MUTED, font_size=dp(11),
                    halign="left", valign="middle", size_hint_y=None, height=dp(14))
        lbl.bind(size=lbl.setter("text_size"))
        box.add_widget(lbl)
        self._model_grid = GridLayout(cols=3, size_hint_y=None,
                                      spacing=dp(5))
        self._model_grid.bind(minimum_height=self._model_grid.setter("height"))
        box.add_widget(self._model_grid)
        return box, {}, self._cfg.model

    def _init_model_for_current(self):
        base = self._cfg.api_base_url.rstrip("/")
        prov = "自定义"
        for name, info in PROVIDERS.items():
            if info and info["base"].rstrip("/") == base:
                prov = name
                break
        self._render_models(prov)

    def _render_models(self, provider_name):
        self._model_grid.clear_widgets()
        self._model_btns = {}
        info = PROVIDERS.get(provider_name)
        if info is None:
            ti = TextInput(text=self._selected_model or self._cfg.model,
                           multiline=False, font_size=dp(13),
                           foreground_color=theme.TEXT_PRIMARY,
                           background_normal="",
                           background_color=theme.SURFACE_LIGHT,
                           cursor_color=theme.GOLD, padding=[dp(8), dp(6)],
                           hint_text="手填 model 名",
                           hint_text_color=theme.TEXT_MUTED,
                           size_hint_y=None, height=dp(38))
            ti.bind(text=lambda i, v: setattr(self, "_selected_model", v.strip()))
            self._model_grid.add_widget(ti)
            return
        models = info["models"]
        if not models:
            tip = Label(text="（该预设暂无 model 列表，请在自定义里填）",
                        color=theme.TEXT_MUTED, font_size=dp(11),
                        halign="left", valign="middle",
                        size_hint_y=None, height=dp(20))
            tip.bind(size=tip.setter("text_size"))
            self._model_grid.add_widget(tip)
            return
        cur = self._selected_model or (models[0] if models else "")
        if cur not in models:
            cur = models[0] if models else ""
        for m in models:
            label = info.get("labels", {}).get(m, m)
            b = Button(text=label, markup=True, font_size=dp(10),
                       size_hint_y=None, height=dp(32),
                       background_normal="", background_color=theme.SURFACE_HIGH,
                       color=theme.TEXT_SECONDARY)
            b.bind(on_release=lambda _, mm=m: self._select_model(mm))
            self._model_btns[m] = b
            self._model_grid.add_widget(b)
        self._select_model(cur)

    def _select_model(self, m):
        self._selected_model = m
        for mm, b in self._model_btns.items():
            if mm == m:
                b.background_color = theme.GOLD
                b.color = (0.05, 0.05, 0.08, 1)
            else:
                b.background_color = theme.SURFACE_HIGH
                b.color = theme.TEXT_SECONDARY

    def _read(self):
        self._cfg.api_key = self._key.children[0].text.strip()
        self._cfg.api_base_url = self._base.children[0].text.strip()
        self._cfg.model = (self._selected_model or "").strip()
        self._cfg.system_prompt = self._sys.children[0].text.strip()

    def _apply_preset(self, name):
        info = PROVIDERS.get(name)
        # 切换 provider 就清空 key（不同 provider 的 key 不通用）
        self._key.children[0].text = ""
        if info is None:
            self._render_models("自定义")
            self._status.text = "[color=888888]自定义：手动填写 base/model/key[/color]"
            return
        base = info["base"]
        self._base.children[0].text = base
        self._render_models(name)
        if base:
            self._status.text = f"[color=88ccff]已套用 {name}，请填入对应 API Key[/color]"
        else:
            self._status.text = f"[color=ffaa00]{name}：base/model 待补[/color]"

    def _save(self):
        self._read()
        self._cfg.save()
        self._status.text = "[color=88ccff]已保存[/color]"
        self._status.color = theme.TEXT_PRIMARY

    def _test(self):
        self._read()
        if not self._cfg.is_configured:
            self._status.text = "[color=ff4444]请先填写 key / base / model[/color]"
            return
        self._status.text = "连接中..."
        import threading
        from kivy.clock import Clock

        def worker():
            try:
                c = llm_client.LLMClient(
                    api_key=self._cfg.api_key, api_base_url=self._cfg.api_base_url,
                    model=self._cfg.model, temperature=0.3, max_tokens=16,
                    max_retries=1, timeout=30.0,
                )
                txt = c.chat_text([{"role": "user", "content": "回复 ok"}])
                c.close()
                msg_ok = txt[:30]
                Clock.schedule_once(
                    lambda dt: self._set_status(True, msg_ok), 0)
            except Exception as e:
                msg_err = str(e)[:120]

                Clock.schedule_once(
                    lambda dt: self._set_status(False, msg_err), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _set_status(self, ok, msg):
        if ok:
            self._status.text = f"[color=88ffaa]连接成功：{msg}[/color]"
        else:
            self._status.text = f"[color=ff4444]失败：{msg}[/color]"
