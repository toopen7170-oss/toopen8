import os
from kivy.config import Config

# 자판 가림 방지 및 입력 최적화
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('softinput_mode', 'below_target')

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar
from kivy.core.text import LabelBase

# [필승 로직] 안드로이드 리소스 절대 경로 강제 인식
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

# 폰트 등록 (유실 시에도 앱 실행 유지)
font_file = get_path("font.ttf")
HAS_FONT = False
if os.path.exists(font_file):
    try:
        LabelBase.register(name="CustomFont", fn_regular=font_file)
        HAS_FONT = True
    except: pass

def add_bg(screen, opacity_val=0.4):
    bg_file = get_path("bg.png")
    if os.path.exists(bg_file):
        screen.add_widget(Image(source=bg_file, allow_stretch=True, keep_ratio=False, opacity=opacity_val))

def show_alert(title, text, on_confirm):
    dialog = MDDialog(
        title=title,
        text=text,
        buttons=[
            MDRectangleFlatButton(text="취소", on_release=lambda x: dialog.dismiss()),
            MDRaisedButton(text="확인", on_release=lambda x: [on_confirm(), dialog.dismiss()]),
        ],
    )
    dialog.open()

# --- 제1 기본원칙 준수 레이아웃 ---

class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self, 1.0)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        title = MDLabel(text="Priston Tale Manager", halign="center", font_style="H5")
        if HAS_FONT: title.font_name = "CustomFont"
        layout.add_widget(title)
        
        menus = [("계정생성창", "account_screen"), ("케릭선택창", "char_select_screen"),
                 ("케릭정보창", "char_info_screen"), ("케릭장비창", "equip_screen"),
                 ("인벤토리창", "inven_screen"), ("사진선택창", "photo_screen")]
        
        for name, screen_name in menus:
            btn = MDRaisedButton(text=name, size_hint=(1, None), height=dp(55))
            btn.bind(on_release=lambda x, sn=screen_name: self.change_screen(sn))
            if HAS_FONT: btn.font_name = "CustomFont"
            layout.add_widget(btn)
        self.add_widget(layout)
    def change_screen(self, screen_name): self.manager.current = screen_name

class AccountScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDTextField(hint_text="계정전체검색바", mode="rectangle"))
        layout.add_widget(MDTextField(hint_text="계정ID 입력", mode="helper"))
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_row.add_widget(MDRaisedButton(text="저장", on_release=lambda x: show_alert("저장", "저장하시겠습니까?", lambda: None)))
        btn_row.add_widget(MDRaisedButton(text="삭제", on_release=lambda x: show_alert("삭제", "삭제하시겠습니까?", lambda: None)))
        layout.add_widget(btn_row)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class CharSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10))
        for i in range(1, 7):
            layout.add_widget(MDRaisedButton(text=f"케릭 {i}", size_hint=(1, 1)))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class CharInfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self, 0.2)
        scroll = MDScrollView()
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        groups = [[('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
                  [('생명력', ''), ('기력', ''), ('근력', '')],
                  [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
                  [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]]
        
        for group in groups:
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(group)*55), spacing=dp(5))
            for label, value in group:
                lbl = MDLabel(text=label, halign="center")
                if HAS_FONT: lbl.font_name = "CustomFont"
                grid.add_widget(lbl)
                grid.add_widget(MDTextField(text=value, halign="center"))
            layout.add_widget(grid)
            layout.add_widget(BoxLayout(size_hint_y=None, height=dp(30))) # 투명 여백

        layout.add_widget(MDRaisedButton(text="전체삭제", on_release=lambda x: show_alert("삭제", "전체 삭제하시겠습니까?", lambda: None)))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        scroll.add_widget(layout)
        self.add_widget(scroll)

class EquipScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        scroll = MDScrollView()
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        for item in items:
            lbl = MDLabel(text=item, halign="center")
            if HAS_FONT: lbl.font_name = "CustomFont"
            layout.add_widget(lbl)
            layout.add_widget(MDTextField(halign="center"))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        scroll.add_widget(layout)
        self.add_widget(scroll)

class InvenScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDTextField(hint_text="아이템 정보 수정", mode="line", halign="center"))
        layout.add_widget(MDRaisedButton(text="삭제", on_release=lambda x: show_alert("삭제", "삭제하시겠습니까?", lambda: None)))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class PhotoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDLabel(text="사진 관리", halign="center"))
        for t in ["사진 선택", "저장", "삭제"]:
            btn = MDRaisedButton(text=t, size_hint=(1, None))
            if t == "삭제": btn.bind(on_release=lambda x: show_alert("삭제", "삭제하시겠습니까?", lambda: None))
            layout.add_widget(btn)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=lambda x: setattr(self.manager, 'current', 'main')))
        self.add_widget(layout)

class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        self.title = "Priston Tale"
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
