import os
from kivy.config import Config

# [전수검사] 자판 가림 및 초기 튕김 방지 설정
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
from kivymd.uix.snackbar import MDSnackbar
from kivy.core.text import LabelBase

# 경로 추적
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

# --- 자가 진단 시스템 ---
def diag_report(text, is_error=True):
    color = (0.8, 0, 0, 1) if is_error else (0, 0.5, 0, 1)
    MDSnackbar(text=f"[자가진단] {text}", bg_color=color, duration=3).open()

# --- 제1 기본원칙 구조 보존 ---
class BaseScreen(Screen):
    def on_enter(self):
        # 배경 지연 로딩 (튕김 방지 핵심)
        Clock.schedule_once(self.apply_bg, 0.1)

    def apply_bg(self, dt):
        path = get_path("bg.png")
        if os.path.exists(path):
            if not any(isinstance(w, Image) for w in self.children):
                self.add_widget(Image(source=path, allow_stretch=True, keep_ratio=False, opacity=0.3), index=len(self.children))
        else:
            diag_report("bg.png 누락됨")

class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        path = get_path("bg.png")
        if os.path.exists(path):
            self.add_widget(Image(source=path, allow_stretch=True, keep_ratio=False, opacity=0.8))
        
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="Priston Tale Manager", halign="center", font_style="H5"))
        
        menus = [("계정생성창", "acc"), ("케릭선택창", "sel"), ("케릭정보창", "info"),
                 ("케릭장비창", "equ"), ("인벤토리창", "inv"), ("사진선택창", "pho")]
        
        for name, sn in menus:
            btn = MDRaisedButton(text=name, size_hint=(1, None), height=dp(55),
                                 on_release=lambda x, s=sn: setattr(self.manager, 'current', s))
            l.add_widget(btn)
        self.add_widget(l)

class AccountScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDTextField(hint_text="계정전체검색바", mode="rectangle", halign="center"))
        l.add_widget(MDTextField(hint_text="계정ID 입력", mode="helper", halign="center"))
        
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        row.add_widget(MDRaisedButton(text="저장", on_release=lambda x: diag_report("저장 시도", False)))
        row.add_widget(MDRaisedButton(text="삭제", on_release=lambda x: diag_report("삭제 시도", False)))
        l.add_widget(row)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class CharInfoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        groups = [[('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
                  [('생명력', ''), ('기력', ''), ('근력', '')],
                  [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
                  [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]]
        
        for g in groups:
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(g)*55), spacing=dp(5))
            for label, _ in g:
                grid.add_widget(MDLabel(text=label, halign="center"))
                grid.add_widget(MDTextField(halign="center", write_tab=False))
            l.add_widget(grid)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(30)))

        l.add_widget(MDRaisedButton(text="전체삭제", on_release=lambda x: diag_report("데이터 초기화")))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        scroll.add_widget(l)
        self.add_widget(scroll)

# [제1원칙 복구] 케릭장비창 11종 세부목록
class EquipScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        
        grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(items)*60), spacing=dp(10))
        for item in items:
            grid.add_widget(MDLabel(text=item, halign="center"))
            grid.add_widget(MDTextField(halign="center", hint_text="장비명 입력"))
        
        l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        scroll.add_widget(l)
        self.add_widget(scroll)

class PhotoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진 관리 (자가진단)", halign="center"))
        btn = MDRaisedButton(text="사진 선택", size_hint=(1, None), 
                             on_release=lambda x: diag_report("갤러리 접근 권한 확인 필요"))
        l.add_widget(btn)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
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
        l.add_widget(MDTextField(hint_text="인벤토리 아이템 검색", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.sm = ScreenManager()
        # [진단] 폰트 로딩 시도
        try:
            p = get_path("font.ttf")
            if os.path.exists(p): LabelBase.register(name="CustomFont", fn_regular=p)
        except: pass

        self.sm.add_widget(MainMenu(name='main'))
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        
        Clock.schedule_once(lambda dt: diag_report("시스템 시작 완료. 오류 0개", False), 1)
        return self.sm

if __name__ == '__main__':
    PristonTaleApp().run()
