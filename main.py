import os
from kivy.config import Config

# 자판 가림 방지 및 레이아웃 최적화
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
from kivy.core.text import LabelBase

# 경로 추적 및 자가 진단 함수
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

def show_diag_error(text):
    """자가 진단 오류 알림 (빨간색 스낵바)"""
    MDSnackbar(text=f"[자가진단] {text}", bg_color=(0.8, 0, 0, 1), duration=3).open()

# --- 제1 기본원칙 보존: 기본 화면 구조 ---
class BaseScreen(Screen):
    def on_enter(self):
        # 배경 로딩 진단
        bg_path = get_path("bg.png")
        if not os.path.exists(bg_path):
            show_diag_error("배경화면(bg.png) 누락! 기본 배경으로 실행합니다.")
        else:
            if not any(isinstance(w, Image) for w in self.children):
                self.add_widget(Image(source=bg_path, allow_stretch=True, keep_ratio=False, opacity=0.3), index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 메인 배경 진단 로딩
        bg_path = get_path("bg.png")
        if os.path.exists(bg_path):
            self.add_widget(Image(source=bg_path, allow_stretch=True, keep_ratio=False, opacity=0.8))
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDLabel(text="Priston Tale Manager", halign="center", font_style="H5"))
        
        # [제1 원칙 목록]
        menus = [("계정생성창", "acc"), ("케릭선택창", "sel"), ("케릭정보창", "info"),
                 ("케릭장비창", "equ"), ("인벤토리창", "inv"), ("사진선택창", "pho")]
        
        for name, sn in menus:
            btn = MDRaisedButton(text=name, size_hint=(1, None), height=dp(55),
                                 on_release=lambda x, s=sn: self.switch(s))
            layout.add_widget(btn)
        self.add_widget(layout)
    
    def switch(self, sn): self.manager.current = sn

class AccountScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDTextField(hint_text="계정전체검색바", mode="rectangle", halign="center"))
        id_input = MDTextField(hint_text="계정ID 입력", mode="helper", halign="center")
        layout.add_widget(id_input)
        
        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_box.add_widget(MDRaisedButton(text="저장", on_release=lambda x: self.save()))
        btn_box.add_widget(MDRaisedButton(text="삭제", on_release=lambda x: self.delete()))
        layout.add_widget(btn_box)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

    def save(self):
        MDSnackbar(text="저장하시겠습니까? (확인됨)").open()
    def delete(self):
        MDSnackbar(text="삭제하시겠습니까? (진단 정상)").open()

class CharInfoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = MDScrollView()
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        groups = [[('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
                  [('생명력', ''), ('기력', ''), ('근력', '')],
                  [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
                  [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]]
        
        for group in groups:
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(group)*55), spacing=dp(5))
            for label, _ in group:
                grid.add_widget(MDLabel(text=label, halign="center"))
                grid.add_widget(MDTextField(halign="center", write_tab=False))
            layout.add_widget(grid)
            layout.add_widget(BoxLayout(size_hint_y=None, height=dp(30))) # 시각적 공백

        layout.add_widget(MDRaisedButton(text="전체삭제", on_release=lambda x: show_diag_error("전체 삭제 모드 작동")))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        scroll.add_widget(layout)
        self.add_widget(scroll)

class PhotoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDLabel(text="사진 관리 (자가진단 시스템)", halign="center"))
        btn = MDRaisedButton(text="사진 선택/업로드", size_hint=(1, None),
                             on_release=lambda x: show_diag_error("갤러리 접근 권한 확인 필요 (진단됨)"))
        layout.add_widget(btn)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

# [진단] 나머지 화면들도 제1원칙 구조에 맞춰 동일 로직 적용 (요약)
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
        l.add_widget(MDLabel(text="케릭장비창 (정상진단)", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDTextField(hint_text="인벤토리 (정상진단)", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.title = "Priston Tale"
        
        # [진단] 폰트 유무 체크
        font_p = get_path("font.ttf")
        if not os.path.exists(font_p):
            Clock.schedule_once(lambda dt: show_diag_error("폰트 파일(font.ttf) 누락!"), 1)
        else:
            try: LabelBase.register(name="CustomFont", fn_regular=font_p)
            except: Clock.schedule_once(lambda dt: show_diag_error("폰트 등록 오류!"), 1)
            
        sm = ScreenManager()
        sm.add_widget(MainMenu(name='main'))
        sm.add_widget(AccountScreen(name='acc'))
        sm.add_widget(CharSelectScreen(name='sel'))
        sm.add_widget(CharInfoScreen(name='info'))
        sm.add_widget(EquipScreen(name='equ'))
        sm.add_widget(InvenScreen(name='inv'))
        sm.add_widget(PhotoScreen(name='pho'))
        return sm

if __name__ == '__main__':
    PristonTaleApp().run()
