import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
# [전수검사] 입력창 최적화 및 폰트 강제 설정
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

# ---------- [오류0] 경로 및 폰트 강제 등록 ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "pt1_data.db")
LOG_FILE = os.path.join(BASE_DIR, "crash_log.txt")

def get_path(file):
    p = resource_find(file)
    return p if p else (file if os.path.exists(file) else None)

# [핵심] 모든 한글 깨짐 방지를 위한 전역 폰트 등록
FONT_FILE = get_path("font.ttf")
if FONT_FILE:
    LabelBase.register(name="KoreanFont", fn_regular=FONT_FILE)

# ---------- DB 초기화 (무결성 검사) ----------
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
        
        # [오류해결] KivyMD의 모든 텍스트 스타일을 font.ttf로 강제 맵핑 (ㅁㅁ 현상 방지)
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

        # [자가 진단] UI가 완전히 뜬 후 2.5초 뒤 가동
        Clock.schedule_once(self.run_diagnostic, 2.5)
        return self.sm

    def run_diagnostic(self, dt):
        msgs = []
        if not FONT_FILE: msgs.append("❌ font.ttf 가 없습니다. (글자 깨짐 발생)")
        if not get_path("bg.png"): msgs.append("❌ bg.png 배경파일이 없습니다.")
        if not get_path("icon.png"): msgs.append("❌ icon.png 아이콘이 없습니다.")
        
        if msgs:
            self.dialog = MDDialog(
                title="🚨 자가 진단 시스템",
                text="\n".join(msgs),
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.dialog.dismiss())]
            )
            self.dialog.open()

# ---------- 공통 배경 ----------
class Base(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_set"):
            bg = get_path("bg.png")
            if bg:
                self.add_widget(Image(source=bg, opacity=0.15, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_set = True

# ---------- 1. 계정 생성 (저장/삭제 오류 해결) ----------
class AccountScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="계정 관리 시스템", halign="center", font_style="H5"))
        
        self.search_input = MDTextField(hint_text="🔍 전체 검색바", mode="rectangle")
        self.search_input.bind(text=self.on_search)
        l.add_widget(self.search_input)

        self.id_input = MDTextField(hint_text="새 계정ID 입력")
        l.add_widget(self.id_input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_row.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=self.confirm_save))
        btn_row.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8, 0, 0, 1), on_release=self.confirm_delete))
        l.add_widget(btn_row)

        self.list_view = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_view.bind(minimum_height=self.list_view.setter('height'))
        sv = MDScrollView()
        sv.add_widget(self.list_view)
        l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.load_accounts()

    def load_accounts(self, query=""):
        self.list_view.clear_widgets()
        if query:
            cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+query+'%',))
        else:
            cur.execute("SELECT name FROM accounts")
        for (name,) in cur.fetchall():
            btn = MDRectangleFlatButton(text=name, size_hint_x=1)
            btn.bind(on_release=lambda x, n=name: self.go_to_char(n))
            self.list_view.add_widget(btn)

    def on_search(self, instance, value): self.load_accounts(value)

    def go_to_char(self, name):
        MDApp.get_running_app().acc = name
        self.manager.current = 'sel'

    def confirm_save(self, *args):
        self.dialog = MDDialog(title="저장", text="계정을 저장하시겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog.dismiss()),
            MDRaisedButton(text="확인", on_release=self.execute_save)
        ])
        self.dialog.open()

    def execute_save(self, *args):
        name = self.id_input.text.strip()
        if name:
            cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (name,))
            conn.commit()
            self.load_accounts()
            self.id_input.text = ""
        self.dialog.dismiss()

    def confirm_delete(self, *args):
        self.dialog = MDDialog(title="삭제", text="계정을 삭제하시겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog.dismiss()),
            MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), on_release=self.execute_delete)
        ])
        self.dialog.open()

    def execute_delete(self, *args):
        name = self.id_input.text.strip()
        cur.execute("DELETE FROM accounts WHERE name=?", (name,))
        conn.commit()
        self.load_accounts()
        self.id_input.text = ""
        self.dialog.dismiss()

