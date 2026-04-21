import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
# [전수검사] S26 울트라 최적화: 키보드 가림 방지
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

# [오류해결] 폰트 로딩 최우선 순위 배치
FONT_FILE = get_path("font.ttf")
if FONT_FILE:
    try:
        LabelBase.register(name="KoreanFont", fn_regular=FONT_FILE)
    except: pass

# ---------- DB 초기화 (커밋 누락 수정) ----------
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
    conn.commit()
except:
    conn = None

# ---------- 메인 앱 엔진 ----------
class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # [오류해결] 모든 텍스트 스타일에 한글 폰트 강제 주입 (일부 깨짐 방지)
        if FONT_FILE:
            for style in list(self.theme_cls.font_styles.keys()):
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        
        # 6개 전체 화면 등록
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        Clock.schedule_once(self.run_diag, 2)
        return self.sm

    def run_diag(self, dt):
        errors = []
        if not FONT_FILE: errors.append("❌ font.ttf 누락")
        if not get_path("bg.png"): errors.append("⚠️ bg.png 누락")
        if not get_path("bg_sword.png"): errors.append("⚠️ bg_sword.png 누락")
        
        msg = "시스템 정상 (114번 기반 안정화 완료)" if not errors else "\n".join(errors)
        self.diag = MDDialog(title="🛡️ 자가 진단 보고", text=msg, 
                             buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.diag.dismiss())])
        self.diag.open()

# ---------- 1. 계정 화면 ----------
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
        
        self.search = MDTextField(hint_text="🔍 계정 검색", mode="rectangle")
        self.search.bind(text=lambda i, v: self.refresh(v))
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="새 계정 ID")
        l.add_widget(self.input)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=self.do_save))
        btns.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=self.do_delete))
        l.add_widget(btns)

        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        sv = MDScrollView(); sv.add_widget(self.list_layout); l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()
    def refresh(self, q=""):
        self.list_layout.clear_widgets()
        if not conn: return
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+q+'%',))
        for (n,) in cur.fetchall():
            btn = MDRectangleFlatButton(text=n, size_hint_x=1)
            btn.bind(on_release=lambda x, name=n: self.go_sel(name))
            self.list_layout.add_widget(btn)

    def go_sel(self, name):
        MDApp.get_running_app().acc = name
        self.manager.current = 'sel'

    def do_save(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,))
            conn.commit(); self.refresh(); self.input.text=""
            MDSnackbar(text="계정이 저장되었습니다.").open()

    def do_delete(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("DELETE FROM accounts WHERE name=?", (n,))
            conn.commit(); self.refresh(); self.input.text=""
            MDSnackbar(text="계정이 삭제되었습니다.").open()

# ---------- 2. 케릭 선택창 ----------
class CharSelectScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_added"):
            bg = get_path("bg_sword.png")
            if bg: self.add_widget(Image(source=bg, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_added = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.info = MDLabel(text="슬롯을 선택하세요", halign="center", font_style="H6")
        l.add_widget(self.info)

        grid = GridLayout(cols=2, spacing=dp(15), size_hint_y=0.5)
        for i in range(1, 7):
            b = MDRaisedButton(text=f"Slot {i}", size_hint=(1, 1))
            b.bind(on_release=lambda x, s=i: self.set_slot(s))
            grid.add_widget(b)
        l.add_widget(grid)

        # [지시사항] 하단 4개 이동 버튼
        menu = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        for n, sc in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            btn = MDRaisedButton(text=n, size_hint_x=0.25)
            btn.bind(on_release=lambda x, t=sc: self.go_sc(t))
            menu.add_widget(btn)
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def set_slot(self, s):
        app = MDApp.get_running_app()
        app.slot = s
        self.info.text = f"계정: {app.acc} / Slot: {s}"
        MDSnackbar(text=f"{s}번 슬롯 선택됨").open()

    def go_sc(self, target):
        if not MDApp.get_running_app().slot:
            MDSnackbar(text="슬롯을 먼저 선택해주세요.").open()
            return
        self.manager.current = target

# ---------- 3. 케릭 정보창 (19종) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        self.fields = [
            ["이름", "직위", "클랜", "레벨"], ["생명력", "기력", "근력"],
            ["힘", "정신력", "재능", "민첩", "건강"], ["명중", "공격", "방어", "흡수", "속도"]
        ]
        sv = MDScrollView()
        self.cont = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(2), size_hint_y=None)
        self.cont.bind(minimum_height=self.cont.setter('height'))
        
        for g in self.fields:
            for f in g:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(MDLabel(text=f, size_hint_x=0.3))
                tf = MDTextField(mode="fill")
                self.inputs[f] = tf
                row.add_widget(tf)
                self.cont.add_widget(row)
            self.cont.add_widget(BoxLayout(size_hint_y=None, height=dp(15)))

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=lambda x: self.save_data()))
        btns.add_widget(MDRaisedButton(text="초기화", size_hint_x=0.5, md_bg_color=(1,0,0,1), on_release=lambda x: self.clear_data()))
        self.cont.add_widget(btns)
        self.cont.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(self.cont); self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='info'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def save_data(self):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'info', json.dumps(data)))
        conn.commit(); MDSnackbar(text="정보가 저장되었습니다.").open()

    def clear_data(self):
        for tf in self.inputs.values(): tf.text = ""
        MDSnackbar(text="내용이 초기화되었습니다.").open()

# ---------- 4. 장비창 (11종) ----------
class EquipScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        sv = MDScrollView()
        cont = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint_y=None)
        cont.bind(minimum_height=cont.setter('height'))
        
        for f in items:
            row = BoxLayout(size_hint_y=None, height=dp(50))
            row.add_widget(MDLabel(text=f, size_hint_x=0.3))
            tf = MDTextField(mode="rectangle")
            self.inputs[f] = tf
            row.add_widget(tf)
            cont.add_widget(row)
            
        cont.add_widget(MDRaisedButton(text="저장", size_hint_x=1, on_release=lambda x: self.save_eq()))
        cont.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(cont); self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='equ'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def save_eq(self):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'equ', json.dumps(data)))
        conn.commit(); MDSnackbar(text="장비가 저장되었습니다.").open()

# ---------- 5. 인벤토리창 (20줄) ----------
class InvenScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(10))
        grid.bind(minimum_height=grid.setter('height'))
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"Slot {i}")
            self.inputs[i] = tf
            grid.add_widget(tf)
        grid.add_widget(MDRaisedButton(text="저장", size_hint_x=1, on_release=lambda x: self.save_inv()))
        grid.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(grid); self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='inv'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for i, tf in self.inputs.items(): tf.text = data.get(str(i), "")

    def save_inv(self):
        app = MDApp.get_running_app()
        data = {str(k): tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'inv', json.dumps(data)))
        conn.commit(); MDSnackbar(text="인벤토리가 저장되었습니다.").open()

# ---------- 6. 사진 관리창 ----------
class PhotoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.img = Image(source="", size_hint_y=0.7)
        l.add_widget(self.img)
        l.add_widget(MDRaisedButton(text="사진 추가", size_hint_x=1, on_release=self.pick))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def pick(self, *a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda s: setattr(self.img, 'source', s[0] if s else ""))
        except: MDSnackbar(text="탐색기 오류").open()

if __name__ == '__main__':
    try:
        PristonTaleApp().run()
    except Exception:
        with open(os.path.join(BASE_DIR, "error_log.txt"), "w") as f:
            f.write(traceback.format_exc())
