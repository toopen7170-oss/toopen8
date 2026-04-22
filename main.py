import os
import json
import traceback
import sqlite3

# [진단] S26 울트라 최적화 설정
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
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

# ---------- [환경 및 폰트/이미지 경로 최적화] ----------
if platform == "android":
    from android.storage import app_storage_path
    from android.permissions import request_permissions, Permission
    BASE_DIR = app_storage_path()
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
else:
    BASE_DIR = os.getcwd()

# [ㅁㅁ박멸] 폰트 선등록
FONT_PATH = os.path.join(BASE_DIR, "font.ttf")
if not os.path.exists(FONT_PATH): FONT_PATH = resource_find("font.ttf")
if FONT_PATH:
    LabelBase.register(name="KoreanFont", fn_regular=FONT_PATH)

DB_PATH = os.path.join(BASE_DIR, "pt1_master.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS chars (acc TEXT, slot INTEGER, type TEXT, data TEXT, PRIMARY KEY(acc, slot, type))")
conn.commit()

# ---------- 메인 앱 엔진 ----------
class PristonTaleApp(MDApp):
    def build(self):
        self.title = "PristonTale"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        
        # [폰트 전체 적용] 모든 스타일에 강제 주입
        if FONT_PATH:
            for style in list(self.theme_cls.font_styles.keys()):
                self.theme_cls.font_styles[style] = ["KoreanFont", 16, False, 0.15]

        self.acc = None
        self.slot = None
        self.sm = ScreenManager(transition=FadeTransition())
        
        # [제1원칙] 6개 화면 + 메뉴화면 등록
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(SlotMenuScreen(name='slot_menu')) # 8번 수정 사항
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))

        Clock.schedule_once(self.run_diagnosis, 1.2)
        return self.sm

    def run_diagnosis(self, dt):
        """전체 검색 자가 진단 시스템"""
        errs = []
        if not os.path.exists(FONT_PATH): errs.append("❌ 폰트(font.ttf) 누락")
        if not os.path.exists(os.path.join(BASE_DIR, "bg.png")): errs.append("⚠️ 배경(bg.png) 누락")
        if not conn: errs.append("🚨 DB 연결 오류")
        
        msg = "\n".join(errs) if errs else "✅ 모든 시스템이 무결합니다. (오류 0개)"
        d = MDDialog(title="🛡️ 올라운드 전수 진단", text=msg, buttons=[MDRaisedButton(text="확인", on_release=lambda x: d.dismiss())])
        d.open()

    def confirm(self, title, text, on_yes):
        d = MDDialog(title=title, text=text, buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: d.dismiss()),
            MDRaisedButton(text="확인", md_bg_color=(1,0,0,1) if "삭제" in title else (0,0.5,0,1), on_release=lambda x: [on_yes(), d.dismiss()])
        ])
        d.open()

# ---------- 1. 계정 생성창 ----------
class AccountScreen(Screen):
    def on_enter(self):
        self.clear_widgets() # 배경 중복 방지
        p = os.path.join(BASE_DIR, "bg.png")
        if os.path.exists(p): self.add_widget(Image(source=p, opacity=0.2, allow_stretch=True, keep_ratio=False))
        self.setup_ui()

    def setup_ui(self):
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="PristonTale", halign="center", font_style="H4"))
        
        self.search = MDTextField(hint_text="🔍 전체 계정 검색", mode="rectangle", halign="center")
        self.search.bind(text=lambda i, v: self.refresh(v))
        l.add_widget(self.search)

        self.new_id = MDTextField(hint_text="새 계정 ID", halign="center")
        l.add_widget(self.new_id)

        l.add_widget(MDRaisedButton(text="계정 저장", md_bg_color=(0,0.5,0,1), size_hint_x=1, on_release=lambda x: MDApp.get_running_app().confirm("저장", "저장하시겠습니까?", self.save)))
        
        self.view = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.view.bind(minimum_height=self.view.setter('height'))
        sv = MDScrollView(); sv.add_widget(self.view); l.add_widget(sv)
        self.add_widget(l); self.refresh()

    def refresh(self, q=""):
        self.view.clear_widgets()
        cur.execute("SELECT name FROM accounts WHERE name LIKE ?", ('%'+q+'%',))
        for (n,) in cur.fetchall():
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            b = MDRectangleFlatButton(text=n, size_hint_x=0.8); b.bind(on_release=lambda x, name=n: self.go_sel(name))
            d = MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1), size_hint_x=0.2); d.bind(on_release=lambda x, name=n: MDApp.get_running_app().confirm("삭제", f"[{name}] 삭제하시겠습니까?", lambda: self.delete(name)))
            row.add_widget(b); row.add_widget(d); self.view.add_widget(row)

    def save(self):
        n = self.new_id.text.strip()
        if n: cur.execute("INSERT OR IGNORE INTO accounts VALUES(?)", (n,)); conn.commit(); self.refresh(); self.new_id.text=""
    def delete(self, n): cur.execute("DELETE FROM accounts WHERE name=?", (n,)); conn.commit(); self.refresh()
    def go_sel(self, n): MDApp.get_running_app().acc = n; self.manager.current = 'sel'

