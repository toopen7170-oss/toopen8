import os
import sqlite3
import json
import traceback
from kivy.config import Config

# [전수검사] S26 울트라 최적화: 자판 대응 및 디스플레이 설정
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

# ---------- [경로 및 권한 진단] ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
    from android.permissions import request_permissions, Permission
    # [원칙] 사진 선택을 위한 권한 자동 요청
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "pt1_master_final.db")

def get_res(file):
    p = resource_find(file)
    return p if p else (file if os.path.exists(file) else None)

# [진단] 폰트 사전 등록 (ㅁㅁ 깨짐 방지)
FONT_FILE = get_res("font.ttf")
if FONT_FILE:
    LabelBase.register(name="KoreanFont", fn_regular=FONT_FILE)

# ---------- DB 초기화 및 안정화 ----------
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
    conn.commit()
except Exception as e:
    conn = None

# ---------- 메인 앱 엔진 ----------
class PristonTaleApp(MDApp):
    def build(self):
        self.icon = get_res("icon.png")
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # [전수검사] 전역 폰트 강제 주입
        if FONT_FILE:
            for style in list(self.theme_cls.font_styles.keys()):
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        
        # [제1원칙] 6대 화면 구성
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # [자가 진단] 구동 직후 전체 점검
        Clock.schedule_once(self.run_diagnosis, 0.5)
        return self.sm

    def run_diagnosis(self, dt):
        issues = []
        if not FONT_FILE: issues.append("❌ font.ttf 누락")
        if not get_res("bg.png"): issues.append("❌ bg.png 누락")
        if not get_res("icon.png"): issues.append("❌ icon.png 누락")
        if not conn: issues.append("🚨 DB 연결 실패")
        
        msg = "✅ 시스템 무결성 검사 완료: 정상" if not issues else "\n".join(issues)
        self.diag = MDDialog(title="🛡️ 자가 진단 보고", text=msg, 
                             buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.diag.dismiss())])
        self.diag.open()

# ---------- 1. 계정 생성창 (원칙 준수) ----------
class AccountScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_set"):
            bg_p = get_res("bg.png")
            if bg_p: self.add_widget(Image(source=bg_p, opacity=0.3, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_set = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="Priston Tale", halign="center", font_style="H4"))
        
        self.search = MDTextField(hint_text="🔍 계정 전체 검색바", mode="rectangle")
        self.search.bind(text=self.filter_list)
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="새 계정ID 입력")
        l.add_widget(self.input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_row.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=self.ask_save))
        btn_row.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=self.ask_delete))
        l.add_widget(btn_row)

        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        sv = MDScrollView()
        sv.add_widget(self.list_layout)
        l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()
    def refresh(self, q=""):
        self.list_layout.clear_widgets()
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+q+'%',))
        for (n,) in cur.fetchall():
            b = MDRectangleFlatButton(text=n, size_hint_x=1)
            b.bind(on_release=lambda x, name=n: self.go_next(name))
            self.list_layout.add_widget(b)

    def filter_list(self, i, v): self.refresh(v)
    def go_next(self, n):
        MDApp.get_running_app().acc = n
        self.manager.current = 'sel'

    def ask_save(self, *a):
        self.dialog = MDDialog(title="저장 확인", text="계정을 저장하시겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog.dismiss()),
            MDRaisedButton(text="확인", on_release=self.do_save)])
        self.dialog.open()

    def do_save(self, *a):
        n = self.input.text.strip()
        if n: cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,)); conn.commit(); self.refresh(); self.input.text=""
        self.dialog.dismiss()

    def ask_delete(self, *a):
        self.dialog = MDDialog(title="삭제 확인", text="계정을 삭제하시겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog.dismiss()),
            MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), on_release=self.do_del)])
        self.dialog.open()

    def do_del(self, *a):
        n = self.input.text.strip()
        cur.execute("DELETE FROM accounts WHERE name=?", (n,)); conn.commit(); self.refresh(); self.input.text=""
        self.dialog.dismiss()

# ---------- 2. 케릭 선택창 (6개 슬롯 고정) ----------
class CharSelectScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.label = MDLabel(text="캐릭터 슬롯을 선택하세요", halign="center", font_style="H6")
        l.add_widget(self.label)

        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.6)
        for i in range(1, 7):
            btn = MDRaisedButton(text=f"슬롯 {i}", size_hint=(1,1))
            btn.bind(on_release=lambda x, s=i: self.set_slot(s))
            grid.add_widget(btn)
        l.add_widget(grid)

        menu = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        for n, sn in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            b = MDRaisedButton(text=n, size_hint_x=0.25)
            b.bind(on_release=lambda x, s=sn: self.go_to(s))
            menu.add_widget(b)
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def set_slot(self, s):
        MDApp.get_running_app().slot = s
        self.label.text = f"계정: {MDApp.get_running_app().acc} / 슬롯: {s}"
        MDSnackbar(text=f"{s}번 슬롯 선택됨").open()

    def go_to(self, sn):
        if not MDApp.get_running_app().slot:
            MDSnackbar(text="슬롯을 먼저 선택하세요.").open()
            return
        self.manager.current = sn

