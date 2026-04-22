import os, json, sqlite3, traceback

# ---------- 기본 설정 ----------
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('kivy', 'softinput_mode', 'pan')

from kivy.utils import platform
from kivy.resources import resource_find
from kivy.uix.screenmanager import ScreenManager, Screen
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

# ---------- 경로 ----------
if platform == "android":
    from android.storage import app_storage_path
    from android.permissions import request_permissions, Permission
    BASE_DIR = app_storage_path()
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
else:
    BASE_DIR = os.getcwd()

# ---------- 폰트 ----------
FONT_PATH = os.path.join(BASE_DIR, "font.ttf")
if not os.path.exists(FONT_PATH):
    FONT_PATH = resource_find("font.ttf")
if FONT_PATH:
    LabelBase.register(name="KFont", fn_regular=FONT_PATH)

# ---------- DB ----------
DB_PATH = os.path.join(BASE_DIR, "pt.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS acc (name TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS data (acc TEXT, slot INT, type TEXT, value TEXT, PRIMARY KEY(acc,slot,type))")
conn.commit()

# ---------- 앱 ----------
class App(MDApp):
    def build(self):
        self.acc = None
        self.slot = None

        self.sm = ScreenManager()
        self.sm.add_widget(Account(name="acc"))
        self.sm.add_widget(Char(name="char"))
        self.sm.add_widget(Menu(name="menu"))
        self.sm.add_widget(Info(name="info"))
        self.sm.add_widget(Equip(name="equip"))
        self.sm.add_widget(Inven(name="inven"))
        self.sm.add_widget(Photo(name="photo"))

        Clock.schedule_once(self.diagnosis, 1)
        return self.sm

    def diagnosis(self, dt):
        err = []
        if not os.path.exists(os.path.join(BASE_DIR,"bg.png")):
            err.append("bg.png 없음")
        if not FONT_PATH:
            err.append("font.ttf 없음")

        msg = "\n".join(err) if err else "정상 작동"
        d = MDDialog(title="진단", text=msg, buttons=[MDRaisedButton(text="확인", on_release=lambda x:d.dismiss())])
        d.open()

    def confirm(self, title, text, func):
        d = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(text="취소", on_release=lambda x:d.dismiss()),
                MDRaisedButton(text="확인", md_bg_color=(1,0,0,1) if "삭제" in title else (0,1,0,1),
                    on_release=lambda x:[func(), d.dismiss()])
            ])
        d.open()

# ---------- 공통 배경 ----------
def bg(screen):
    p = os.path.join(BASE_DIR,"bg.png")
    if os.path.exists(p):
        screen.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.2))

# ---------- 1 계정 ----------
class Account(Screen):
    def on_enter(self):
        self.clear_widgets()
        bg(self)

        box = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.add_widget(box)

        self.input = MDTextField(hint_text="계정 입력")
        box.add_widget(self.input)

        box.add_widget(MDRaisedButton(text="저장", md_bg_color=(0,1,0,1),
            on_release=lambda x:App.get_running_app().confirm("저장","저장?", self.save)))

        self.list = GridLayout(cols=1, size_hint_y=None)
        self.list.bind(minimum_height=self.list.setter('height'))

        sv = MDScrollView()
        sv.add_widget(self.list)
        box.add_widget(sv)

        self.refresh()

    def refresh(self):
        self.list.clear_widgets()
        for (n,) in cur.execute("SELECT name FROM acc"):
            row = BoxLayout(size_hint_y=None,height=50)

            b = MDRaisedButton(text=n, on_release=lambda x,n=n:self.go(n))
            d = MDRaisedButton(text="삭제", md_bg_color=(1,0,0,1),
                on_release=lambda x,n=n:App.get_running_app().confirm("삭제","삭제?", lambda:self.delacc(n)))

            row.add_widget(b)
            row.add_widget(d)
            self.list.add_widget(row)

    def save(self):
        n = self.input.text.strip()
        if n:
            cur.execute("INSERT OR IGNORE INTO acc VALUES(?)",(n,))
            conn.commit()
            self.refresh()
            self.input.text=""

    def delacc(self,n):
        cur.execute("DELETE FROM acc WHERE name=?",(n,))
        conn.commit()
        self.refresh()

    def go(self,n):
        App.get_running_app().acc=n
        self.manager.current="char"

