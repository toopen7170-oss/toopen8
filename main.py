import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
# [전수검사] S26 울트라 자판 대응 및 레이아웃 고정
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
from kivy.core.text import LabelBase # [신규] 폰트 등록용

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar

# ---------- [전수검사] 경로 설정 ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "pt1_manager.db")
LOG_FILE = os.path.join(BASE_DIR, "crash_log.txt")

def get_path(file):
    p = resource_find(file)
    return p if p else (file if os.path.exists(file) else None)

# ---------- [오류0] 폰트 강제 등록 (ㅁㅁ현상 해결) ----------
FONT_PATH = get_path("font.ttf")
if FONT_PATH:
    LabelBase.register(name="KoreanFont", fn_regular=FONT_PATH)
    # KivyMD 기본 폰트를 등록한 한글 폰트로 교체
    from kivymd.icon_definitions import md_icons
    Config.set('kivy', 'default_font', ['KoreanFont', FONT_PATH])

# ---------- DB 초기화 ----------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
cur.execute("CREATE TABLE IF NOT EXISTS photos (acc TEXT, slot INTEGER, path TEXT)")
conn.commit()

# ---------- 메인 앱 엔진 ----------
class PristonTaleApp(MDApp):
    def build(self):
        # [점주님 원칙] 디자인 유지
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"
        self.acc = None
        self.slot = None
        
        # 폰트 전역 적용
        if FONT_PATH:
            self.theme_cls.font_styles["H5"] = ["KoreanFont", 24, False, 0.15]
            self.theme_cls.font_styles["Button"] = ["KoreanFont", 14, False, 0.15]
            self.theme_cls.font_styles["Body1"] = ["KoreanFont", 16, False, 0.15]

        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # [최우선] 자가 진단 실행 (1.5초 후)
        Clock.schedule_once(self.check_system, 1.5)
        return self.sm

    def check_system(self, dt):
        errors = []
        if not FONT_PATH: errors.append("❌ font.ttf 누락 (글자 깨짐 원인)")
        if not get_path("bg.png"): errors.append("❌ bg.png 누락")
        if not get_path("icon.png"): errors.append("❌ icon.png 누락")
        
        if errors:
            self.diag = MDDialog(
                title="🚨 자가 진단 보고",
                text="[System Check]\n" + "\n".join(errors),
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.diag.dismiss())]
            )
            self.diag.open()

# ---------- 배경 공통 ----------
class Base(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_added"):
            bg = get_path("bg.png")
            if bg: self.add_widget(Image(source=bg, opacity=0.2, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_added = True

# ---------- 1. 계정 생성창 ----------
class AccountScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="계정 관리 시스템", halign="center", font_style="H5"))
        
        self.search = MDTextField(hint_text="🔍 전체 계정 검색바", mode="rectangle")
        self.search.bind(text=self.filter_acc)
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="새 계정ID 입력")
        l.add_widget(self.input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_box.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=lambda x: self.ask("저장", self.do_save)))
        btn_box.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0.2,0.2,1), on_release=lambda x: self.ask("삭제", self.do_del)))
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
            self.list_layout.add_widget(MDRectangleFlatButton(text=name, size_hint_x=1, on_release=lambda x, n=name: self.select_acc(n)))

    def filter_acc(self, inst, text):
        self.list_layout.clear_widgets()
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+text+'%',))
        for (name,) in cur.fetchall():
            self.list_layout.add_widget(MDRectangleFlatButton(text=name, size_hint_x=1, on_release=lambda x, n=name: self.select_acc(n)))

    def select_acc(self, name):
        MDApp.get_running_app().acc = name
        self.manager.current = "sel"

    def ask(self, title, func):
        self.diag = MDDialog(title="알림", text=f"{title}하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.diag.dismiss()),
            MDRaisedButton(text="확인", on_release=lambda x: func())
        ])
        self.diag.open()

    def do_save(self):
        n = self.input.text.strip()
        if n: cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,)); conn.commit(); self.refresh()
        self.diag.dismiss()

    def do_del(self):
        n = self.input.text.strip()
        cur.execute("DELETE FROM accounts WHERE name=?", (n,)); conn.commit(); self.refresh()
        self.diag.dismiss()

# ---------- 2. 케릭 선택창 ----------
class CharSelectScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="케릭 선택 (6 Slot)", halign="center"))
        
        grid = GridLayout(cols=2, spacing=dp(15))
        for i in range(1, 7):
            grid.add_widget(MDRaisedButton(text=f"Slot {i}", size_hint=(1, 1), on_release=lambda x, s=i: self.set_slot(s)))
        l.add_widget(grid)
        
        menu = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        for n, sn in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            menu.add_widget(MDRaisedButton(text=n, on_release=lambda x, s=sn: self.go(s)))
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="계정 전환", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def set_slot(self, s):
        MDApp.get_running_app().slot = s
        MDSnackbar(text=f"Slot {s} 가 선택되었습니다.").open()

    def go(self, name):
        app = MDApp.get_running_app()
        if not app.acc or not app.slot:
            MDSnackbar(text="계정과 슬롯을 먼저 선택하세요.").open()
            return
        self.manager.current = name

