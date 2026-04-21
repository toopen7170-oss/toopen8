import os
import sys
import json
import traceback
import sqlite3

# [진단 1순위] 앱 시작 즉시 오류 로깅 준비
from kivy.config import Config
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

# ---------- [경로 설정] ----------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DIR, "pt1_master.db")

def get_path(file):
    p = resource_find(file)
    return p if p else (file if os.path.exists(file) else None)

# [폰트 해결] MDApp 시작 전 폰트 선등록
FONT_FILE = get_path("font.ttf")
if FONT_FILE:
    try:
        LabelBase.register(name="KoreanFont", fn_regular=FONT_FILE)
    except Exception as e:
        print(f"Font Reg Error: {e}")

# ---------- DB 초기화 ----------
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
        # [폰트 해결] 모든 테마 스타일에 강제 주입 (일부 깨짐 방지)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        if FONT_FILE:
            for style in list(self.theme_cls.font_styles.keys()):
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        
        # [절대규칙] 6대 화면 고정 등록
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        # [진단 1순위] 앱 실행 1초 후 전체 진단 수행
        Clock.schedule_once(self.run_full_diagnosis, 1)
        return self.sm

    def run_full_diagnosis(self, dt):
        """올라운드 전체검색 자가 진단 시스템"""
        diags = []
        
        # 1. 폰트 점검
        if not FONT_FILE: diags.append("❌ [폰트] font.ttf 파일을 찾을 수 없습니다.")
        else: diags.append("✅ [폰트] font.ttf 로드 성공")
            
        # 2. 리소스 점검
        if not get_path("bg.png"): diags.append("⚠️ [이미지] bg.png 누락")
        if not get_path("bg_sword.png"): diags.append("⚠️ [이미지] bg_sword.png 누락")
        
        # 3. 데이터베이스 점검
        if not conn: diags.append("🚨 [DB] 데이터베이스 연결 실패")
        else: diags.append("✅ [DB] pt1_master.db 정상 작동")

        # 4. 화면 및 절대규칙 점검
        screens = self.sm.screen_names
        if len(screens) < 6: diags.append(f"❌ [화면] 등록된 화면 부족 ({len(screens)}/6)")
        else: diags.append("✅ [화면] 6개 전체 화면 정상 등록")

        # 전체 결과 출력
        msg = "\n".join(diags)
        self.diag_dialog = MDDialog(
            title="🛡️ 올라운드 전수 검사 결과",
            text=msg,
            buttons=[MDRaisedButton(text="시스템 시작", on_release=lambda x: self.diag_dialog.dismiss())]
        )
        self.diag_dialog.open()

# ---------- 1. 계정 화면 (PristonTale) ----------
class AccountScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_done"):
            bg = get_path("bg.png")
            if bg: self.add_widget(Image(source=bg, opacity=0.2, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_done = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        # [이름 변경]
        l.add_widget(MDLabel(text="PristonTale", halign="center", font_style="H4", theme_text_color="Primary"))
        
        self.search = MDTextField(hint_text="🔍 계정 검색 (입력 시 자동 필터)", mode="rectangle")
        self.search.bind(text=lambda i, v: self.refresh(v))
        l.add_widget(self.search)

        self.input = MDTextField(hint_text="새 계정 ID 입력")
        l.add_widget(self.input)

        b_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        b_box.add_widget(MDRaisedButton(text="계정 저장", size_hint_x=0.5, on_release=self.save))
        b_box.add_widget(MDRaisedButton(text="계정 삭제", size_hint_x=0.5, md_bg_color=(0.8,0,0,1), on_release=self.delete))
        l.add_widget(b_box)

        self.list_view = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.list_view.bind(minimum_height=self.list_view.setter('height'))
        sv = MDScrollView(); sv.add_widget(self.list_view); l.add_widget(sv)
        self.add_widget(l)

    def on_pre_enter(self): self.refresh()
    def refresh(self, q=""):
        self.list_view.clear_widgets()
        if not conn: return
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+q+'%',))
        for (n,) in cur.fetchall():
            btn = MDRectangleFlatButton(text=n, size_hint_x=1)
            btn.bind(on_release=lambda x, name=n: self.go_next(name))
            self.list_view.add_widget(btn)

    def go_next(self, n):
        MDApp.get_running_app().acc = n
        self.manager.current = 'sel'

    def save(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,))
            conn.commit(); self.refresh(); self.input.text=""
            MDSnackbar(text="[완료] 계정이 저장되었습니다.").open()

    def delete(self, *a):
        n = self.input.text.strip()
        if n and conn:
            cur.execute("DELETE FROM accounts WHERE name=?", (n,))
            conn.commit(); self.refresh(); self.input.text=""
            MDSnackbar(text="[완료] 계정이 삭제되었습니다.").open()

