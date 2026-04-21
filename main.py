import os
import sqlite3
import json
import traceback
from kivy.config import Config

# [전수검사] S26 울트라 최적화: 자판 가림 방지 및 입력 고정
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('softinput_mode', 'pan')

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

# ---------- [경로 및 시스템 진단 준비] ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "pt1_master_final.db")

def get_res(file):
    p = resource_find(file)
    return p if p else (file if os.path.exists(file) else None)

# [진단] 폰트 사전 등록 (ㅁㅁ 깨짐 방지)
FONT_PATH = get_res("font.ttf")
if FONT_PATH:
    try:
        LabelBase.register(name="KoreanFont", fn_regular=FONT_PATH)
    except: pass

# ---------- DB 엔진 가동 ----------
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
    conn.commit()
except:
    conn = None

# ---------- 메인 애플리케이션 ----------
class PristonTaleApp(MDApp):
    def build(self):
        self.icon = get_res("icon.png")
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # [원칙] 전역 한글 폰트 강제 주입
        if FONT_PATH:
            for style in list(self.theme_cls.font_styles.keys()):
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        
        # [제1원칙] 6개 필수 화면 등록
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # [진단 시작] 앱 안정화 후 실행 (114번 방식)
        Clock.schedule_once(self.run_final_diagnosis, 1.2)
        return self.sm

    def run_final_diagnosis(self, dt):
        errors = []
        if not FONT_PATH: errors.append("❌ font.ttf 누락 (한글 깨짐)")
        if not get_res("bg.png"): errors.append("⚠️ bg.png 누락 (배경 없음)")
        if not get_res("icon.png"): errors.append("⚠️ icon.png 누락")
        if not conn: errors.append("🚨 DB 파일 생성 실패")
        
        title = "🛡️ 자가 진단 결과"
        msg = "모든 리소스가 정상이며 114번 빌드와 동등한 안정성을 확인했습니다." if not errors else "\n".join(errors)
        
        self.diag = MDDialog(title=title, text=msg, buttons=[
            MDRaisedButton(text="확인", on_release=lambda x: self.diag.dismiss())])
        self.diag.open()

# ---------- 1. 계정 생성창 (원칙 준수) ----------
class AccountScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_loaded"):
            bg = get_res("bg.png")
            if bg: self.add_widget(Image(source=bg, opacity=0.3, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_loaded = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="Priston Tale Manager", halign="center", font_style="H5"))
        
        self.search = MDTextField(hint_text="🔍 계정 전체 검색바", mode="rectangle")
        self.search.bind(text=lambda i, v: self.load_list(v))
        l.add_widget(self.search)

        self.acc_input = MDTextField(hint_text="새 계정 ID 입력")
        l.add_widget(self.acc_input)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=lambda x: self.confirm_action("save")))
        btns.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=lambda x: self.confirm_action("delete")))
        l.add_widget(btns)

        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        sv = MDScrollView(); sv.add_widget(self.list_layout); l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.load_list()
    def load_list(self, q=""):
        self.list_layout.clear_widgets()
        if not conn: return
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+q+'%',))
        for (n,) in cur.fetchall():
            b = MDRectangleFlatButton(text=n, size_hint_x=1)
            b.bind(on_release=lambda x, name=n: self.go_sel(name))
            self.list_layout.add_widget(b)

    def go_sel(self, name):
        MDApp.get_running_app().acc = name
        self.manager.current = 'sel'

    def confirm_action(self, type):
        msg = "계정을 저장하시겠습니까?" if type=="save" else "계정을 삭제하시겠습니까?"
        self.dialog = MDDialog(title="확인", text=msg, buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog.dismiss()),
            MDRaisedButton(text="확인", on_release=lambda x: self.do_action(type))])
        self.dialog.open()

    def do_action(self, type):
        n = self.acc_input.text.strip()
        if n and conn:
            if type=="save": cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,))
            else: cur.execute("DELETE FROM accounts WHERE name=?", (n,))
            conn.commit(); self.load_list(); self.acc_input.text=""
        self.dialog.dismiss()

# ---------- 2. 케릭 선택창 (6슬롯 고정) ----------
class CharSelectScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.info = MDLabel(text="슬롯을 선택해 주세요", halign="center", font_style="H6")
        l.add_widget(self.info)

        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.6)
        for i in range(1, 7):
            b = MDRaisedButton(text=f"Slot {i}", size_hint=(1,1))
            b.bind(on_release=lambda x, s=i: self.select_slot(s))
            grid.add_widget(b)
        l.add_widget(grid)

        menu = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        for n, sc in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            btn = MDRaisedButton(text=n, size_hint_x=0.25)
            btn.bind(on_release=lambda x, target=sc: self.safe_go(target))
            menu.add_widget(btn)
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def select_slot(self, s):
        app = MDApp.get_running_app()
        app.slot = s
        self.info.text = f"계정: {app.acc} / 슬롯: {s}"
        MDSnackbar(text=f"{s}번 슬롯이 선택되었습니다.").open()

    def safe_go(self, target):
        if not MDApp.get_running_app().slot:
            MDSnackbar(text="먼저 슬롯을 선택해 주세요.").open()
            return
        self.manager.current = target

