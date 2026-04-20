import os
import sys
from kivy.config import Config

# [전수검사] 최신 안드로이드 하드웨어 가속 및 자판 충돌 방지
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('softinput_mode', 'pan')

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

class PristonTaleApp(MDApp):
    def build(self):
        # 엔진 시동 시 테마 설정을 최소화하여 튕김 방지
        self.theme_cls.primary_palette = "BlueGray"
        self.sm = ScreenManager()
        
        # [제1원칙] 6개 화면 등록
        self.sm.add_widget(MainMenu(name='main'))
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        
        # [자가진단] 시동 후 보안 검사를 우회하여 지연 실행
        Clock.schedule_once(self.run_final_diagnostic, 2.0)
        return self.sm

    def run_final_diagnostic(self, dt):
        errors = []
        if not os.path.exists(get_path("font.ttf")): errors.append("폰트 누락")
        if not os.path.exists(get_path("bg.png")): errors.append("배경 누락")
        
        if errors:
            self.dialog = MDDialog(
                title="[자가진단] 시스템 알림",
                text=f"현재 '{', '.join(errors)}' 상태입니다. 리소스를 확인하세요.",
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.dialog.dismiss())]
            )
            self.dialog.open()
        else:
            MDSnackbar(text="[자가진단] 모든 시스템 정상 가동!", bg_color=(0, 0.4, 0, 1)).open()

# --- 화면 공통 배경 (지연 로딩 방식) ---
class BaseScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.apply_safe_bg, 0.2)
    def apply_safe_bg(self, dt):
        p = get_path("bg.png")
        if os.path.exists(p) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.3), index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="Priston Tale Manager", halign="center", font_style="H5"))
        menus = [("계정생성창", "acc"), ("케릭선택창", "sel"), ("케릭정보창", "info"),
                 ("케릭장비창", "equ"), ("인벤토리창", "inv"), ("사진선택창", "pho")]
        for name, sn in menus:
            l.add_widget(MDRaisedButton(text=name, size_hint=(1, None), height=dp(50),
                                       on_release=lambda x, s=sn: setattr(self.manager, 'current', s)))
        self.add_widget(l)

# [제1원칙] 케릭정보창 세부 목록 (19종)
class CharInfoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        groups = [
            ("기본 정보", [('이름',''), ('직위',''), ('클랜',''), ('레벨','')]),
            ("상태 수치", [('생명력','HP'), ('기력','MP'), ('근력','STM')]),
            ("기본 스탯", [('힘','STR'), ('정신력','SPI'), ('재능','TAL'), ('민첩','AGI'), ('건강','VIT')]),
            ("전투 지표", [('명중','Rating'), ('공격','Power'), ('방어','Defense'), ('흡수','Absorb'), ('속도','Speed')])
        ]
        for title, items in groups:
            l.add_widget(MDLabel(text=f"[{title}]", font_style="Subtitle2"))
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(items)*55), spacing=dp(5))
            for label, hint in items:
                grid.add_widget(MDLabel(text=label, halign="center"))
                grid.add_widget(MDTextField(hint_text=hint, halign="center"))
            l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        scroll.add_widget(l)
        self.add_widget(scroll)

# [제1원칙] 케릭장비창 세부 목록 (11종)
class EquipScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        scroll = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(items)*60), spacing=dp(10))
        for item in items:
            grid.add_widget(MDLabel(text=item, halign="center"))
            grid.add_widget(MDTextField(halign="center", hint_text="장착 정보"))
        l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        scroll.add_widget(l)
        self.add_widget(scroll)

class AccountScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDTextField(hint_text="계정전체검색", mode="rectangle"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        self.add_widget(l)

class PhotoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진 관리 시스템", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        self.add_widget(l)

class CharSelectScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = GridLayout(cols=2, padding=dp(20), spacing=dp(10))
        for i in range(1, 7): l.add_widget(MDRaisedButton(text=f"케릭 {i}", size_hint=(1,1)))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDTextField(hint_text="아이템 검색", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

if __name__ == '__main__':
    PristonTaleApp().run()