# ---------- 3. 케릭정보창 (제1원칙 19종 그룹화) ----------
class CharInfoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [제1원칙] 19종 항목 및 4개 그룹 분리
        groups = [
            [('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
            [('생명력', ''), ('기력', ''), ('근력', '')],
            [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
            [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]
        ]
        
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for g in groups:
            for label, _ in g:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(MDLabel(text=label, size_hint_x=0.3, halign="center"))
                tf = MDTextField(hint_text=f"{label} 입력", halign="center", mode="fill")
                tf.bind(text=self.auto_save)
                self.inputs[label] = tf
                row.add_widget(tf)
                l.add_widget(row)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # [비가시적 간격]

        l.add_widget(MDRaisedButton(text="목록 전체 삭제", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=1, on_release=self.ask_clear))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='info'", (app.acc, app.slot))
        r = cur.fetchone()
        data = json.loads(r[0]) if r else {}
        for k, v in self.inputs.items(): v.text = data.get(k, "")

    def auto_save(self, *a):
        app = MDApp.get_running_app()
        data = {k: v.text for k, v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, "info", json.dumps(data)))
        conn.commit()

    def ask_clear(self, obj):
        self.diag = MDDialog(title="경고", text="삭제하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.diag.dismiss()),
            MDRaisedButton(text="삭제", on_release=lambda x: self.do_clear())
        ])
        self.diag.open()

    def do_clear(self):
        for v in self.inputs.values(): v.text = ""
        self.diag.dismiss()

# ---------- 4. 케릭장비창 (11종 고정) ----------
class EquipScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        items = ["한손무기","두손무기","갑옷","방패","장갑","부츠","암릿","링1","링2","아뮬랫","기타"]
        
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(50))
            row.add_widget(MDLabel(text=item, size_hint_x=0.4, halign="center"))
            tf = MDTextField(halign="center")
            tf.bind(text=self.auto_save)
            self.inputs[item] = tf
            row.add_widget(tf)
            l.add_widget(row)

        l.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(0.8,0.2,0.2,1), size_hint_x=1, on_release=self.do_clear))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='equ'", (app.acc, app.slot))
        r = cur.fetchone()
        data = json.loads(r[0]) if r else {}
        for k, v in self.inputs.items(): v.text = data.get(k, "")

    def auto_save(self, *a):
        app = MDApp.get_running_app()
        data = {k: v.text for k, v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, "equ", json.dumps(data)))
        conn.commit()

    def do_clear(self, *a):
        for v in self.inputs.values(): v.text = ""

# ---------- 5. 인벤토리창 (수정모드) ----------
class InvenScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="인벤토리 (한 줄 클릭 시 수정)", halign="center"))
        
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        grid.bind(minimum_height=grid.setter('height'))
        
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"Slot {i}", halign="center")
            tf.bind(text=self.auto_save)
            self.inputs[i] = tf
            grid.add_widget(tf)
            
        sv.add_widget(grid)
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='inv'", (app.acc, app.slot))
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
        l.add_widget(MDLabel(text="사진 선택 및 관리", halign="center"))
        
        self.img_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(10))
        self.img_list.bind(minimum_height=self.img_list.setter('height'))
        sv = MDScrollView()
        sv.add_widget(self.img_list)
        
        l.add_widget(MDRaisedButton(text="사진 추가 (핸드폰에서 선택)", size_hint_x=1, on_release=self.open_picker))
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()
    def refresh(self):
        self.img_list.clear_widgets()
        app = MDApp.get_running_app()
        cur.execute("SELECT path FROM photos WHERE acc=? AND slot=?", (app.acc, app.slot))
        for (p,) in cur.fetchall():
            row = BoxLayout(size_hint_y=None, height=dp(45))
            row.add_widget(MDLabel(text=os.path.basename(p)))
            row.add_widget(MDRaisedButton(text="삭제", md_bg_color=(0.8,0.2,0.2,1), on_release=lambda x, path=p: self.del_photo(path)))
            self.img_list.add_widget(row)

    def open_picker(self, obj):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.on_select, multiple=True)
        except: MDSnackbar(text="지원되지 않는 환경입니다.").open()

    def on_select(self, selection):
        if selection:
            app = MDApp.get_running_app()
            for p in selection: cur.execute("INSERT INTO photos VALUES(?,?,?)", (app.acc, app.slot, p))
            conn.commit(); self.refresh()

    def del_photo(self, path):
        app = MDApp.get_running_app()
        cur.execute("DELETE FROM photos WHERE acc=? AND slot=? AND path=?", (app.acc, app.slot, path))
        conn.commit(); self.refresh()

if __name__ == '__main__':
    PristonTaleApp().run()
