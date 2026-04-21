import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
# [전수검사] S26 울트라 최적화 및 키보드 간섭 방지
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

# [오류해결] 폰트 엔진 강제 초기화 (ㅁㅁ 현상 완전 박멸)
FONT_FILE = get_path("font.ttf")
if FONT_FILE:
    try:
        LabelBase.register(name="KoreanFont", fn_regular=FONT_FILE)
    except: pass

# ---------- DB 초기화 (안정성 강화) ----------
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
    conn.commit()
except:
    conn = None

# ---------- 메인 앱 엔진 (PristonTale) ----------
class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # [절대규칙] 모든 위젯 스타일에 한글 폰트 강제 주입
        if FONT_FILE:
            for style in list(self.theme_cls.font_styles.keys()):
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        
        # [절대규칙] 6개 전체 화면 등록 (절대 삭제/수정 금지)
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # 앱 구동 2초 후 올라운드 진단 실행
        Clock.schedule_once(self.run_all_diag, 2)
        return self.sm

    def run_all_diag(self, dt):
        error_report = []
        if not FONT_FILE: error_report.append("❌ font.ttf 폰트 파일 누락")
        if not get_path("bg.png"): error_report.append("⚠️ bg.png 배경 이미지 누락")
        if not get_path("bg_sword.png"): error_report.append("⚠️ bg_sword.png 이미지 누락")
        if not conn: error_report.append("🚨 DB 연결 실패")
        
        if error_report:
            msg = "\n".join(error_report)
            self.diag = MDDialog(
                title="🛡️ 올라운드 시스템 진단 보고",
                text=f"발견된 이슈:\n\n{msg}",
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.diag.dismiss())]
            )
            self.diag.open()

# ---------- 1. 계정 화면 (PristonTale) ----------
class AccountScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_added"):
            bg = get_path("bg.png")
            if bg: self.add_widget(Image(source=bg, opacity=0.15, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_added = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        # [지시사항] 이름 변경
        l.add_widget(MDLabel(text="PristonTale", halign="center", font_style="H4"))
        
        self.search = MDTextField(hint_text="🔍 계정 검색", mode="rectangle")
        self.search.bind(text=lambda i, v: self.refresh_list(v))
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="새로운 계정 ID 입력")
        l.add_widget(self.input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_box.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=self.save_acc))
        btn_box.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=self.delete_acc))
        l.add_widget(btn_box)

        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        sv = MDScrollView(); sv.add_widget(self.list_layout); l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.refresh_list()
    def refresh_list(self, query=""):
        self.list_layout.clear_widgets()
        if not conn: return
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+query+'%',))
        for (name,) in cur.fetchall():
            btn = MDRectangleFlatButton(text=name, size_hint_x=1)
            btn.bind(on_release=lambda x, n=name: self.select_acc(n))
            self.list_layout.add_widget(btn)

    def select_acc(self, name):
        MDApp.get_running_app().acc = name
        self.manager.current = 'sel'

    def save_acc(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,))
            conn.commit(); self.refresh_list(); self.input.text=""
            MDSnackbar(text="계정이 정상적으로 저장되었습니다.").open()

    def delete_acc(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("DELETE FROM accounts WHERE name=?", (n,))
            conn.commit(); self.refresh_list(); self.input.text=""
            MDSnackbar(text="계정이 정상적으로 삭제되었습니다.").open()

# ---------- 2. 케릭 선택창 (배경 고정) ----------
class CharSelectScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_added"):
            bg = get_path("bg_sword.png")
            if bg: self.add_widget(Image(source=bg, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_added = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.acc_info = MDLabel(text="슬롯을 선택하세요", halign="center", font_style="H6")
        l.add_widget(self.acc_info)

        grid = GridLayout(cols=2, spacing=dp(15), size_hint_y=0.5)
        for i in range(1, 7):
            b = MDRaisedButton(text=f"Slot {i}", size_hint=(1, 1))
            b.bind(on_release=lambda x, s=i: self.set_slot(s))
            grid.add_widget(b)
        l.add_widget(grid)

        # [지시사항] 하단 4개 이동 버튼
        menu = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        for n, target in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            btn = MDRaisedButton(text=n, size_hint_x=0.25)
            btn.bind(on_release=lambda x, t=target: self.go_next(t))
            menu.add_widget(btn)
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def set_slot(self, s):
        app = MDApp.get_running_app()
        app.slot = s
        self.acc_info.text = f"계정: {app.acc} / 슬롯: {s}"
        MDSnackbar(text=f"{s}번 슬롯이 선택되었습니다.").open()

    def go_next(self, target):
        if not MDApp.get_running_app().slot:
            MDSnackbar(text="슬롯을 먼저 선택해 주세요.").open()
            return
        self.manager.current = target

# ---------- 3. 케릭 정보창 (18종 절대규칙) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [절대규칙] 18개 세부 목록 고정
        self.field_list = [
            "이름", "직위", "클랜", "레벨", "생명력", "기력", "근력", 
            "힘", "정신력", "재능", "민첩", "건강", 
            "명중", "공격", "방어", "흡수", "속도", "기타메모"
        ]
        self.build_ui()

    def build_ui(self):
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for f in self.field_list:
            row = BoxLayout(size_hint_y=None, height=dp(45))
            row.add_widget(MDLabel(text=f, size_hint_x=0.35, halign="center"))
            tf = MDTextField(mode="fill", halign="center")
            self.inputs[f] = tf
            row.add_widget(tf)
            l.add_widget(row)

        l.add_widget(BoxLayout(size_hint_y=None, height=dp(20)))
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_row.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=lambda x: self.save_data()))
        btn_row.add_widget(MDRaisedButton(text="초기화", size_hint_x=0.5, md_bg_color=(1,0,0,1), on_release=lambda x: self.clear_fields()))
        l.add_widget(btn_row)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l); self.add_widget(sv)

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
        conn.commit(); MDSnackbar(text="정보가 성공적으로 저장되었습니다.").open()

    def clear_fields(self):
        for tf in self.inputs.values(): tf.text = ""

