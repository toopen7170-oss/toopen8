import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
# [전수검사] 자판 가림 방지 및 입력창 자동 올림
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('kivy', 'softinput_mode', 'pan')

from kivy.utils import platform
from kivy.resources import resource_find
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
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
from kivymd.uix.snackbar import MDSnackbar

# ---------- 경로 및 로그 ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "pt1_manager.db")
LOG_FILE = os.path.join(BASE_DIR, "crash_log.txt")

def handle_exception(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open(LOG_FILE, "a") as f: f.write(msg + "\n")

sys.excepthook = handle_exception

# ---------- DB 초기화 ----------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
cur.execute("CREATE TABLE IF NOT EXISTS photos (acc TEXT, slot INTEGER, path TEXT)")
conn.commit()

def get_path(file):
    p = resource_find(file)
    return p if p else (file if os.path.exists(file) else None)

# ---------- 메인 앱 ----------
class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.acc = None
        self.slot = None
        
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # [최우선] 자가 진단 시스템
        Clock.schedule_once(self.check_system, 1.5)
        return self.sm

    def check_system(self, dt):
        errors = []
        for f in ["bg.png", "icon.png", "font.ttf"]:
            if not get_path(f): errors.append(f"❌ {f} 누락")
        if errors:
            MDDialog(title="🚨 자가 진단", text="\n".join(errors),
                     buttons=[MDRaisedButton(text="확인", on_release=lambda x: x.parent.parent.parent.parent.dismiss())]).open()

# ---------- 공통 배경 ----------
class Base(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_set"):
            bg = get_path("bg.png")
            if bg: self.add_widget(Image(source=bg, opacity=0.15, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_set = True

# ---------- 1. 계정 생성창 ----------
class AccountScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        l.add_widget(MDLabel(text="계정 관리 시스템", halign="center", font_style="H5"))
        self.search = MDTextField(hint_text="🔍 전체 검색바", mode="rectangle")
        self.search.bind(text=self.filter_acc)
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="새 계정ID 입력")
        l.add_widget(self.input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_box.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=self.ask_save))
        btn_box.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=self.ask_del))
        l.add_widget(btn_box)

        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        sv = MDScrollView()
        sv.add_widget(self.list_layout)
        l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()

    def refresh(self):
        self.list_layout.clear_widgets()
        cur.execute("SELECT name FROM accounts")
        for (name,) in cur.fetchall():
            self.list_layout.add_widget(MDRectangleFlatButton(text=name, size_hint_x=1, 
                                                              on_release=lambda x, n=name: self.select_acc(n)))

    def filter_acc(self, inst, text):
        self.list_layout.clear_widgets()
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+text+'%',))
        for (name,) in cur.fetchall():
            self.list_layout.add_widget(MDRectangleFlatButton(text=name, size_hint_x=1, on_release=lambda x, n=name: self.select_acc(n)))

    def select_acc(self, name):
        MDApp.get_running_app().acc = name
        self.manager.current = "sel"

    def ask_save(self, obj):
        d = MDDialog(title="알림", text="저장하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: d.dismiss()),
            MDRaisedButton(text="저장", on_release=lambda x: self.do_save(d))
        ])
        d.open()

    def do_save(self, dialog):
        name = self.input.text.strip()
        if name:
            cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (name,))
            conn.commit()
            self.refresh()
        dialog.dismiss()

    def ask_del(self, obj):
        d = MDDialog(title="경고", text="삭제하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: d.dismiss()),
            MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), on_release=lambda x: self.do_del(d))
        ])
        d.open()

    def do_del(self, dialog):
        name = self.input.text.strip()
        cur.execute("DELETE FROM accounts WHERE name=?", (name,))
        conn.commit()
        self.refresh()
        dialog.dismiss()

# ---------- 2. 케릭 선택창 ----------
class CharSelectScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="케릭 선택 (6 Slot)", halign="center", font_style="H6"))
        
        grid = GridLayout(cols=2, spacing=dp(15))
        for i in range(1, 7):
            grid.add_widget(MDRaisedButton(text=f"Slot {i}", size_hint=(1, 1), 
                                          on_release=lambda x, s=i: self.set_slot(s)))
        l.add_widget(grid)
        
        menu = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        for n, sn in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            menu.add_widget(MDRaisedButton(text=n, on_release=lambda x, s=sn: self.go(s)))
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="계정선택으로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def set_slot(self, s):
        MDApp.get_running_app().slot = s
        MDSnackbar(text=f"Slot {s} 선택됨").open()

    def go(self, name):
        app = MDApp.get_running_app()
        if not app.acc or not app.slot:
            MDSnackbar(text="계정과 슬롯을 먼저 선택해주세요").open()
            return
        self.manager.current = name