# ---------- 2 캐릭터 ----------
class Char(Screen):
    def on_enter(self):
        self.clear_widgets()
        bg(self)

        g = GridLayout(cols=2)
        for i in range(1,7):
            btn = MDRaisedButton(text=f"슬롯 {i}")
            btn.bind(on_release=lambda x,i=i:self.go(i))
            g.add_widget(btn)

        self.add_widget(g)

    def go(self,i):
        App.get_running_app().slot=i
        self.manager.current="menu"

# ---------- 3 메뉴 ----------
class Menu(Screen):
    def on_enter(self):
        self.clear_widgets()
        bg(self)

        l = BoxLayout(orientation='vertical', spacing=10, padding=20)
        for name,screen in [
            ("정보","info"),("장비","equip"),("인벤","inven"),("사진","photo")
        ]:
            l.add_widget(MDRaisedButton(text=name, on_release=lambda x,s=screen:setattr(self.manager,'current',s)))

        self.add_widget(l)

# ---------- 4 정보 ----------
class Info(Screen):
    def on_enter(self):
        self.clear_widgets()
        bg(self)

        self.inputs={}
        sv = MDScrollView()
        box = BoxLayout(orientation='vertical',size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        fields = ["이름","직위","클랜","레벨","생명력","기력","근력","힘","정신력","재능","민첩","건강","명중","공격","방어","흡수","속도"]

        for f in fields:
            tf = MDTextField(hint_text=f)
            self.inputs[f]=tf
            box.add_widget(tf)

        box.add_widget(MDRaisedButton(text="저장", on_release=lambda x:self.save()))
        sv.add_widget(box)
        self.add_widget(sv)

        self.load()

    def save(self):
        app=App.get_running_app()
        data={k:v.text for k,v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO data VALUES(?,?,?,?)",(app.acc,app.slot,"info",json.dumps(data)))
        conn.commit()

    def load(self):
        app=App.get_running_app()
        r=cur.execute("SELECT value FROM data WHERE acc=? AND slot=? AND type='info'",(app.acc,app.slot)).fetchone()
        if r:
            d=json.loads(r[0])
            for k in self.inputs:
                self.inputs[k].text=d.get(k,"")

# ---------- 5 장비 ----------
class Equip(Screen):
    def on_enter(self):
        self.clear_widgets()
        bg(self)

        self.inputs={}
        sv=MDScrollView()
        box=BoxLayout(orientation='vertical',size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        eq=["한손무기","두손무기","갑옷","방패","장갑","부츠","암릿","링1","링2","아뮬렛","기타"]

        for e in eq:
            tf=MDTextField(hint_text=e)
            self.inputs[e]=tf
            box.add_widget(tf)

        box.add_widget(MDRaisedButton(text="저장", on_release=lambda x:self.save()))
        sv.add_widget(box)
        self.add_widget(sv)

        self.load()

    def save(self):
        app=App.get_running_app()
        data={k:v.text for k,v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO data VALUES(?,?,?,?)",(app.acc,app.slot,"equip",json.dumps(data)))
        conn.commit()

    def load(self):
        app=App.get_running_app()
        r=cur.execute("SELECT value FROM data WHERE acc=? AND slot=? AND type='equip'",(app.acc,app.slot)).fetchone()
        if r:
            d=json.loads(r[0])
            for k in self.inputs:
                self.inputs[k].text=d.get(k,"")

# ---------- 6 인벤 ----------
class Inven(Screen):
    def on_enter(self):
        self.clear_widgets()
        bg(self)

        self.inputs={}
        sv=MDScrollView()
        box=BoxLayout(orientation='vertical',size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        for i in range(1,21):
            tf=MDTextField(hint_text=f"칸 {i}")
            self.inputs[i]=tf
            box.add_widget(tf)

        box.add_widget(MDRaisedButton(text="저장", on_release=lambda x:self.save()))
        sv.add_widget(box)
        self.add_widget(sv)

    def save(self):
        app=App.get_running_app()
        data={str(k):v.text for k,v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO data VALUES(?,?,?,?)",(app.acc,app.slot,"inven",json.dumps(data)))
        conn.commit()

# ---------- 7 사진 ----------
class Photo(Screen):
    def on_enter(self):
        self.clear_widgets()
        bg(self)

        l=BoxLayout(orientation='vertical')
        self.img=Image()
        l.add_widget(self.img)

        l.add_widget(MDRaisedButton(text="사진 선택", on_release=self.pick))
        self.add_widget(l)

    def pick(self,*a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.sel, multiple=True)
        except:
            pass

    def sel(self,files):
        if files:
            self.img.source=files[0]

# ---------- 실행 ----------
if __name__=="__main__":
    try:
        App().run()
    except:
        with open("error.txt","w") as f:
            f.write(traceback.format_exc())