# ---------- 4. 장비창 (11종 절대규칙) ----------
class EquipScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [절대규칙] 11개 세부 목록 고정
        self.eq_list = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타장비"]
        self.build_ui()

    def build_ui(self):
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        for f in self.eq_list:
            row = BoxLayout(size_hint_y=None, height=dp(50))
            row.add_widget(MDLabel(text=f, size_hint_x=0.35))
            tf = MDTextField(mode="rectangle")
            self.inputs[f] = tf
            row.add_widget(tf)
            l.add_widget(row)
        
        l.add_widget(MDRaisedButton(text="장비 저장", size_hint_x=1, on_release=lambda x: self.save_eq()))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l); self.add_widget(sv)

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
        conn.commit(); MDSnackbar(text="장비 정보가 저장되었습니다.").open()

# ---------- 5. 인벤토리 (20줄 고정) ----------
class InvenScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(15))
        grid.bind(minimum_height=grid.setter('height'))
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"아이템 슬롯 {i}", mode="line")
            self.inputs[i] = tf
            grid.add_widget(tf)
        grid.add_widget(MDRaisedButton(text="인벤토리 저장", size_hint_x=1, on_release=lambda x: self.save_inv()))
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

# ---------- 6. 사진 관리 ----------
class PhotoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.img_display = Image(source="", size_hint_y=0.7)
        l.add_widget(self.img_display)
        l.add_widget(MDRaisedButton(text="사진 불러오기", size_hint_x=1, on_release=self.open_finder))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def open_finder(self, *a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.handle_selection)
        except: MDSnackbar(text="탐색기 실행 불가").open()

    def handle_selection(self, selection):
        if selection: self.img_display.source = selection[0]

if __name__ == '__main__':
    try:
        PristonTaleApp().run()
    except Exception:
        with open(os.path.join(BASE_DIR, "error_log.txt"), "w") as f:
            f.write(traceback.format_exc())