# ---------- 3. 케릭정보창 (제1원칙 19종 그룹화) ----------
class CharInfoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [제1원칙] 19종 그룹화 배치
        self.groups = [
            [('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
            [('생명력', ''), ('기력', ''), ('근력', '')],
            [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
            [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]
        ]
        
        sv = MDScrollView()
        self.container = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        self.container.bind(minimum_height=self.container.setter('height'))
        
        for group in self.groups:
            for label, _ in group:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(MDLabel(text=label, size_hint_x=0.3, halign="center"))
                tf = MDTextField(hint_text=f"{label} 입력", halign="center", mode="fill")
                tf.bind(text=self.auto_save)
                self.inputs[label] = tf
                row.add_widget(tf)
                self.container.add_widget(row)
            self.container.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 비가시적 간격

        self.container.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=self.ask_clear))
        self.container.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(self.container)
        self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type=?", (app.acc, app.slot, "info"))
        r = cur.fetchone()
        data = json.loads(r[0]) if r else {}
        for k, v in self.inputs.items(): v.text = data.get(k, "")

    def auto_save(self, *a):
        app = MDApp.get_running_app()
        data = {k: v.text for k, v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, "info", json.dumps(data)))
        conn.commit()

    def ask_clear(self, obj):
        d = MDDialog(title="경고", text="전체 삭제하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: d.dismiss()),
            MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), on_release=lambda x: self.do_clear(d))
        ])
        d.open()

    def do_clear(self, d):
        for v in self.inputs.values(): v.text = ""
        d.dismiss()

# ---------- 4. 케릭장비창 (11종 고정) ----------
class EquipScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        items = ["한손무기","두손무기","갑옷","방패","장갑","부츠","암릿","링1","링2","아뮬랫","기타"]
        
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(50))
            row.add_widget(MDLabel(text=item, size_hint_x=0.4, halign="center"))
            tf = MDTextField(halign="center")
            tf.bind(text=self.auto_save)
            self.inputs[item] = tf
            row.add_widget(tf)
            l.add_widget(row)

        l.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=lambda x: self.do_clear()))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type=?", (app.acc, app.slot, "equ"))
        r = cur.fetchone()
        data = json.loads(r[0]) if r else {}
        for k, v in self.inputs.items(): v.text = data.get(k, "")

    def auto_save(self, *a):
        app = MDApp.get_running_app()
        data = {k: v.text for k, v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, "equ", json.dumps(data)))
        conn.commit()

    def do_clear(self):
        for v in self.inputs.values(): v.text = ""

# ---------- 5. 인벤토리창 (수정 모드 지원) ----------
class InvenScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="인벤토리 (20칸)", halign="center"))
        
        sv = MDScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"인벤토리 {i}번", halign="center")
            tf.bind(text=self.auto_save)
            self.inputs[i] = tf
            self.grid.add_widget(tf)
            
        sv.add_widget(self.grid)
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type=?", (app.acc, app.slot, "inv"))
        r = cur.fetchone()
        data = json.loads(r[0]) if r else {}
        for k, v in self.inputs.items(): v.text = data.get(str(k), "")

    def auto_save(self, *a):
        app = MDApp.get_running_app()
        data = {k: v.text for k, v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, "inv", json.dumps(data)))
        conn.commit()

# ---------- 6. 사진 선택창 ----------
class PhotoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진첩 관리", halign="center"))
        
        self.img_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(10))
        self.img_list.bind(minimum_height=self.img_list.setter('height'))
        sv = MDScrollView()
        sv.add_widget(self.img_list)
        
        l.add_widget(MDRaisedButton(text="사진 추가 (갤러리)", size_hint_x=1, on_release=self.open_picker))
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()

    def refresh(self):
        self.img_list.clear_widgets()
        app = MDApp.get_running_app()
        cur.execute("SELECT path FROM photos WHERE acc=? AND slot=?", (app.acc, app.slot))
        for (p,) in cur.fetchall():
            row = BoxLayout(size_hint_y=None, height=dp(40))
            row.add_widget(MDLabel(text=os.path.basename(p)))
            row.add_widget(MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), on_release=lambda x, path=p: self.del_photo(path)))
            self.img_list.add_widget(row)

    def open_picker(self, obj):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.on_select, multiple=True)
        except: MDSnackbar(text="지원되지 않는 환경입니다").open()

    def on_select(self, selection):
        if selection:
            app = MDApp.get_running_app()
            for p in selection:
                cur.execute("INSERT INTO photos VALUES(?,?,?)", (app.acc, app.slot, p))
            conn.commit()
            self.refresh()

    def del_photo(self, path):
        app = MDApp.get_running_app()
        cur.execute("DELETE FROM photos WHERE acc=? AND slot=? AND path=?", (app.acc, app.slot, path))
        conn.commit()
        self.refresh()

if __name__ == '__main__':
    PristonTaleApp().run()