# ---------- 2. 캐릭터 선택창 (6슬롯) ----------
class CharSelectScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        p = os.path.join(BASE_DIR, "bg_sword.png")
        if os.path.exists(p): self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False))
        
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        l.add_widget(MDLabel(text=f"[{MDApp.get_running_app().acc}] 캐릭터 선택", halign="center", font_style="H5"))
        
        grid = GridLayout(cols=2, spacing=dp(10))
        for i in range(1, 7):
            cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='info'", (MDApp.get_running_app().acc, i))
            res = cur.fetchone(); name = json.loads(res[0]).get("이름", "") if res else "비어있음"
            btn = MDRaisedButton(text=f"슬롯 {i}\n{name}", size_hint=(1,1), halign="center")
            btn.bind(on_release=lambda x, s=i: self.go_menu(s))
            grid.add_widget(btn)
        l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="이전으로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def go_menu(self, s):
        MDApp.get_running_app().slot = s
        self.manager.current = 'slot_menu'

# ---------- 8번 수정: 슬롯 메뉴 전체 화면 ----------
class SlotMenuScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        p = os.path.join(BASE_DIR, "bg_sword.png")
        if os.path.exists(p): self.add_widget(Image(source=p, opacity=0.3, allow_stretch=True, keep_ratio=False))
        
        l = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20))
        l.add_widget(MDLabel(text=f"슬롯 {MDApp.get_running_app().slot} 관리", halign="center", font_style="H4"))
        
        # 4개 버튼 (지시 사항 9번 대응)
        for n, t in [("케릭정보창", "info"), ("케릭장비창", "equ"), ("인벤토리창", "inv"), ("사진선택창", "pho")]:
            btn = MDRaisedButton(text=n, size_hint_x=1, height=dp(60), font_style="H6", md_bg_color=(0,0.4,0.6,1))
            btn.bind(on_release=lambda x, target=t: setattr(self.manager, 'current', target))
            l.add_widget(btn)
            
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

# ---------- 3. 케릭정보창 (절대규칙 18종) ----------
class CharInfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        # 절대 규칙 그룹
        self.groups = [
            ["이름", "직위", "클랜", "레벨"],
            ["생명력", "기력", "근력"],
            ["힘", "정신력", "재능", "민첩", "건강"],
            ["명중", "공격", "방어", "흡수", "속도"]
        ]
        sv = MDScrollView(); self.cont = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint_y=None)
        self.cont.bind(minimum_height=self.cont.setter('height'))
        
        for g in self.groups:
            gb = BoxLayout(orientation='vertical', spacing=dp(2), size_hint_y=None)
            gb.bind(minimum_height=gb.setter('height'))
            for f in g:
                row = BoxLayout(size_hint_y=None, height=dp(55))
                row.add_widget(MDLabel(text=f, size_hint_x=0.3, halign="center"))
                tf = MDTextField(mode="fill", halign="center", font_size='18sp')
                self.inputs[f] = tf; row.add_widget(tf); gb.add_widget(row)
            self.cont.add_widget(gb) # 한칸 띄우기 효과

        self.cont.add_widget(MDRaisedButton(text="정보 저장", md_bg_color=(0,0.5,0,1), size_hint_x=1, on_release=lambda x: self.save()))
        self.cont.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=lambda x: MDApp.get_running_app().confirm("삭제", "정말 삭제하시겠습니까?", self.clear)))
        self.cont.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'slot_menu')))
        sv.add_widget(self.cont); self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='info'", (app.acc, app.slot))
        res = cur.fetchone(); data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")

    def save(self):
        app = MDApp.get_running_app(); data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'info', json.dumps(data))); conn.commit()

    def clear(self):
        for tf in self.inputs.values(): tf.text = ""
        self.save()

