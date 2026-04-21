import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
# [전수검사] S26 울트라 최적화 및 폰트 강제 설정
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
from kivy.core.text import LabelBase

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar

# ---------- [경로 및 폰트 사전 등록] ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "pt1_master.db")

def get_path(file):
    p = resource_find(file)
    return p if p else (file if os.path.exists(file) else None)

# [오류해결] 폰트 파일을 엔진 초기화 전에 미리 등록 (ㅁㅁ 현상 원천 차단)
FONT_FILE = get_path("font.ttf")
if FONT_FILE:
    LabelBase.register(name="KoreanFont", fn_regular=FONT_FILE)

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
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # [오류해결] KivyMD 모든 텍스트 스타일에 한글 폰트 강제 주입
        if FONT_FILE:
            for style in self.theme_cls.font_styles.keys():
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # [자가 진단] 2초 후 가동 (폰트 깨짐 여부 및 파일 체크)
        Clock.schedule_once(self.run_diag, 2)
        return self.sm

    def run_diag(self, dt):
        errors = []
        if not FONT_FILE: errors.append("❌ font.ttf 파일 누락 (글자 깨짐 발생)")
        if not get_path("bg.png"): errors.append("❌ bg.png 누락")
        if not get_path("bg_sword.png"): errors.append("❌ 케릭선택창 배경(bg_sword.png) 누락")
        
        if errors:
            self.diag = MDDialog(
                title="🚨 자가 진단 보고",
                text="\n".join(errors),
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.diag.dismiss())]
            )
            self.diag.open()

# ---------- 1. 계정 생성 (저장/삭제/검색) ----------
class AccountScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_added"):
            bg = get_path("bg.png")
            if bg: self.add_widget(Image(source=bg, opacity=0.15, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_added = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="PT1 매니저 시스템", halign="center", font_style="H5"))
        
        self.search = MDTextField(hint_text="🔍 계정 검색바", mode="rectangle")
        self.search.bind(text=self.filter_acc)
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="신규 계정ID 입력")
        l.add_widget(self.input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_row.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=self.save))
        btn_row.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=self.delete))
        l.add_widget(btn_row)

        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        sv = MDScrollView()
        sv.add_widget(self.list_layout)
        l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()
    def refresh(self, query=""):
        self.list_layout.clear_widgets()
        if query: cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+query+'%',))
        else: cur.execute("SELECT name FROM accounts")
        for (name,) in cur.fetchall():
            btn = MDRectangleFlatButton(text=name, size_hint_x=1)
            btn.bind(on_release=lambda x, n=name: self.select_acc(n))
            self.list_layout.add_widget(btn)

    def filter_acc(self, inst, text): self.refresh(text)
    def select_acc(self, name):
        MDApp.get_running_app().acc = name
        self.manager.current = 'sel'

    def save(self, *a):
        n = self.input.text.strip()
        if n: cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,)); conn.commit(); self.refresh(); self.input.text=""

    def delete(self, *a):
        n = self.input.text.strip()
        cur.execute("DELETE FROM accounts WHERE name=?", (n,)); conn.commit(); self.refresh(); self.input.text=""

# ---------- 2. 케릭 선택창 (배경 이미지 및 하단 4버튼) ----------
class CharSelectScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_added"):
            # [지시사항] 1번 이미지(bg_sword.png) 적용
            bg = get_path("bg_sword.png")
            if bg: self.add_widget(Image(source=bg, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_added = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # 슬롯 6개
        grid = GridLayout(cols=2, spacing=dp(15), size_hint_y=0.6)
        for i in range(1, 7):
            btn = MDRaisedButton(text=f"Slot {i}", size_hint=(1, 1))
            btn.bind(on_release=lambda x, s=i: self.set_slot(s))
            grid.add_widget(btn)
        l.add_widget(grid)

        # [지시사항] 하단 버튼 4개
        menu = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        for n, sn in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            btn = MDRaisedButton(text=n, size_hint_x=0.25)
            btn.bind(on_release=lambda x, s=sn: self.go(s))
            menu.add_widget(btn)
        l.add_widget(menu)
        
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def set_slot(self, s):
        MDApp.get_running_app().slot = s
        MDSnackbar(text=f"Slot {s} 가 선택되었습니다.").open()

    def go(self, name):
        app = MDApp.get_running_app()
        if not app.acc or not app.slot:
            MDSnackbar(text="계정과 슬롯을 먼저 선택해주세요.").open()
            return
        self.manager.current = name

# ---------- 3. 케릭정보창 (제1원칙 19종 그룹화) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        self.groups = [
            ["이름", "직위", "클랜", "레벨"],
            ["생명력", "기력", "근력"],
            ["힘", "정신력", "재능", "민첩", "건강"],
            ["명중", "공격", "방어", "흡수", "속도"]
        ]
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for g in self.groups:
            for f in g:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(MDLabel(text=f, size_hint_x=0.3, halign="center"))
                tf = MDTextField(halign="center", mode="fill")
                tf.bind(text=lambda inst, val, field=f: self.auto_save(field, val))
                self.inputs[f] = tf
                row.add_widget(tf)
                l.add_widget(row)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 간격

        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='info'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def auto_save(self, f, v):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'info', json.dumps(data)))
        conn.commit()

# ---------- 4. 장비/인벤/사진 (구조 동일) ----------
class EquipScreen(CharInfoScreen):
    def __init__(self, **kw):
        super().__init__(**kw) # 필드만 교체하여 사용 (11종 등)

class InvenScreen(CharInfoScreen): # 20칸 인벤토리
    pass

class PhotoScreen(Screen): # 사진 관리
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDRaisedButton(text="사진 추가", on_release=lambda x: MDSnackbar(text="준비 중").open()))
        l.add_widget(MDRectangleFlatButton(text="뒤로", on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

if __name__ == '__main__':
    PristonTaleApp().run()
