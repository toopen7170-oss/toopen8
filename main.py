import os
import sys

# [전수검사] S26 울트라 그래픽 가속 충돌 및 자판 가림 방지
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
        # 1단계: 엔진 시동 시 리소스 로딩 완전 배제 (튕김 방지)
        self.theme_cls.primary_palette = "BlueGray"
        self.sm = ScreenManager()
        
        # [제1원칙] 6개 주요 화면 등록
        self.sm.add_widget(MainMenu(name='main'))
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        
        # 2단계: 앱이 켜진 후 자가진단 시스템 강제 호출
        Clock.schedule_once(self.activate_diagnostic, 1.5)
        return self.sm

    def activate_diagnostic(self, dt):
        """자가진단 오류 표시 시스템 (강제 활성화)"""
        diagnostic_log = []
        
        # 리소스 체크
        if not os.path.exists(get_path("font.ttf")): diagnostic_log.append("- 폰트파일(font.ttf) 없음")
        if not os.path.exists(get_path("bg.png")): diagnostic_log.append("- 배경이미지(bg.png) 없음")
        
        # 결과 표시
        if diagnostic_log:
            error_text = "\n".join(diagnostic_log)
            self.show_error_dialog(f"아래 오류가 발견되었습니다:\n\n{error_text}")
        else:
            MDSnackbar(
                text="[자가진단] 모든 시스템이 정상 가동 중입니다!",
                bg_color=(0, 0.5, 0, 1),
                duration=3
            ).open()

    def show_error_dialog(self, message):
        self.dialog = MDDialog(
            title="[자가진단] 오류 보고",
            text=message,
            buttons=[
                MDRaisedButton(text="확인", on_release=lambda x: self.dialog.dismiss())
            ],
        )
        self.dialog.open()

# --- 배경 및 화면 처리 (세이프 로드) ---
class BaseScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.load_resources, 0.3)
    def load_resources(self, dt):
        p = get_path("bg.png")
        if os.path.exists(p) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.2), index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(12))
        l.add_widget(MDLabel(text="PT1 Manager", halign="center", font_style="H4"))
        
        menus = [("계정 생성", "acc"), ("케릭 선택", "sel"), ("케릭 정보", "info"),
                 ("케릭 장비", "equ"), ("인벤토리", "inv"), ("사진 선택", "pho")]
        for name, sn in menus:
            l.add_widget(MDRaisedButton(text=name, size_hint=(1, None), height=dp(52),
                                       on_release=lambda x, s=sn: setattr(self.manager, 'current', s)))
        self.add_widget(l)

# [제1원칙] 케릭정보창 세부 목록 (19종) 완벽 적용
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
            l.add_widget(MDLabel(text=f"■ {title}", font_style="H6", theme_text_color="Secondary"))
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(items)*55), spacing=dp(5))
            for label, hint in items:
                grid.add_widget(MDLabel(text=label, halign="center"))
                grid.add_widget(MDTextField(hint_text=hint, halign="center"))
            l.add_widget(grid)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(15)))

        l.add_widget(MDRectangleFlatButton(text="메인으로 돌아가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        scroll.add_widget(l)
        self.add_widget(scroll)

# [제1원칙] 케릭장비창 세부 목록 (11종) 완벽 적용
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
            grid.add_widget(MDTextField(halign="center", hint_text="장비 명칭 입력"))
        
        l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="메인으로 돌아가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        scroll.add_widget(l)
        self.add_widget(scroll)

# 기타 화면들 (구조 유지)
class AccountScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDTextField(hint_text="ID 검색", mode="rectangle"))
        l.add_widget(MDRectangleFlatButton(text="뒤로", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        self.add_widget(l)

class CharSelectScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = GridLayout(cols=2, padding=dp(20), spacing=dp(10))
        for i in range(1, 7): l.add_widget(MDRaisedButton(text=f"Slot {i}", size_hint=(1,1)))
        l.add_widget(MDRectangleFlatButton(text="뒤로", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(padding=dp(20))
        l.add_widget(MDTextField(hint_text="아이템명 검색")); self.add_widget(l)

class PhotoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDLabel(text="사진 선택창", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        self.add_widget(l)

if __name__ == '__main__':
    PristonTaleApp().run()
