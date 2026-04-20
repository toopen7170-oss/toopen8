import os
from kivy.config import Config

# 자판 가림 방지 및 레이아웃 밀림 최적화
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

# [전수검사] 안드로이드 내부 절대 경로 인식 로직
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

# --- 공통 알림 및 팝업 로직 ---
def show_alert(title, text, confirm_fn=None):
    dialog = MDDialog(
        title=title,
        text=text,
        buttons=[
            MDRectangleFlatButton(text="취소", on_release=lambda x: dialog.dismiss()),
            MDRaisedButton(text="확인", on_release=lambda x: [confirm_fn() if confirm_fn else None, dialog.dismiss()]),
        ],
    )
    dialog.open()

# --- 제1 기본원칙: 목록과 창 구조 보존 영역 ---

class BaseScreen(Screen):
    """모든 화면의 공통 배경 및 기본 구조"""
    def on_enter(self):
        # 튕김 방지를 위해 화면에 진입한 후 배경을 불러오는 지연 로딩 적용
        Clock.schedule_once(self.load_resources, 0.1)

    def load_resources(self, dt):
        bg_path = get_path("bg.png")
        if os.path.exists(bg_path) and not any(isinstance(w, Image) for w in self.children):
            bg = Image(source=bg_path, allow_stretch=True, keep_ratio=False, opacity=0.3)
            self.add_widget(bg, index=len(self.children))

class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 메인메뉴 배경은 즉시 로딩 (0.5 투명도)
        bg_path = get_path("bg.png")
        if os.path.exists(bg_path):
            self.add_widget(Image(source=bg_path, allow_stretch=True, keep_ratio=False, opacity=0.8))
            
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        title = MDLabel(text="Priston Tale Manager", halign="center", font_style="H5")
        layout.add_widget(title)
        
        # [제1 원칙] 기본 토대 목록 (절대 보존)
        menus = [
            ("계정생성창", "account_screen"), ("케릭선택창", "char_select_screen"),
            ("케릭정보창", "char_info_screen"), ("케릭장비창", "equip_screen"),
            ("인벤토리창", "inven_screen"), ("사진선택창", "photo_screen")
        ]
        
        for name, sn in menus:
            btn = MDRaisedButton(text=name, size_hint=(1, None), height=dp(55),
                                 on_release=lambda x, screen_name=sn: self.change_screen(screen_name))
            layout.add_widget(btn)
        self.add_widget(layout)
    def change_screen(self, sn): self.manager.current = sn

class AccountScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDTextField(hint_text="계정전체검색바", mode="rectangle", halign="center"))
        layout.add_widget(MDTextField(hint_text="계정ID 입력", mode="helper", halign="center"))
        
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btns.add_widget(MDRaisedButton(text="저장", on_release=lambda x: show_alert("저장", "저장하시겠습니까?")))
        btns.add_widget(MDRaisedButton(text="삭제", on_release=lambda x: show_alert("삭제", "삭제하시겠습니까?")))
        layout.add_widget(btns)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class CharSelectScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10))
        for i in range(1, 7):
            layout.add_widget(MDRaisedButton(text=f"케릭 선택창 {i}", size_hint=(1, 1)))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class CharInfoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = MDScrollView()
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # [제1 원칙] 점주님 요청 그룹 레이아웃
        groups = [[('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
                  [('생명력', ''), ('기력', ''), ('근력', '')],
                  [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
                  [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]]
        
        for group in groups:
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(group)*55), spacing=dp(5))
            for label, _ in group:
                grid.add_widget(MDLabel(text=label, halign="center"))
                grid.add_widget(MDTextField(halign="center", write_tab=False)) # 자동수정 대응
            layout.add_widget(grid)
            layout.add_widget(BoxLayout(size_hint_y=None, height=dp(30))) # 보이지 않는 여백

        layout.add_widget(MDRaisedButton(text="전체삭제", on_release=lambda x: show_alert("삭제", "삭제하시겠습니까?")))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        scroll.add_widget(layout)
        self.add_widget(scroll)

class EquipScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = MDScrollView()
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        for item in items:
            layout.add_widget(MDLabel(text=item, halign="center"))
            layout.add_widget(MDTextField(halign="center"))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        scroll.add_widget(layout)
        self.add_widget(scroll)

class InvenScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDTextField(hint_text="아이템 정보 수정", mode="line", halign="center"))
        layout.add_widget(MDRaisedButton(text="삭제", on_release=lambda x: show_alert("삭제", "삭제하시겠습니까?")))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class PhotoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDLabel(text="사진 관리 (여러장 선택)", halign="center"))
        for t in ["사진 선택", "저장", "삭제"]:
            btn = MDRaisedButton(text=t, size_hint=(1, None))
            if t == "삭제": btn.on_release = lambda: show_alert("삭제", "삭제하시겠습니까?")
            layout.add_widget(btn)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.title = "Priston Tale"
        
        # 폰트 선등록 (실패해도 튕기지 않음)
        font_path = get_path("font.ttf")
        if os.path.exists(font_path):
            try: LabelBase.register(name="CustomFont", fn_regular=font_path)
            except: pass
            
        sm = ScreenManager()
        sm.add_widget(MainMenu(name='main'))
        sm.add_widget(AccountScreen(name='account_screen'))
        sm.add_widget(CharSelectScreen(name='char_select_screen'))
        sm.add_widget(CharInfoScreen(name='char_info_screen'))
        sm.add_widget(EquipScreen(name='equip_screen'))
        sm.add_widget(InvenScreen(name='inven_screen'))
        sm.add_widget(PhotoScreen(name='photo_screen'))
        return sm

if __name__ == '__main__':
    PristonTaleApp().run()
