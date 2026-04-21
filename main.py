import os
import sys
import traceback

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('kivy', 'softinput_mode', 'pan')

from kivy.resources import resource_find
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

# ---------------- 로그 시스템 ----------------
LOG_FILE = "error_log.txt"

def save_log(text):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n\n")
    except:
        pass

def handle_exception(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    save_log(error_msg)
    print(error_msg)

sys.excepthook = handle_exception

# ---------------- 공통 ----------------
def get_path(file):
    return resource_find(file)

DATA_FILE = "data.txt"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"accounts": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return eval(f.read())
    except:
        return {"accounts": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(str(data))

# ---------------- 앱 ----------------
class App(MDApp):
    def build(self):
        self.data = load_data()

        sm = ScreenManager()
        sm.add_widget(AccountScreen(name='acc'))
        sm.add_widget(CharSelectScreen(name='sel'))
        sm.add_widget(CharInfoScreen(name='info'))
        sm.add_widget(EquipScreen(name='equ'))
        sm.add_widget(InvenScreen(name='inv'))
        sm.add_widget(PhotoScreen(name='pho'))

        # 🔥 자가진단 실행
        Clock.schedule_once(self.check_system, 1)

        return sm

    def check_system(self, dt):
        errors = []

        if not get_path("icon.png"):
            errors.append("icon.png 누락")

        if not get_path("bg.png"):
            errors.append("bg.png 누락")

        if not get_path("font.ttf"):
            errors.append("font.ttf 누락")

        if os.path.exists(LOG_FILE):
            errors.append("이전 실행 오류 로그 존재")

        if errors:
            MDDialog(
                title="🚨 자가 진단",
                text="\n".join(errors),
                buttons=[MDRaisedButton(text="확인")]
            ).open()

# ---------------- 배경 ----------------
class Base(Screen):
    def on_enter(self):
        try:
            bg = get_path("bg.png")
            if bg:
                self.add_widget(Image(source=bg, opacity=0.15), index=0)
        except Exception as e:
            save_log(str(e))

# ---------------- 1. 계정 ----------------
class AccountScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.app = MDApp.get_running_app()

        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        self.search = MDTextField(hint_text="전체검색")
        self.search.bind(text=self.filter_list)
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="계정ID 입력")
        l.add_widget(self.input)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="저장", on_release=self.save))
        btns.add_widget(MDRaisedButton(text="삭제", on_release=self.delete))
        l.add_widget(btns)

        self.list = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list.bind(minimum_height=self.list.setter('height'))

        sv = MDScrollView()
        sv.add_widget(self.list)
        l.add_widget(sv)

        self.add_widget(l)
        self.refresh()

    def refresh(self):
        self.list.clear_widgets()
        for acc in self.app.data["accounts"]:
            self.list.add_widget(
                MDRaisedButton(text=acc, on_release=lambda x, a=acc: self.select(a))
            )

    def filter_list(self, instance, text):
        self.list.clear_widgets()
        for acc in self.app.data["accounts"]:
            if text in acc:
                self.list.add_widget(
                    MDRaisedButton(text=acc, on_release=lambda x, a=acc: self.select(a))
                )

    def select(self, acc):
        self.manager.current = "sel"

    def save(self, obj):
        name = self.input.text.strip()
        if not name:
            return

        def ok(x):
            self.app.data["accounts"].append(name)
            save_data(self.app.data)
            self.refresh()

        MDDialog(title="확인", text="저장하겠습니까?",
                 buttons=[MDRaisedButton(text="예", on_release=ok)]).open()

    def delete(self, obj):
        name = self.input.text.strip()
        if name not in self.app.data["accounts"]:
            return

        def ok(x):
            self.app.data["accounts"].remove(name)
            save_data(self.app.data)
            self.refresh()

        MDDialog(title="확인", text="삭제하겠습니까?",
                 buttons=[MDRaisedButton(text="예", on_release=ok)]).open()

