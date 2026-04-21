import os
import sys
import json
import traceback
import sqlite3

from kivy.config import Config
# [진단] 안드로이드 키보드 가림 및 튕김 방지 설정
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

# ---------- [폰트 엔진 최우선 실행] ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

# [ㅁㅁ현상 완전박멸] 폰트 경로 강제 지정
FONT_PATH = os.path.join(BASE_DIR, "font.ttf")
if not os.path.exists(FONT_PATH):
    FONT_PATH = resource_find("font.ttf")

if FONT_PATH:
    LabelBase.register(name="KoreanFont", fn_regular=FONT_PATH)

DB_PATH = os.path.join(BASE_DIR, "pt1_master.db")

# ---------- DB 초기화 (절대 규칙 데이터베이스) ----------
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
    conn.commit()
except:
    conn = None

# ---------- 메인 앱 (PristonTale) ----------
class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # 모든 위젯에 폰트 강제 이식
        if FONT_PATH:
            for style in list(self.theme_cls.font_styles.keys()):
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        
        # 6대 화면 등록 (절대 규칙)
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # 앱 시작 즉시 "전체 검색 자가 진단" 실행
        Clock.schedule_once(self.run_full_system_diagnosis, 1.5)
        return self.sm

    def show_popup(self, title, text):
        """저장/삭제 시 알림 팝업 (가장 안정적인 방식)"""
        d = MDDialog(title=title, text=text, buttons=[MDRaisedButton(text="확인", on_release=lambda x: d.dismiss())])
        d.open()

    def run_full_system_diagnosis(self, dt):
        """올라운드 자가 진단 엔진: 모든 오류를 하나로 모아 표시"""
        reports = []
        
        # 1. 폰트 체크
        if not FONT_PATH or not os.path.exists(FONT_PATH):
            reports.append("❌ [폰트] font.ttf 파일이 경로에 없습니다.")
        else:
            reports.append("✅ [폰트] 시스템 폰트 정상 등록됨.")

        # 2. 배경 이미지 체크
        bg1 = os.path.join(BASE_DIR, "bg.png")
        bg2 = os.path.join(BASE_DIR, "bg_sword.png")
        if not os.path.exists(bg1): reports.append("⚠️ [이미지] bg.png 파일 누락")
        if not os.path.exists(bg2): reports.append("⚠️ [이미지] bg_sword.png 파일 누락")
        
        # 3. DB 체크
        if not conn: reports.append("🚨 [DB] 데이터베이스 연결 불가")
        else: reports.append("✅ [DB] 캐릭터 데이터베이스 연결 성공")

        # 결과 리포트 출력
        msg = "\n".join(reports)
        self.show_popup("🛡️ 올라운드 자가 진단 보고", msg)

