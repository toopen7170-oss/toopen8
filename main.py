# === PristonTale FULL APP (최종 안정판) ===

import os, json, sqlite3, traceback
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('kivy', 'softinput_mode', 'pan')

from kivy.utils import platform
from kivy.resources import resource_find
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

# -------- 경로 --------
if platform == "android":
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
else:
    BASE_DIR = os.getcwd()

FONT_PATH = os.path.join(BASE_DIR, "font.ttf")
if not os.path.exists(FONT_PATH):
    FONT_PATH = resource_find("font.ttf")

if FONT_PATH:
    LabelBase.register(name="KFont", fn_regular=FONT_PATH)

# -------- DB --------
DB = os.path.join(BASE_DIR, "app.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS acc(name TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS data(acc TEXT, slot INT, type TEXT, val TEXT, PRIMARY KEY(acc,slot,type))")
conn.commit()

# -------- 앱 --------
class App(MDApp):
    def build(self):
        self.acc=None; self.slot=None
        self.sm=ScreenManager(transition=FadeTransition())
        self.sm.add_widget(Account(name='acc'))
        self.sm.add_widget(Slot(name='slot'))
        self.sm.add_widget(Menu(name='menu'))
        self.sm.add_widget(Info(name='info'))
        self.sm.add_widget(Equip(name='equip'))
        self.sm.add_widget(Inven(name='inv'))
        self.sm.add_widget(Photo(name='photo'))

        Clock.schedule_once(self.check,1)
        return self.sm

    def check(self,*a):
        err=[]
        if not os.path.exists(os.path.join(BASE_DIR,"bg.png")):
            err.append("bg.png 없음")
        if not os.path.exists(FONT_PATH):
            err.append("font.ttf 없음")
        txt="\n".join(err) if err else "오류 없음"
        MDDialog(title="자가진단", text=txt,
        buttons=[MDRaisedButton(text="확인", on_release=lambda x:x.parent.parent.dismiss())]).open()

app = App()

# -------- 1 계정 --------
class Account(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.add_widget(Image(source="bg.png", allow_stretch=True, keep_ratio=False))

        l=BoxLayout(orientation='vertical',padding=20,spacing=10)
        self.input=MDTextField(hint_text="계정 생성")
        l.add_widget(self.input)

        l.add_widget(MDRaisedButton(text="저장", md_bg_color=(0,1,0,1),
        on_release=lambda x:self.save()))

        self.list=GridLayout(cols=1,size_hint_y=None)
        self.list.bind(minimum_height=self.list.setter('height'))
        sv=MDScrollView(); sv.add_widget(self.list)
        l.add_widget(sv)

        self.add_widget(l)
        self.refresh()

    def save(self):
        n=self.input.text.strip()
        if n:
            cur.execute("INSERT OR IGNORE INTO acc VALUES(?)",(n,))
            conn.commit()
            self.refresh()

    def refresh(self):
        self.list.clear_widgets()
        for (n,) in cur.execute("SELECT name FROM acc"):
            b=MDRaisedButton(text=n)
            b.bind(on_release=lambda x,v=n:self.go(v))
            self.list.add_widget(b)

    def go(self,n):
        app.acc=n
        self.manager.current='slot'

# -------- 2 슬롯 --------
class Slot(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.add_widget(Image(source="bg.png", allow_stretch=True))

        g=GridLayout(cols=2)
        for i in range(1,7):
            b=MDRaisedButton(text=f"{i}")
            b.bind(on_release=lambda x,v=i:self.go(v))
            g.add_widget(b)

        self.add_widget(g)

    def go(self,i):
        app.slot=i
        self.manager.current='menu'

# -------- 3 메뉴 --------
class Menu(Screen):
    def on_enter(self):
        self.clear_widgets()
        l=BoxLayout(orientation='vertical')
        for t,n in [("info","정보"),("equip","장비"),("inv","인벤"),("photo","사진")]:
            b=MDRaisedButton(text=n)
            b.bind(on_release=lambda x,v=t:setattr(self.manager,'current',v))
            l.add_widget(b)
        self.add_widget(l)

# -------- 4 정보 --------
class Info(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.inputs={}
        sv=MDScrollView()
        l=BoxLayout(orientation='vertical',size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        fields=["이름","직위","클랜","레벨","생명력","기력","근력",
        "힘","정신력","재능","민첩","건강",
        "명중","공격","방어","흡수","속도"]

        for f in fields:
            tf=MDTextField(hint_text=f)
            self.inputs[f]=tf
            l.add_widget(tf)

        l.add_widget(MDRaisedButton(text="저장", on_release=lambda x:self.save()))
        sv.add_widget(l)
        self.add_widget(sv)

    def save(self):
        d={k:v.text for k,v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO data VALUES(?,?,?,?)",
        (app.acc,app.slot,"info",json.dumps(d)))
        conn.commit()

# -------- 5 장비 --------
class Equip(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.inputs={}
        sv=MDScrollView()
        l=BoxLayout(orientation='vertical',size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        fields=["한손무기","두손무기","갑옷","방패","장갑","부츠",
        "암릿","링1","링2","아뮬렛","기타"]

        for f in fields:
            tf=MDTextField(hint_text=f)
            self.inputs[f]=tf
            l.add_widget(tf)

        l.add_widget(MDRaisedButton(text="저장", on_release=lambda x:self.save()))
        sv.add_widget(l)
        self.add_widget(sv)

    def save(self):
        d={k:v.text for k,v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO data VALUES(?,?,?,?)",
        (app.acc,app.slot,"equip",json.dumps(d)))
        conn.commit()

# -------- 6 인벤 --------
class Inven(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.inputs={}
        sv=MDScrollView()
        l=BoxLayout(orientation='vertical',size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        for i in range(1,21):
            tf=MDTextField(hint_text=f"{i}")
            self.inputs[i]=tf
            l.add_widget(tf)

        l.add_widget(MDRaisedButton(text="저장", on_release=lambda x:self.save()))
        sv.add_widget(l)
        self.add_widget(sv)

    def save(self):
        d={str(k):v.text for k,v in self.inputs.items()}
        cur.execute("INSERT OR REPLACE INTO data VALUES(?,?,?,?)",
        (app.acc,app.slot,"inv",json.dumps(d)))
        conn.commit()

# -------- 7 사진 --------
class Photo(Screen):
    def on_enter(self):
        self.clear_widgets()
        l=BoxLayout(orientation='vertical')
        self.img=Image()
        l.add_widget(self.img)
        l.add_widget(MDRaisedButton(text="사진선택", on_release=self.pick))
        self.add_widget(l)

    def pick(self,*a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=self.sel, multiple=True)
        except: pass

    def sel(self,s):
        if s: self.img.source=s[0]

# -------- 실행 --------
if __name__=="__main__":
    try:
        app.run()
    except:
        open("error.txt","w").write(traceback.format_exc())