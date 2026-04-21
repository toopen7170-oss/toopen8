import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('kivy', 'softinput_mode', 'pan')

from kivy.utils import platform
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

# ---------- Android 경로 ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "app.db")
LOG_FILE = os.path.join(BASE_DIR, "error_log.txt")

# ---------- 로그 ----------
def save_log(text):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n\n")
    except:
        pass

def handle_exception(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    save_log(msg)

sys.excepthook = handle_exception

# ---------- DB ----------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
cur.execute("""
CREATE TABLE IF NOT EXISTS chars (
    acc TEXT,
    slot INTEGER,
    type TEXT,
    data TEXT,
    PRIMARY KEY(acc, slot, type)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS photos (
    acc TEXT,
    slot INTEGER,
    path TEXT
)
""")
conn.commit()

# ---------- 공통 ----------
def get_path(file):
    p = resource_find(file)
    if p:
        return p
    local = os.path.join(os.getcwd(), file)
    return local if os.path.exists(local) else None

# ---------- 앱 ----------
class App(MDApp):
    def build(self):
        self.acc = None
        self.slot = None

        sm = ScreenManager()
        sm.add_widget(AccountScreen(name='acc'))
        sm.add_widget(CharSelectScreen(name='sel'))
        sm.add_widget(CharInfoScreen(name='info'))
        sm.add_widget(EquipScreen(name='equ'))
        sm.add_widget(InvenScreen(name='inv'))
        sm.add_widget(PhotoScreen(name='pho'))

        Clock.schedule_once(self.check_system, 1)
        return sm

    def check_system(self, dt):
        errors = []
        for f in ["bg.png", "icon.png", "font.ttf"]:
            if not get_path(f):
                errors.append(f"{f} 누락")

        if os.path.exists(LOG_FILE):
            errors.append("이전 오류 로그 존재")

        if errors:
            MDDialog(title="자가진단", text="\n".join(errors),
                     buttons=[MDRaisedButton(text="확인")]).open()

# ---------- 배경 ----------
class Base(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_added"):
            bg = get_path("bg.png")
            if bg:
                self.add_widget(Image(source=bg, opacity=0.15), index=0)
            self.bg_added = True

# ---------- 계정 ----------
class AccountScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = MDApp.get_running_app()

        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        self.search = MDTextField(hint_text="전체검색")
        self.search.bind(text=self.filter)
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="계정ID 입력")
        l.add_widget(self.input)

        btn = BoxLayout(size_hint_y=None, height=dp(50))
        btn.add_widget(MDRaisedButton(text="저장", on_release=self.save))
        btn.add_widget(MDRaisedButton(text="삭제", on_release=self.delete))
        l.add_widget(btn)

        self.list = GridLayout(cols=1, size_hint_y=None)
        self.list.bind(minimum_height=self.list.setter('height'))

        sv = MDScrollView()
        sv.add_widget(self.list)
        l.add_widget(sv)

        self.add_widget(l)
        self.refresh()

    def refresh(self):
        self.list.clear_widgets()
        cur.execute("SELECT name FROM accounts")
        for (name,) in cur.fetchall():
            self.list.add_widget(MDRaisedButton(text=name,
                on_release=lambda x, n=name: self.select(n)))

    def filter(self, inst, text):
        self.list.clear_widgets()
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+text+'%',))
        for (name,) in cur.fetchall():
            self.list.add_widget(MDRaisedButton(text=name,
                on_release=lambda x, n=name: self.select(n)))

    def select(self, name):
        self.app.acc = name
        self.manager.current = "sel"

    def save(self, obj):
        name = self.input.text.strip()
        if not name: return
        cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (name,))
        conn.commit()
        self.refresh()

    def delete(self, obj):
        name = self.input.text.strip()
        cur.execute("DELETE FROM accounts WHERE name=?", (name,))
        conn.commit()
        self.refresh()