# ---------- 1. 계정 화면 (PristonTale) ----------
class AccountScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg"):
            p = os.path.join(BASE_DIR, "bg.png")
            if os.path.exists(p):
                self.add_widget(Image(source=p, opacity=0.15, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="PristonTale", halign="center", font_style="H4"))
        
        self.search = MDTextField(hint_text="🔍 계정 검색", mode="rectangle")
        self.search.bind(text=lambda i, v: self.refresh(v))
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="새 계정 ID")
        l.add_widget(self.input)

        b_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        b_box.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=self.do_save))
        b_box.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=self.do_delete))
        l.add_widget(b_box)

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
            btn.bind(on_release=lambda x, name=n: self.go_char(name))
            self.list_layout.add_widget(btn)

    def go_char(self, n):
        MDApp.get_running_app().acc = n
        self.manager.current = 'sel'

    def do_save(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,))
            conn.commit(); self.refresh(); self.input.text=""
            MDApp.get_running_app().show_popup("성공", "계정이 저장되었습니다.")

    def do_delete(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("DELETE FROM accounts WHERE name=?", (n,))
            conn.commit(); self.refresh(); self.input.text=""
            MDApp.get_running_app().show_popup("성공", "계정이 삭제되었습니다.")

# ---------- 2. 캐릭터 선택창 ----------
class CharSelectScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg"):
            p = os.path.join(BASE_DIR, "bg_sword.png")
            if os.path.exists(p):
                self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.info = MDLabel(text="슬롯을 선택해 주세요", halign="center", font_style="H6")
        l.add_widget(self.info)

        grid = GridLayout(cols=2, spacing=dp(15), size_hint_y=0.5)
        for i in range(1, 7):
            b = MDRaisedButton(text=f"슬롯 {i}", size_hint=(1, 1))
            b.bind(on_release=lambda x, s=i: self.select_slot(s))
            grid.add_widget(b)
        l.add_widget(grid)

        # [지시사항] 하단 4개 세부 창 이동
        menu = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        for n, t in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            btn = MDRaisedButton(text=n, size_hint_x=0.25)
            btn.bind(on_release=lambda x, target=t: self.move_to(target))
            menu.add_widget(btn)
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def select_slot(self, s):
        app = MDApp.get_running_app()
        app.slot = s
        self.info.text = f"계정: {app.acc} / 슬롯: {s}"
        app.show_popup("슬롯 선택", f"{s}번 캐릭터 슬롯이 선택되었습니다.")

    def move_to(self, target):
        if not MDApp.get_running_app().slot:
            MDApp.get_running_app().show_popup("알림", "슬롯을 먼저 선택해야 합니다.")
            return
        self.manager.current = target

# ---------- 3. 캐릭터 정보창 (18종 절대 규칙) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # 절대 규칙: 목록 박제
        self.fields = ["이름","직위","클랜","레벨","생명력","기력","근력","힘","정신력","재능","민첩","건강","명중","공격","방어","흡수","속도","메모"]
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(2), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for f in self.fields:
            row = BoxLayout(size_hint_y=None, height=dp(45))
            row.add_widget(MDLabel(text=f, size_hint_x=0.3))
            tf = MDTextField(mode="fill")
            self.inputs[f] = tf
            row.add_widget(tf)
            l.add_widget(row)

        l.add_widget(MDRaisedButton(text="정보 저장", size_hint_x=1, on_release=lambda x: self.save()))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l); self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='info'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def save(self):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'info', json.dumps(data)))
        conn.commit()
        app.show_popup("저장 완료", "캐릭터 정보가 저장되었습니다.")

# ---------- 4. 캐릭터 장비창 (11종 절대 규칙) ----------
class EquipScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        self.eq_list = ["한손무기","두손무기","갑옷","방패","장갑","부츠","암릿","링1","링2","아뮬렛","기타"]
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        for e in self.eq_list:
            row = BoxLayout(size_hint_y=None, height=dp(50))
            row.add_widget(MDLabel(text=e, size_hint_x=0.3))
            tf = MDTextField(mode="rectangle")
            self.inputs[e] = tf
            row.add_widget(tf)
            l.add_widget(row)
        l.add_widget(MDRaisedButton(text="장비 저장", size_hint_x=1, on_release=lambda x: self.save()))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l); self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='equ'", (app.acc, app.slot))
        res = cur.fetchone()
        data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def save(self):
        app = MDApp.get_running_app()
        data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'equ', json.dumps(data)))
        conn.commit()
        app.show_popup("저장 완료", "장비 정보가 저장되었습니다.")

# ---------- 5. 인벤토리 및 6. 사진 (기본 구조) ----------
class InvenScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(10))
        grid.bind(minimum_height=grid.setter('height'))
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"슬롯 {i}")
            self.inputs[i] = tf
            grid.add_widget(tf)
        grid.add_widget(MDRaisedButton(text="저장", size_hint_x=1, on_release=self.save))
        grid.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(grid); self.add_widget(sv)

    def save(self, *a):
        app = MDApp.get_running_app()
        data = {str(k): tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'inv', json.dumps(data)))
        conn.commit()
        app.show_popup("완료", "인벤토리 데이터가 저장되었습니다.")

class PhotoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.img = Image(source="", size_hint_y=0.7)
        l.add_widget(self.img)
        l.add_widget(MDRaisedButton(text="사진 선택", size_hint_x=1, on_release=self.pick))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def pick(self, *a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda s: setattr(self.img, 'source', s[0] if s else ""))
        except: MDApp.get_running_app().show_popup("오류", "파일 탐색기를 열 수 없습니다.")

if __name__ == '__main__':
    try:
        PristonTaleApp().run()
    except Exception:
        with open(os.path.join(BASE_DIR, "error_log.txt"), "w") as f:
            f.write(traceback.format_exc())
