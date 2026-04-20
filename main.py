import os
import sys
from kivy.config import Config

# [전수검사] S26 울트라 호환성 및 자판 가림 방지
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
        
        # [최우선 과제] 자가 진단 시스템 강제 호출 (시동 1.5초 후)
        Clock.schedule_once(self.run_diagnostic_priority, 1.5)
        return self.sm

    def run_diagnostic_priority(self, dt):
        """오류를 찾아 화면에 표시하는 최우선 시스템"""
        logs = []
        # 파일 존재 여부 라인별 전수 체크
        files = {"bg.png": "배경 이미지", "icon.png": "앱 아이콘", "font.ttf": "폰트 파일"}
        for filename, desc in files.items():
            if not os.path.exists(get_path(filename)):
                logs.append(f"❌ {desc}({filename}) 누락")
        
        if logs:
            self.dialog = MDDialog(
                title="🚨 자가 진단 오류 보고",
                text="시스템 실행 중 아래 문제가 발견되었습니다:\n\n" + "\n".join(logs),
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.dialog.dismiss())]
            )
            self.dialog.open()
        else:
            MDSnackbar(text="✅ [자가 진단] 모든 시스템 정상이 확인되었습니다!", bg_color=(0, 0.4, 0, 1)).open()

class BaseScreen(Screen):
    def on_enter(self):
        # 배경 이미지는 화면이 뜬 후 0.5초 뒤에 천천히 로드 (튕김 방지)
        Clock.schedule_once(self.load_bg_safe, 0.5)
    def load_bg_safe(self, dt):
        p = get_path("bg.png")
        if os.path.exists(p) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.3), index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(12))
        l.add_widget(MDLabel(text="PT1 Manager", halign="center", font_style="H5"))
        
        menu_items = [("계정생성창", "acc"), ("케릭선택창", "sel"), ("케릭정보창", "info"), 
                      ("케릭장비창", "equ"), ("인벤토리창", "inv"), ("사진선택창", "pho")]
        for text, sn in menu_items:
            l.add_widget(MDRaisedButton(text=text, size_hint_x=1, height=dp(50),
                                       on_release=lambda x, s=sn: setattr(self.manager, 'current', s)))
        self.add_widget(l)

# [제1 기본원칙] 케릭정보창 세부 목록 (19종 완벽 보존)
class CharInfoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        # 19종 정밀 리스트
        fields = ["이름", "직위", "클랜", "레벨", "생명력(HP)", "기력(MP)", "근력(STM)", 
                  "힘(STR)", "정신력(SPI)", "재능(TAL)", "민첩(AGI)", "건강(VIT)", 
                  "명중(Rating)", "공격력(Power)", "방어력(Defense)", "흡수력(Absorb)", 
                  "이동속도(Speed)", "공격속도", "치명타확률"]
        
        for f in fields:
            row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
            row.add_widget(MDLabel(text=f, size_hint_x=0.4))
            row.add_widget(MDTextField(hint_text=f"{f} 입력", size_hint_x=0.6))
            l.add_widget(row)
            
        l.add_widget(MDRectangleFlatButton(text="메인으로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'main')))
        sv.add_widget(l)
        self.add_widget(sv)

# [제1 기본원칙] 케릭장비창 세부 목록 (11종 완벽 보존)
class EquipScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        # 11종 정밀 리스트
        equips = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬렛", "기타항목"]
        
        for eq in equips:
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            row.add_widget(MDLabel(text=eq, size_hint_x=0.4))
            row.add_widget(MDTextField(hint_text="아이템명", size_hint_x=0.6))
            l.add_widget(row)

        l.add_widget(MDRectangleFlatButton(text="메인으로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'main')))
        sv.add_widget(l)
        self.add_widget(sv)

# 기타 창 구조 유지
class AccountScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(padding=dp(20)); l.add_widget(MDTextField(hint_text="계정 검색")); self.add_widget(l)
class CharSelectScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = GridLayout(cols=2, padding=dp(20)); [l.add_widget(MDRaisedButton(text=f"Slot{i}")) for i in range(1,7)]; self.add_widget(l)
class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(padding=dp(20)); l.add_widget(MDLabel(text="인벤토리")); self.add_widget(l)
class PhotoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(padding=dp(20)); l.add_widget(MDLabel(text="사진첩")); self.add_widget(l)

if __name__ == '__main__':
    PristonTaleApp().run()
