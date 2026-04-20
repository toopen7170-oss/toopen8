import os
from kivy.config import Config

# S26 울트라 최적화: 자판이 올라와도 입력창을 가리지 않도록 설정
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
        
        # [제1원칙] 모든 화면 등록
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        
        # [자가 진단] 초기 성공 코드의 안정성을 위해 1초 뒤 실행
        Clock.schedule_once(self.check_system, 1.0)
        return self.sm

    def check_system(self, dt):
        errors = []
        if not os.path.exists(get_path("icon.png")): errors.append("- 아이콘(icon.png) 누락")
        if not os.path.exists(get_path("bg.png")): errors.append("- 배경(bg.png) 누락")
        if not os.path.exists(get_path("font.ttf")): errors.append("- 폰트(font.ttf) 누락")
        
        if errors:
            self.dialog = MDDialog(
                title="🚨 자가 진단 알림",
                text="일부 리소스가 준비되지 않았습니다:\n\n" + "\n".join(errors),
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.dialog.dismiss())]
            )
            self.dialog.open()

# --- 배경 처리 클래스 ---
class BaseScreen(Screen):
    def on_enter(self):
        p = get_path("bg.png")
        if os.path.exists(p) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.2), index=len(self.children))

# 1. 계정 생성창
class AccountScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="계정 관리", halign="center", font_style="H5"))
        l.add_widget(MDTextField(hint_text="계정 전체 검색 바", mode="rectangle"))
        
        self.acc_name = MDTextField(hint_text="새 계정ID 입력")
        l.add_widget(self.acc_name)
        
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        row.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5, on_release=lambda x: self.ask("저장하겠습니까?")))
        row.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5, on_release=lambda x: self.ask("삭제하겠습니까?")))
        l.add_widget(row)
        
        # 목록 클릭 시 케릭선택창 이동
        l.add_widget(MDRectangleFlatButton(text="[계정 목록] toopen8 (클릭 시 이동)", size_hint_x=1, 
                                          on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        l.add_widget(BoxLayout())
        self.add_widget(l)

    def ask(self, msg):
        MDDialog(title="확인", text=msg, buttons=[MDRaisedButton(text="예"), MDRaisedButton(text="아니오")]).open()

# 2. 케릭 선택창 (6개)
class CharSelectScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        grid = GridLayout(cols=2, spacing=dp(15))
        for i in range(1, 7):
            grid.add_widget(MDRaisedButton(text=f"Slot {i}", size_hint=(1, 1), 
                                          on_release=lambda x: setattr(self.manager, 'current', 'info')))
        l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

# 3. 케릭정보창 (19종 정밀 그룹화)
class CharInfoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        # 19종 그룹
        groups = [
            [('이름',''), ('직위',''), ('클랜',''), ('레벨','')],
            [('생명력',''), ('기력',''), ('근력','')],
            [('힘',''), ('정신력',''), ('재능',''), ('민첩',''), ('건강','')],
            [('명중',''), ('공격',''), ('방어',''), ('흡수',''), ('속도','')]
        ]
        
        for g in groups:
            for label, val in g:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(MDLabel(text=label, size_hint_x=0.4, halign="center"))
                row.add_widget(MDTextField(text=val, size_hint_x=0.6, halign="center"))
                l.add_widget(row)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 비가시적 간격

        l.add_widget(MDRaisedButton(text="전체 삭제", size_hint_x=1, md_bg_color=(1,0,0,1), 
                                   on_release=lambda x: self.ask_del()))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

    def ask_del(self):
        MDDialog(title="경고", text="삭제하겠습니까?", buttons=[MDRaisedButton(text="취소"), MDRaisedButton(text="삭제")]).open()

# 4. 케릭장비창 (11종 고정)
class EquipScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(50))
            row.add_widget(MDLabel(text=item, size_hint_x=0.4, halign="center"))
            row.add_widget(MDTextField(size_hint_x=0.6, halign="center"))
            l.add_widget(row)
        
        l.add_widget(MDRaisedButton(text="전체 삭제", size_hint_x=1, md_bg_color=(1,0,0,1)))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

# 5. 인벤토리 및 6. 사진 (구조 유지)
class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(padding=dp(20))
        l.add_widget(MDLabel(text="인벤토리 (한 줄씩 클릭하여 수정)", halign="center"))
        self.add_widget(l)

class PhotoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="사진 선택/업로드/다운로드", halign="center"))
        l.add_widget(MDRaisedButton(text="사진 선택 (다중)", size_hint_x=1))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

if __name__ == '__main__':
    PristonTaleApp().run()