# ---------- 슬롯 ----------
class CharSelectScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = MDApp.get_running_app()

        l = BoxLayout(orientation='vertical', padding=dp(20))
        grid = GridLayout(cols=2, spacing=dp(10))

        for i in range(1, 7):
            grid.add_widget(MDRaisedButton(
                text=f"Slot {i}",
                on_release=lambda x, s=i: self.select(s)
            ))

        l.add_widget(grid)

        l.add_widget(MDRaisedButton(text="정보", on_release=lambda x:self.go('info')))
        l.add_widget(MDRaisedButton(text="장비", on_release=lambda x:self.go('equ')))
        l.add_widget(MDRaisedButton(text="인벤토리", on_release=lambda x:self.go('inv')))
        l.add_widget(MDRaisedButton(text="사진", on_release=lambda x:self.go('pho')))

        self.add_widget(l)

    def select(self, slot):
        self.app.slot = slot

    def go(self, name):
        if not self.app.acc or not self.app.slot:
            MDDialog(title="경고", text="계정과 슬롯 선택 필요",
                     buttons=[MDRaisedButton(text="확인")]).open()
            return
        self.manager.current = name

# ---------- 공통 저장/불러오기 ----------
def save_section(app, section, data):
    cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)",
                (app.acc, app.slot, section, json.dumps(data)))
    conn.commit()

def load_section(app, section):
    cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type=?",
                (app.acc, app.slot, section))
    r = cur.fetchone()
    return json.loads(r[0]) if r else {}

# ---------- 정보 ----------
class CharInfoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = MDApp.get_running_app()

        self.fields = ["이름","직위","클랜","레벨",
                       "생명력","기력","근력",
                       "힘","정신력","재능","민첩","건강",
                       "명중","공격","방어","흡수","속도"]

        self.inputs = {}

        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        for f in self.fields:
            tf = MDTextField(hint_text=f)
            tf.bind(text=self.auto_save)
            self.inputs[f] = tf
            l.add_widget(tf)

        l.add_widget(MDRaisedButton(text="전체삭제", md_bg_color=(1,0,0,1),
                                    on_release=self.clear))
        l.add_widget(MDRectangleFlatButton(text="뒤로",
                                           on_release=lambda x:self.manager.current='sel'))

        sv.add_widget(l)
        self.add_widget(sv)

    def on_pre_enter(self):
        data = load_section(self.app, "info")
        for k,v in self.inputs.items():
            v.text = data.get(k, "")

    def auto_save(self, *a):
        data = {k:v.text for k,v in self.inputs.items()}
        save_section(self.app, "info", data)

    def clear(self, obj):
        for i in self.inputs.values():
            i.text = ""

# ---------- 장비 ----------
class EquipScreen(CharInfoScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.fields = ["한손무기","두손무기","갑옷","방패","장갑","부츠","암릿","링1","링2","아뮬랫","기타"]

# ---------- 인벤 ----------
class InvenScreen(CharInfoScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.fields = [f"아이템{i}" for i in range(1,21)]

# ---------- 사진 ----------
class PhotoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = MDApp.get_running_app()

        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        self.list = GridLayout(cols=1, size_hint_y=None)
        self.list.bind(minimum_height=self.list.setter('height'))

        sv = MDScrollView()
        sv.add_widget(self.list)

        l.add_widget(MDRaisedButton(text="사진 선택", on_release=self.pick))
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로",
                                           on_release=lambda x:self.manager.current='sel'))

        self.add_widget(l)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):
        self.list.clear_widgets()
        cur.execute("SELECT path FROM photos WHERE acc=? AND slot=?",
                    (self.app.acc, self.app.slot))
        for (p,) in cur.fetchall():
            self.list.add_widget(MDLabel(text=p))

    def pick(self, obj):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.selected)
        except Exception as e:
            save_log(str(e))

    def selected(self, selection):
        if selection:
            path = selection[0]
            cur.execute("INSERT INTO photos VALUES(?,?,?)",
                        (self.app.acc, self.app.slot, path))
            conn.commit()
            self.refresh()

# ---------- 실행 ----------
App().run()