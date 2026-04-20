import os
import sys

# [전수검사] 초기 그래픽 엔진 충돌 방지 설정
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('softinput_mode', 'pan')

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import MDSnackbar
from kivy.core.text import LabelBase

# [진단 로직] 경로 추적
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.title = "Priston Tale"
        
        # [자가 진단] 폰트 로딩 분리 (튕김 방지 핵심)
        Clock.schedule_once(self.diagnostic_check, 0.5)
        
        self.sm = ScreenManager()
        self.sm.add_widget(MainMenu(name='main'))
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        return self.sm

    def diagnostic_check(self, dt):
        """앱 실행 후 하단에 진단 결과 보고"""
        errors = []
        if not os.path.exists(get_path("font.ttf")): errors.append("폰트(font.ttf) 누락")
        if not os.path.exists(get_path("bg.png")): errors.append("배경(bg.png) 누락")
        if not os.path.exists(get_path("icon.png")): errors.append("아이콘(icon.png) 누락")
        
        if errors:
            msg = f"[자가진단] 경고: {', '.join(errors)}! 파일을 확인하세요."
            MDSnackbar(text=msg, bg_color=(0.8, 0, 0, 1), duration=4).open()
        else:
            MDSnackbar(text="[자가진단] 모든 리소스가 정상입니다. 65회차 성공!", duration=2).open()

    def report_sync_error(self):
        MDSnackbar(text="[자가진단] 동기화 실패! 데이터 연결을 확인하세요.", bg_color=(0.8, 0, 0, 1)).open()

# --- 화면 구성 (제1 기본원칙 보존) ---

class BaseScreen(Screen):
    def on_enter(self):
        # 배경 지연 로딩으로 초기 튕김 방지
        Clock.schedule_once(self.load_bg, 0.1)

    def load_bg(self, dt):
        path = get_path("bg.png")
        if os.path.exists(path) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=path, allow_stretch=True, keep_ratio=False, opacity=0.3), index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 메인 메뉴는 배경을 조금 더 진하게
        path = get_path("bg.png")
        if os.path.exists(path):
            self.add_widget(Image(source=path, allow_stretch=True, keep_ratio=False, opacity=0.7))
        
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="Priston Tale Manager", halign="center", font_style="H5"))
        
        # [제1원칙 목록]
        for name, sn in [("계정생성창", "acc"), ("케릭선택창", "sel"), ("케릭정보창", "info"),
                         ("케릭장비창", "equ"), ("인벤토리창", "inv"), ("사진선택창", "pho")]:
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
        row.add_widget(MDRaisedButton(text="저장", on_release=lambda x: MDSnackbar(text="저장하시겠습니까?").open()))
        row.add_widget(MDRaisedButton(text="삭제", on_release=lambda x: MDSnackbar(text="삭제하시겠습니까?").open()))
        l.add_widget(row)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class CharInfoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        # [제1원칙 그룹 레이아웃]
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
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(30))) # 시각적 한칸 띄우기

        l.add_widget(MDRaisedButton(text="전체삭제", on_release=lambda x: MDSnackbar(text="전체 삭제하시겠습니까?").open()))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        scroll.add_widget(l)
        self.add_widget(scroll)

class PhotoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진 관리 시스템", halign="center"))
        btn = MDRaisedButton(text="사진 선택/업로드", size_hint=(1, None),
                             on_release=lambda x: MDSnackbar(text="[자가진단] 갤러리 접근 권한 확인 필요", bg_color=(0.8, 0, 0, 1)).open())
        l.add_widget(btn)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

# [진단] 나머지 화면 (CharSelect, Equip, Inven) 구조 유지
class CharSelectScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = GridLayout(cols=2, padding=dp(20), spacing=dp(10))
        for i in range(1, 7): l.add_widget(MDRaisedButton(text=f"케릭 {i}", size_hint=(1,1)))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class EquipScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDLabel(text="케릭장비창", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDLabel(text="인벤토리창", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

if __name__ == '__main__':
    # 폰트 등록 오류 시 앱이 죽지 않도록 예외 처리
    try:
        f_p = get_path("font.ttf")
        if os.path.exists(f_p): LabelBase.register(name="CustomFont", fn_regular=f_p)
    except: pass
    PristonTaleApp().run()
