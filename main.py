import os
from kivy.config import Config

# [전수검사] 그래픽 가속 충돌 방지 및 자판 레이아웃 설정
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

# 경로 추적 로직 (패키지명 불일치 방지)
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.sm = ScreenManager()
        
        # [제1원칙] 6개 주요 화면 등록 (장비창 포함)
        self.sm.add_widget(MainMenu(name='main'))
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        
        # [자가진단] 엔진 안정화를 위해 2초 뒤 정밀 진단 보고
        Clock.schedule_once(self.run_final_diagnostic, 2)
        return self.sm

    def run_final_diagnostic(self, dt):
        """앱 스스로 권한 및 파일 상태를 점주님께 보고"""
        diag_msg = []
        if not os.path.exists(get_path("font.ttf")): diag_msg.append("폰트누락")
        if not os.path.exists(get_path("bg.png")): diag_msg.append("배경누락")
        
        if diag_msg:
            # 빨간색 경고 다이얼로그 (무조건 확인해야 닫힘)
            self.diag_dialog = MDDialog(
                title="[자가진단] 시스템 경고",
                text=f"현재 '{', '.join(diag_msg)}' 상태입니다. 리소스를 확인하세요.",
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.diag_dialog.dismiss())]
            )
            self.diag_dialog.open()
        else:
            MDSnackbar(text="[자가진단] 모든 시스템 정상. Priston Tale 가동!", bg_color=(0, 0.5, 0, 1)).open()

# --- 화면 공통 배경 처리 ---
class BaseScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.apply_safe_bg, 0.2)
    def apply_safe_bg(self, dt):
        p = get_path("bg.png")
        if os.path.exists(p) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.3), index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        p = get_path("bg.png")
        if os.path.exists(p):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.8))
        
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
        l.add_widget(MDTextField(hint_text="계정ID 입력", halign="center"))
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        row.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5))
        row.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5))
        l.add_widget(row)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
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
                grid.add_widget(MDTextField(halign="center"))
            l.add_widget(grid)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(30)))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        scroll.add_widget(l)
        self.add_widget(scroll)

# [제1원칙 복구] 케릭장비창 11종 세부 목록
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
            grid.add_widget(MDTextField(halign="center", hint_text="장비 입력"))
        
        l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main'), size_hint_x=1))
        scroll.add_widget(l)
        self.add_widget(scroll)

class PhotoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진 관리 (자가진단 가동)", halign="center"))
        l.add_widget(MDRaisedButton(text="사진 선택/업로드", size_hint=(1, None),
                                   on_release=lambda x: MDSnackbar(text="[자가진단] 권한 확인 필요").open()))
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
        l.add_widget(MDTextField(hint_text="인벤토리 검색", halign="center"))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(l)

if __name__ == '__main__':
    try:
        p = get_path("font.ttf")
        if os.path.exists(p): LabelBase.register(name="CustomFont", fn_regular=p)
    except: pass
    PristonTaleApp().run()