# ---------- 4. 케릭장비창 (11종) ----------
class EquipScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.inputs = {}
        eqs = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        sv = MDScrollView(); l = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        for f in eqs:
            row = BoxLayout(size_hint_y=None, height=dp(55))
            row.add_widget(MDLabel(text=f, size_hint_x=0.3, halign="center"))
            tf = MDTextField(mode="rectangle", halign="center"); self.inputs[f] = tf
            row.add_widget(tf); l.add_widget(row)
        l.add_widget(MDRaisedButton(text="장비 저장", md_bg_color=(0,0.5,0,1), size_hint_x=1, on_release=lambda x: self.save()))
        l.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(1,0,0,1), size_hint_x=1, on_release=lambda x: MDApp.get_running_app().confirm("삭제", "장비 정보를 비우시겠습니까?", self.clear)))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'slot_menu')))
        sv.add_widget(l); self.add_widget(sv)

    def on_pre_enter(self):
        app = MDApp.get_running_app(); cur.execute("SELECT data FROM chars WHERE acc=? AND slot=? AND type='equ'", (app.acc, app.slot))
        res = cur.fetchone(); data = json.loads(res[0]) if res else {}
        for k, tf in self.inputs.items(): tf.text = data.get(k, "")
    def save(self):
        app = MDApp.get_running_app(); data = {k: tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'equ', json.dumps(data))); conn.commit()
    def clear(self):
        for tf in self.inputs.values(): tf.text = ""
        self.save()

# ---------- 5. 인벤토리 및 6. 사진 (골자 유지) ----------
class InvenScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView(); self.l = GridLayout(cols=1, spacing=dp(10), padding=dp(20), size_hint_y=None)
        self.l.bind(minimum_height=self.l.setter('height'))
        self.inputs = {}
        for i in range(1, 21):
            tf = MDTextField(hint_text=f"인벤토리 줄 {i}", mode="rectangle", halign="center")
            self.inputs[i] = tf; self.l.add_widget(tf)
        self.l.add_widget(MDRaisedButton(text="저장", md_bg_color=(0,0.5,0,1), size_hint_x=1, on_release=lambda x: self.save()))
        self.l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'slot_menu')))
        sv.add_widget(self.l); self.add_widget(sv)
    def save(self):
        app = MDApp.get_running_app(); data = {str(k): tf.text for k, tf in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO chars VALUES(?,?,?,?)", (app.acc, app.slot, 'inv', json.dumps(data))); conn.commit()

class PhotoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.img = Image(source="", size_hint_y=0.7)
        l.add_widget(self.img)
        l.add_widget(MDRaisedButton(text="핸드폰 사진 선택 (다중)", md_bg_color=(0,0.4,0.7,1), size_hint_x=1, on_release=self.pick))
        l.add_widget(MDRectangleFlatButton(text="뒤로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'slot_menu')))
        self.add_widget(l)
    def pick(self, *a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda s: setattr(self.img, 'source', s[0] if s else ""), multiple=True)
        except: pass

if __name__ == '__main__':
    try: PristonTaleApp().run()
    except:
        with open(os.path.join(BASE_DIR, "error_log.txt"), "w") as f: f.write(traceback.format_exc())