# ---------------- 2. 캐릭 선택 ----------------
class CharSelectScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)

        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        grid = GridLayout(cols=2, spacing=dp(10))

        for i in range(1, 7):
            grid.add_widget(MDRaisedButton(text=f"Slot {i}"))

        l.add_widget(grid)

        l.add_widget(MDRaisedButton(text="정보", on_release=lambda x: self.go("info")))
        l.add_widget(MDRaisedButton(text="장비", on_release=lambda x: self.go("equ")))
        l.add_widget(MDRaisedButton(text="인벤토리", on_release=lambda x: self.go("inv")))
        l.add_widget(MDRaisedButton(text="사진", on_release=lambda x: self.go("pho")))

        self.add_widget(l)

    def go(self, name):
        self.manager.current = name

# ---------------- 3. 캐릭 정보 ----------------
class CharInfoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)

        fields = [
            ["이름","직위","클랜","레벨"],
            ["생명력","기력","근력"],
            ["힘","정신력","재능","민첩","건강"],
            ["명중","공격","방어","흡수","속도"]
        ]

        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        self.inputs = []

        for group in fields:
            for f in group:
                tf = MDTextField(hint_text=f, halign="center")
                self.inputs.append(tf)
                l.add_widget(tf)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(15)))

        l.add_widget(MDRaisedButton(text="전체삭제", md_bg_color=(1,0,0,1),
                                    on_release=self.clear_all))
        l.add_widget(MDRectangleFlatButton(text="뒤로",
                                           on_release=lambda x: setattr(self.manager,'current','sel')))

        sv.add_widget(l)
        self.add_widget(sv)

    def clear_all(self, obj):
        def ok(x):
            for i in self.inputs:
                i.text = ""
        MDDialog(title="삭제", text="삭제하겠습니까?",
                 buttons=[MDRaisedButton(text="예", on_release=ok)]).open()

# ---------------- 4. 장비 ----------------
class EquipScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)

        items = ["한손무기","두손무기","갑옷","방패","장갑","부츠","암릿","링1","링2","아뮬랫","기타"]

        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        self.inputs = []

        for item in items:
            tf = MDTextField(hint_text=item, halign="center")
            self.inputs.append(tf)
            l.add_widget(tf)

        l.add_widget(MDRaisedButton(text="전체삭제", md_bg_color=(1,0,0,1),
                                    on_release=self.clear_all))
        l.add_widget(MDRectangleFlatButton(text="뒤로",
                                           on_release=lambda x: setattr(self.manager,'current','sel')))

        sv.add_widget(l)
        self.add_widget(sv)

    def clear_all(self, obj):
        def ok(x):
            for i in self.inputs:
                i.text = ""
        MDDialog(title="삭제", text="삭제하겠습니까?",
                 buttons=[MDRaisedButton(text="예", on_release=ok)]).open()

# ---------------- 5. 인벤 ----------------
class InvenScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)

        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        self.items = []

        for i in range(20):
            tf = MDTextField(hint_text=f"아이템 {i+1}", halign="center")
            self.items.append(tf)
            l.add_widget(tf)

        l.add_widget(MDRaisedButton(text="전체삭제", md_bg_color=(1,0,0,1),
                                    on_release=self.clear_all))
        l.add_widget(MDRectangleFlatButton(text="뒤로",
                                           on_release=lambda x: setattr(self.manager,'current','sel')))

        sv.add_widget(l)
        self.add_widget(sv)

    def clear_all(self, obj):
        def ok(x):
            for i in self.items:
                i.text = ""
        MDDialog(title="삭제", text="삭제하겠습니까?",
                 buttons=[MDRaisedButton(text="예", on_release=ok)]).open()

# ---------------- 6. 사진 ----------------
class PhotoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)

        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        l.add_widget(MDLabel(text="사진 선택"))

        l.add_widget(MDRaisedButton(text="사진 선택", on_release=self.pick))
        l.add_widget(MDRaisedButton(text="저장"))
        l.add_widget(MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1)))

        l.add_widget(MDRectangleFlatButton(text="뒤로",
                                           on_release=lambda x: setattr(self.manager,'current','sel')))

        self.add_widget(l)

    def pick(self, obj):
        MDDialog(title="안내", text="갤러리 연동은 다음 단계에서 구현").open()

# ---------------- 실행 ----------------
App().run()