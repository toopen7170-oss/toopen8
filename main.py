import os, json, sqlite3, traceback

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('kivy', 'softinput_mode', 'pan')

from kivy.resources import resource_find
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.text import LabelBase

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

# ---------- 폰트 ----------
FONT_PATH = resource_find("font.ttf")
if FONT_PATH:
    LabelBase.register(name="KFont", fn_regular=FONT_PATH)

# ---------- DB ----------
DB = sqlite3.connect("pt.db")
cur = DB.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS acc(name TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS data(acc TEXT, slot INT, type TEXT, val TEXT)")
DB.commit()

# ---------- 앱 ----------
class App(MDApp):
    def build(self):
        self.sm = ScreenManager()
        self.acc = ""
        self.slot = 1

        self.sm.add_widget(Account(name="acc"))
        self.sm.add_widget(Char(name="char"))
        self.sm.add_widget(Menu(name="menu"))
        self.sm.add_widget(Info(name="info"))
        self.sm.add_widget(Equip(name="equip"))
        self.sm.add_widget(Inven(name="inv"))
        self.sm.add_widget(Photo(name="photo"))

        return self.sm

    def confirm(self, msg, func):
        d = MDDialog(text=msg, buttons=[
            MDRaisedButton(text="취소", on_release=lambda x:d.dismiss()),
            MDRaisedButton(text="확인", on_release=lambda x:(func(),d.dismiss()))
        ])
        d.open()

# ---------- 공통 배경 ----------
def bg():
    p = resource_find("bg.png")
    return Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.2) if p else None

# ---------- 계정 ----------
class Account(Screen):
    def on_enter(self):
        self.clear_widgets()
        if bg(): self.add_widget(bg())

        l = BoxLayout(orientation='vertical', padding=20)
        self.t = MDTextField(hint_text="계정 입력")
        l.add_widget(self.t)

        l.add_widget(MDRaisedButton(text="저장",
            on_release=lambda x: App.get_running_app().confirm("저장?", self.save)))

        self.list = GridLayout(cols=1, size_hint_y=None)
        self.list.bind(minimum_height=self.list.setter('height'))
        sv = MDScrollView(); sv.add_widget(self.list)
        l.add_widget(sv)

        self.add_widget(l)
        self.refresh()

    def save(self):
        cur.execute("INSERT OR IGNORE INTO acc VALUES(?)",(self.t.text,))
        DB.commit()
        self.refresh()

    def refresh(self):
        self.list.clear_widgets()
        for (n,) in cur.execute("SELECT name FROM acc"):
            self.list.add_widget(
                MDRaisedButton(text=n, on_release=lambda x,n=n:self.go(n))
            )

    def go(self,n):
        App.get_running_app().acc=n
        self.manager.current="char"

# ---------- 캐릭터 ----------
class Char(Screen):
    def on_enter(self):
        self.clear_widgets()
        if bg(): self.add_widget(bg())

        g=GridLayout(cols=2)
        for i in range(1,7):
            g.add_widget(MDRaisedButton(text=f"슬롯{i}",
                on_release=lambda x,i=i:self.go(i)))
        self.add_widget(g)

    def go(self,i):
        App.get_running_app().slot=i
        self.manager.current="menu"

# ---------- 메뉴 ----------
class Menu(Screen):
    def on_enter(self):
        self.clear_widgets()
        if bg(): self.add_widget(bg())

        l=BoxLayout(orientation='vertical',spacing=10,padding=20)
        for n,s in [("정보","info"),("장비","equip"),("인벤","inv"),("사진","photo")]:
            l.add_widget(MDRaisedButton(text=n,
                on_release=lambda x,s=s:setattr(self.manager,"current",s)))
        self.add_widget(l)

# ---------- 정보 (18개 유지) ----------
class Info(Screen):
    def on_enter(self):
        self.clear_widgets()
        if bg(): self.add_widget(bg())

        fields=["이름","직위","클랜","레벨","생명력","기력","근력",
        "힘","정신력","재능","민첩","건강",
        "명중","공격","방어","흡수","속도"]

        l=GridLayout(cols=1,size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        self.inputs={}
        for f in fields:
            tf=MDTextField(hint_text=f)
            self.inputs[f]=tf
            l.add_widget(tf)

        sv=MDScrollView(); sv.add_widget(l)
        self.add_widget(sv)

# ---------- 장비 (11개 유지) ----------
class Equip(Screen):
    def on_enter(self):
        self.clear_widgets()
        if bg(): self.add_widget(bg())

        eq=["한손무기","두손무기","갑옷","방패","장갑","부츠","암릿","링1","링2","아뮬렛","기타"]

        l=GridLayout(cols=1,size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        for e in eq:
            l.add_widget(MDTextField(hint_text=e))

        sv=MDScrollView(); sv.add_widget(l)
        self.add_widget(sv)

# ---------- 인벤 ----------
class Inven(Screen):
    def on_enter(self):
        self.clear_widgets()
        if bg(): self.add_widget(bg())

        l=GridLayout(cols=1,size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))

        for i in range(20):
            l.add_widget(MDTextField(hint_text=f"아이템{i}"))

        sv=MDScrollView(); sv.add_widget(l)
        self.add_widget(sv)

# ---------- 사진 ----------
class Photo(Screen):
    def on_enter(self):
        self.clear_widgets()
        if bg(): self.add_widget(bg())

        l=BoxLayout(orientation='vertical')
        self.img=Image()
        l.add_widget(self.img)

        l.add_widget(MDRaisedButton(text="사진 선택",
            on_release=self.pick))

        self.add_widget(l)

    def pick(self,*a):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda s:self.set(s), multiple=True)
        except:
            pass

    def set(self,s):
        if s:
            self.img.source=s[0]

# ---------- 실행 ----------
if __name__=="__main__":
    try:
        App().run()
    except:
        open("error.txt","w").write(traceback.format_exc())