# ---------- 2. 케릭 선택창 ----------
class CharSelectScreen(Screen):
    def on_enter(self):
        if not hasattr(self, "bg_done"):
            bg = get_path("bg_sword.png")
            if bg: self.add_widget(Image(source=bg, allow_stretch=True, keep_ratio=False), index=len(self.children))
            self.bg_done = True

    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.status = MDLabel(text="사용할 캐릭터 슬롯을 선택하세요", halign="center", font_style="H6")
        l.add_widget(self.status)

        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.5)
        for i in range(1, 7):
            btn = MDRaisedButton(text=f"캐릭터 슬롯 {i}", size_hint=(1, 1))
            btn.bind(on_release=lambda x, s=i: self.select_slot(s))
            grid.add_widget(btn)
        l.add_widget(grid)

        # 4개 세부 창 버튼
        menu = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        for n, sc in [("정보","info"), ("장비","equ"), ("인벤","inv"), ("사진","pho")]:
            b = MDRaisedButton(text=n, size_hint_x=0.25)
            b.bind(on_release=lambda x, target=sc: self.go_target(target))
            menu.add_widget(b)
        l.add_widget(menu)
        l.add_widget(MDRectangleFlatButton(text="이전으로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def select_slot(self, s):
        app = MDApp.get_running_app()
        app.slot = s
        self.status.text = f"선택 계정: {app.acc} / 슬롯: {s}"
        MDSnackbar(text=f"{s}번 슬롯이 활성화되었습니다.").open()

    def go_target(self, t):
        if not MDApp.get_running_app().slot:
            MDSnackbar(text="슬롯을 먼저 선택해야 합니다.").open()
            return
        self.manager.current = t

# ---------- 3. 케릭 정보창 (18종 절대규칙) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [절대규칙] 18종 리스트 박제
        self.fields = [
            "이름", "직위", "클랜", "레벨", "생명력", "기력", "근력", 
            "힘", "정신력", "재능", "민첩", "건강", "명중", "공격", 
            "방어", "흡수", "속도", "추가메모"
        ]
        sv = MDScrollView()
        cont = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None)
        cont.bind(minimum_height=cont.setter('height'))
        
        for f in self.fields:
            row = BoxLayout(size_hint_y=None, height=dp(45))
            row.add_widget(MDLabel(text=f, size_hint_x=0.3))
            tf = MDTextField(mode="fill", halign="center")
            self.inputs[f] = tf
            row.add_widget(tf)
            cont.add_widget(row)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="정보 저장", size_hint_x=0.5, on_release=lambda x: self.save()))
        btns.add_widget(MDRaisedButton(text="내용 비우기", size_hint_x=0.5, md_bg_color=(1,0,0,1), on_release=lambda x: self.clear()))
        cont.add_widget(btns)
        cont.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(cont); self.add_widget(sv)

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
        conn.commit(); MDSnackbar(text="정보가 성공적으로 저장되었습니다.").open()

    def clear(self):
        for tf in self.inputs.values(): tf.text = ""

# ---------- 4. 장비창 (11종 절대규칙) ----------
class EquipScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # [절대규칙] 11종 리스트 박제
        self.eqs = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        for e in self.eqs:
            row = BoxLayout(size_hint_y=None, height=dp(45))
            row.add_widget(MDLabel(text=e, size_hint_x=0.3))
            tf = MDTextField(mode="rectangle")
            self.inputs[e] = tf
            row.add_widget(tf)
            l.add_widget(row)
        
        l.add_widget(MDRaisedButton(text="장비 정보 저장", size_hint_x=1, on_release=lambda x: self.save()))
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
        conn.commit(); MDSnackbar(text="장비 정보가 저장되었습니다.").open()

# ---------- 5. 인벤토리 및 6. 사진 (생략/유지) ----------
class InvenScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        sv = MDScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(10))
        grid.bind(minimum_height=grid.setter('height'))
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"아이템 슬롯 {i}")
            self.inputs[i] = tf
            grid.add_widget(tf)
        grid.add_widget(MDRaisedButton(text="인벤토리 저장", size_hint_x=1, on_release=self.save))
        grid.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(grid); self.add_widget(sv)

    def save(self, *a):
        app = MDApp.get_running_app()
        data = {str(k): tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'inv', json.dumps(data)))
        conn.commit(); MDSnackbar(text="인벤토리가 저장되었습니다.").open()

class PhotoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.img = Image(source="", size_hint_y=0.7)
        l.add_widget(self.img)
        l.add_widget(MDRaisedButton(text="사진 찾기", size_hint_x=1, on_release=self.pick))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

    def pick(self, *a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda s: setattr(self.img, 'source', s[0] if s else ""))
        except: MDSnackbar(text="기능 지원 안됨").open()

if __name__ == '__main__':
    try:
        PristonTaleApp().run()
    except Exception:
        with open(os.path.join(BASE_DIR, "error_log.txt"), "w") as f:
            f.write(traceback.format_exc())