# ---------- 3. 케릭 정보창 (19종 그룹화 원칙) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [제1원칙] 19종 항목 그룹화
        self.groups = [
            [('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
            [('생명력', ''), ('기력', ''), ('근력', '')],
            [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
            [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]
        ]
        
        l = BoxLayout(orientation='vertical', padding=dp(10))
        sv = MDScrollView()
        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        container.bind(minimum_height=container.setter('height'))
        
        for group in self.groups:
            for field, _ in group:
                row = BoxLayout(size_hint_y=None, height=dp(55), padding=[dp(10), dp(5)])
                row.add_widget(MDLabel(text=field, size_hint_x=0.3))
                # [전수검사] 중앙 정렬 및 위아래 고정
                tf = MDTextField(halign="center", mode="fill", fill_color_normal=(0,0,0,0.1))
                tf.bind(text=lambda inst, val, f=field: self.auto_save(f, val))
                self.inputs[field] = tf
                row.add_widget(tf)
                container.add_widget(row)
            # [원칙] 한칸 띄어주기 (화면엔 안보임)
            container.add_widget(BoxLayout(size_hint_y=None, height=dp(20)))

        # 하단 버튼
        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_box.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=0.5, on_release=self.ask_clear))
        btn_box.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=0.5, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        container.add_widget(btn_box)
        
        sv.add_widget(container)
        l.add_widget(sv)
        self.add_widget(l)

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
        self.dialog = MDDialog(title="삭제 확인", text="정보를 전체 삭제하시겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog.dismiss()),
            MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), on_release=self.do_clear)])
        self.dialog.open()

    def do_clear(self, *a):
        for tf in self.inputs.values(): tf.text = ""
        self.dialog.dismiss()

# ---------- 4. 케릭 장비창 (11종 원칙) ----------
class EquipScreen(CharInfoScreen):
    def __init__(self, **kw):
        super(CharInfoScreen, self).__init__(**kw)
        self.inputs = {}
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        l = BoxLayout(orientation='vertical', padding=dp(10))
        sv = MDScrollView()
        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        container.bind(minimum_height=container.setter('height'))
        
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(55))
            row.add_widget(MDLabel(text=item, size_hint_x=0.3, halign="center"))
            tf = MDTextField(halign="center", mode="rectangle")
            tf.bind(text=lambda inst, val, f=item: self.auto_save_eq(f, val))
            self.inputs[item] = tf
            row.add_widget(tf)
            container.add_widget(row)
        
        container.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=self.ask_clear))
        container.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(container)
        l.add_widget(sv)
        self.add_widget(l)

    def auto_save_eq(self, f, v):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'equ', json.dumps(data)))
        conn.commit()

# ---------- 5. 인벤토리창 (20줄 원칙) ----------
class InvenScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        l = BoxLayout(orientation='vertical', padding=dp(10))
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        grid.bind(minimum_height=grid.setter('height'))
        
        for i in range(1, 21):
            row = BoxLayout(size_hint_y=None, height=dp(50))
            tf = MDTextField(hint_text=f"Slot {i}", halign="center")
            tf.bind(text=lambda inst, val, idx=i: self.auto_save_inv(idx, val))
            self.inputs[i] = tf
            grid.add_widget(tf)
            
        grid.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=self.ask_clear))
        grid.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(grid)
        l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='inv'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for i, tf in self.inputs.items(): tf.text = data.get(str(i), "")

    def auto_save_inv(self, idx, v):
        app = MDApp.get_running_app()
        data = {str(k): tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'inv', json.dumps(data)))
        conn.commit()

    def ask_clear(self, *a):
        for tf in self.inputs.values(): tf.text = ""

# ---------- 6. 사진 선택창 (권한 및 업로드 원칙) ----------
class PhotoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진 선택 매니저", halign="center", font_style="H5"))
        
        self.img = Image(source="", size_hint_y=0.6)
        l.add_widget(self.img)
        
        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_box.add_widget(MDRaisedButton(text="업로드/선택", size_hint_x=0.5, on_release=self.pick_img))
        btn_box.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(1,0,0,1), on_release=self.ask_del))
        l.add_widget(btn_box)
        
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def pick_img(self, *a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.on_pick, multiple=True)
        except: MDSnackbar(text="S26 권한을 확인하세요.").open()

    def on_pick(self, selection):
        if selection: self.img.source = selection[0]; MDSnackbar(text="사진 로드 완료").open()

    def ask_del(self, *a):
        self.img.source = ""; MDSnackbar(text="사진 삭제 완료").open()

if __name__ == '__main__':
    try:
        PristonTaleApp().run()
    except Exception:
        with open(os.path.join(BASE_DIR, "pt1_crash.txt"), "w") as f:
            f.write(traceback.format_exc())