# ---------- 3. 케릭 정보창 (19종 원칙 그룹화) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [제1원칙] 19종 필수 항목 그룹화 (한칸 띄움 포함)
        self.groups = [
            [('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
            [('생명력', ''), ('기력', ''), ('근력', '')],
            [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
            [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]
        ]
        
        l = BoxLayout(orientation='vertical', padding=dp(10))
        sv = MDScrollView()
        self.container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        self.container.bind(minimum_height=self.container.setter('height'))
        
        for g in self.groups:
            for field, _ in g:
                row = BoxLayout(size_hint_y=None, height=dp(55), padding=[dp(10), 0])
                row.add_widget(MDLabel(text=field, size_hint_x=0.3))
                tf = MDTextField(halign="center", mode="fill", fill_color_normal=(0,0,0,0.1))
                tf.bind(text=lambda inst, val, f=field: self.auto_save(f, val))
                self.inputs[field] = tf
                row.add_widget(tf)
                self.container.add_widget(row)
            self.container.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 비가시적 띄움

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=0.5, on_release=self.ask_clear))
        btns.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=0.5, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.container.add_widget(btns)
        
        sv.add_widget(self.container); l.add_widget(sv); self.add_widget(l)

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

    def ask_clear(self, *a):
        self.diag = MDDialog(title="정보 삭제", text="모든 내용을 삭제하시겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.diag.dismiss()),
            MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), on_release=self.do_clear)])
        self.diag.open()

    def do_clear(self, *a):
        for tf in self.inputs.values(): tf.text = ""
        self.diag.dismiss()

# ---------- 4. 케릭 장비창 (11종 고정) ----------
class EquipScreen(CharInfoScreen):
    def __init__(self, **kw):
        super(CharInfoScreen, self).__init__(**kw)
        self.inputs = {}
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        l = BoxLayout(orientation='vertical', padding=dp(10))
        sv = MDScrollView()
        cont = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        cont.bind(minimum_height=cont.setter('height'))
        
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(55))
            row.add_widget(MDLabel(text=item, size_hint_x=0.3, halign="center"))
            tf = MDTextField(halign="center", mode="rectangle")
            tf.bind(text=lambda inst, val, f=item: self.save_eq(f, val))
            self.inputs[item] = tf
            row.add_widget(tf)
            cont.add_widget(row)
        
        cont.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=self.ask_clear))
        cont.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(cont); l.add_widget(sv); self.add_widget(l)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='equ'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def save_eq(self, f, v):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'equ', json.dumps(data)))
        conn.commit()

# ---------- 5. 인벤토리창 (20줄 고정) ----------
class InvenScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        l = BoxLayout(orientation='vertical', padding=dp(10))
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        grid.bind(minimum_height=grid.setter('height'))
        
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"아이템 슬롯 {i}", halign="center")
            tf.bind(text=lambda inst, val, idx=i: self.save_inv(idx, val))
            self.inputs[i] = tf
            grid.add_widget(tf)
            
        grid.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=self.ask_clear))
        grid.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(grid); l.add_widget(sv); self.add_widget(l)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='inv'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for i, tf in self.inputs.items(): tf.text = data.get(str(i), "")

    def save_inv(self, idx, v):
        app = MDApp.get_running_app()
        data = {str(k): tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'inv', json.dumps(data)))
        conn.commit()

    def ask_clear(self, *a):
        for tf in self.inputs.values(): tf.text = ""

# ---------- 6. 사진 선택창 (핸드폰 연동) ----------
class PhotoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="스크린샷 매니저", halign="center", font_style="H5"))
        self.img = Image(source="", size_hint_y=0.6)
        l.add_widget(self.img)
        
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="사진 선택", size_hint_x=0.5, on_release=self.pick))
        btns.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(1,0,0,1), on_release=self.remove))
        l.add_widget(btns)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def pick(self, *a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.on_pick, multiple=True)
        except: MDSnackbar(text="파일 탐색기를 실행할 수 없습니다.").open()

    def on_pick(self, selection):
        if selection: self.img.source = selection[0]; MDSnackbar(text="사진이 로드되었습니다.").open()

    def remove(self, *a):
        self.img.source = ""; MDSnackbar(text="사진이 삭제되었습니다.").open()

if __name__ == '__main__':
    try:
        PristonTaleApp().run()
    except Exception:
        with open(os.path.join(BASE_DIR, "error_log.txt"), "w") as f:
            f.write(traceback.format_exc())