# ---------- 2. 케릭 선택창 ----------
class CharSelectScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        grid = GridLayout(cols=2, spacing=dp(10))
        for i in range(1, 7):
            btn = MDRaisedButton(text=f"Slot {i}", size_hint=(1, 1))
            btn.bind(on_release=lambda x, s=i: self.select_slot(s))
            grid.add_widget(btn)
        l.add_widget(grid)
        
        menu = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        for n, screen in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            btn = MDRaisedButton(text=n)
            btn.bind(on_release=lambda x, sc=screen: self.go(sc))
            menu.add_widget(btn)
        l.add_widget(menu)
        self.add_widget(l)

    def select_slot(self, s):
        MDApp.get_running_app().slot = s
        MDSnackbar(text=f"Slot {s} 가 선택되었습니다.").open()

    def go(self, screen_name):
        app = MDApp.get_running_app()
        if not app.acc or not app.slot:
            MDSnackbar(text="계정과 슬롯을 먼저 선택해주세요.").open()
            return
        self.manager.current = screen_name

# ---------- 3. 케릭정보창 (제1원칙 19종 그룹화) ----------
class CharInfoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [제1원칙] 19종 항목 및 4개 그룹 분할
        self.groups = [
            ["이름", "직위", "클랜", "레벨"],
            ["생명력", "기력", "근력"],
            ["힘", "정신력", "재능", "민첩", "건강"],
            ["명중", "공격", "방어", "흡수", "속도"]
        ]
        
        sv = MDScrollView()
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5), size_hint_y=None)
        self.main_layout.bind(minimum_height=self.main_layout.setter('height'))
        
        for g in self.groups:
            for field in g:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(MDLabel(text=field, size_hint_x=0.3, halign="center"))
                tf = MDTextField(halign="center", mode="fill")
                tf.bind(text=lambda instance, value, f=field: self.auto_save(f, value))
                self.inputs[field] = tf
                row.add_widget(tf)
                self.main_layout.add_widget(row)
            self.main_layout.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 비가시적 간격

        self.main_layout.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(0.8,0,0,1), size_hint_x=1, on_release=self.clear_all))
        self.main_layout.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(self.main_layout)
        self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='info'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items():
            tf.text = data.get(k, "")

    def auto_save(self, field, value):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'info', json.dumps(data)))
        conn.commit()

    def clear_all(self, *args):
        for tf in self.inputs.values(): tf.text = ""

# ---------- 4. 케릭장비창 (11종 고정) ----------
class EquipScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(45))
            row.add_widget(MDLabel(text=item, size_hint_x=0.4, halign="center"))
            tf = MDTextField(halign="center")
            tf.bind(text=lambda instance, value, i=item: self.auto_save(i, value))
            self.inputs[item] = tf
            row.add_widget(tf)
            l.add_widget(row)
        
        l.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(0.8,0,0,1), size_hint_x=1, on_release=lambda x: [setattr(tf, 'text', '') for tf in self.inputs.values()]))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='equ'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def auto_save(self, field, value):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'equ', json.dumps(data)))
        conn.commit()

# ---------- 5. 인벤토리창 (수정모드) ----------
class InvenScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="인벤토리 (20칸)", halign="center"))
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        grid.bind(minimum_height=grid.setter('height'))
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"아이템 Slot {i}", halign="center")
            tf.bind(text=lambda instance, value, idx=i: self.auto_save(idx, value))
            self.inputs[i] = tf
            grid.add_widget(tf)
        sv.add_widget(grid)
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='inv'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for i, tf in self.inputs.items(): tf.text = data.get(str(i), "")

    def auto_save(self, idx, value):
        app = MDApp.get_running_app()
        data = {str(k): tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'inv', json.dumps(data)))
        conn.commit()

# ---------- 6. 사진 선택창 ----------
class PhotoScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진 관리", halign="center"))
        self.photo_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(10))
        self.photo_list.bind(minimum_height=self.photo_list.setter('height'))
        sv = MDScrollView()
        sv.add_widget(self.photo_list)
        l.add_widget(MDRaisedButton(text="사진 추가 (갤러리)", size_hint_x=1, on_release=self.add_photo))
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()

    def refresh(self):
        self.photo_list.clear_widgets()
        app = MDApp.get_running_app()
        cur.execute("SELECT path FROM photos WHERE acc=? AND slot=?", (app.acc, app.slot))
        for (path,) in cur.fetchall():
            row = BoxLayout(size_hint_y=None, height=dp(45))
            row.add_widget(MDLabel(text=os.path.basename(path)))
            btn = MDRaisedButton(text="삭제", md_bg_color=(0.8,0,0,1))
            btn.bind(on_release=lambda x, p=path: self.del_photo(p))
            row.add_widget(btn)
            self.photo_list.add_widget(row)

    def add_photo(self, *args):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.on_photo_selected, multiple=True)
        except: MDSnackbar(text="파일 선택을 지원하지 않는 환경입니다.").open()

    def on_photo_selected(self, selection):
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
