import os
import sys
from kivy.config import Config

# S26 울트라 가로세로 비율 및 자판 충돌 방지 고정
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
        
        # 기본원칙: 6개 주요 화면 등록
        self.sm.add_widget(MainMenu(name='main'))
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        
        # 자가진단 강제 활성화 (시동 2초 후)
        Clock.schedule_once(self.run_diagnostic, 2.0)
        return self.sm

    def run_diagnostic(self, dt):
        issues = []
        if not os.path.exists(get_path("bg.png")): issues.append("- bg.png(배경) 없음")
        if not os.path.exists(get_path("icon.png")): issues.append("- icon.png(아이콘) 없음")
        if not os.path.exists(get_path("font.ttf")): issues.append("- font.ttf(폰트) 없음")
        
        if issues:
            self.dialog = MDDialog(
                title="[자가진단 보고]",
                text="필수 리소스가 누락되었습니다:\n\n" + "\n".join(issues),
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.dialog.dismiss())]
            )
            self.dialog.open()
        else:
            MDSnackbar(text="[정상] 모든 리소스를 확인했습니다.", bg_color=(0, 0.4, 0, 1)).open()

class BaseScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.set_bg, 0.2)
    def set_bg(self, dt):
        p = get_path("bg.png")
        if os.path.exists(p) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.3), index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(10))
        l.add_widget(MDLabel(text="Priston Tale Manager", halign="center", font_style="H5"))
        for n, sn in [("계정생성", "acc"), ("케릭선택", "sel"), ("케릭정보", "info"), ("케릭장비", "equ"), ("인벤토리", "inv"), ("사진선택", "pho")]:
            l.add_widget(MDRaisedButton(text=n, size_hint_x=1, on_release=lambda x, s=sn: setattr(self.manager, 'current', s)))
        self.add_widget(l)

# [제1 기본원칙] 케릭정보창 (19종)
class CharInfoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        # 19종 리스트: 이름, 직위, 클랜, 레벨, HP, MP, STM, STR, SPI, TAL, AGI, VIT, Rating, Power, Defense, Absorb, Speed + 추가 항목 보존
        info_list = [
            "이름", "직위", "클랜", "레벨", 
            "생명력(HP)", "기력(MP)", "근력(STM)",
            "힘(STR)", "정신력(SPI)", "재능(TAL)", "민첩(AGI)", "건강(VIT)",
            "명중(Rating)", "공격력(Power)", "방어력(Defense)", "흡수력(Absorb)", "이동속도(Speed)",
            "공격속도", "치명타확률"
        ]
        
        for item in info_list:
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            row.add_widget(MDLabel(text=item, size_hint_x=0.4))
            row.add_widget(MDTextField(hint_text=f"{item} 입력", size_hint_x=0.6))
            l.add_widget(row)
        
        l.add_widget(MDRectangleFlatButton(text="메인으로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'main')))
        sv.add_widget(l)
        self.add_widget(sv)

# [제1 기본원칙] 케릭장비창 (11종)
class EquipScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        # 11종 리스트: 무기1, 무기2, 갑옷, 방패, 장갑, 부츠, 암릿, 링1, 링2, 아뮬렛, 기타
        equip_list = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬렛", "기타항목"]
        
        for eq in equip_list:
            row = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            row.add_widget(MDLabel(text=eq, size_hint_x=0.4))
            row.add_widget(MDTextField(hint_text="장착 아이템", size_hint_x=0.6))
            l.add_widget(row)

        l.add_widget(MDRectangleFlatButton(text="메인으로", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'main')))
        sv.add_widget(l)
        self.add_widget(sv)

# 나머지 화면 (구조 보존)
class AccountScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(padding=dp(20)); l.add_widget(MDTextField(hint_text="ID 검색")); self.add_widget(l)
class CharSelectScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = GridLayout(cols=2, padding=dp(20)); [l.add_widget(MDRaisedButton(text=f"케릭{i}")) for i in range(1,7)]; self.add_widget(l)
class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(padding=dp(20)); l.add_widget(MDLabel(text="인벤토리 준비 중")); self.add_widget(l)
class PhotoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw); l = BoxLayout(padding=dp(20)); l.add_widget(MDLabel(text="사진첩 준비 중")); self.add_widget(l)

if __name__ == '__main__':
    PristonTaleApp().run()
