import os
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivy.core.text import LabelBase

# [안전장치] 폰트 등록 (font.ttf 파일이 없어도 앱 실행 유지)
font_path = "font.ttf"
if os.path.exists(font_path):
    try:
        LabelBase.register(name="CustomFont", fn_regular=font_path)
        HAS_FONT = True
    except:
        HAS_FONT = False
else:
    HAS_FONT = False

# [공통 기능] 배경 이미지(bg.png) 적용 함수
def add_bg(screen, opacity_val=0.4):
    if os.path.exists("bg.png"):
        screen.add_widget(Image(source='bg.png', allow_stretch=True, keep_ratio=False, opacity=opacity_val))

# 1. 메인 메뉴 화면 (제1 원칙: 목록 구조 절대 보존)
class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self, 1.0) # 메인 배경은 선명하게
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        title = MDLabel(text="Priston Tale Manager", halign="center", font_style="H5")
        if HAS_FONT: title.font_name = "CustomFont"
        layout.add_widget(title)
        
        # 목록은 절대로 수정하지 않음
        menus = [("계정생성창", "account_screen"), ("케릭선택창", "char_select_screen"),
                 ("케릭정보창", "char_info_screen"), ("케릭장비창", "equip_screen"),
                 ("인벤토리창", "inven_screen"), ("사진선택창", "photo_screen")]
        
        for name, screen_name in menus:
            btn = MDRaisedButton(text=name, size_hint=(1, None), height=dp(55),
                                 on_release=lambda x, sn=screen_name: self.change_screen(sn))
            if HAS_FONT: btn.font_name = "CustomFont"
            layout.add_widget(btn)
        self.add_widget(layout)

    def change_screen(self, screen_name):
        self.manager.current = screen_name

# 2. 계정생성창 (ID선택, 검색바)
class AccountScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDTextField(hint_text="계정전체검색바", mode="rectangle"))
        layout.add_widget(MDTextField(hint_text="계정ID선택창", mode="helper"))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

# 3. 케릭선택창 (6개 선택 영역)
class CharSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10))
        for i in range(1, 7):
            layout.add_widget(MDRaisedButton(text=f"케릭 선택창 {i}", size_hint=(1, 1)))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

# 4. 케릭정보창 (요청하신 상세 그룹 레이아웃)
class CharInfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self, 0.3)
        scroll = MDScrollView()
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        groups = [[('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
                  [('생명력', ''), ('기력', ''), ('근력', '')],
                  [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
                  [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]]
        
        for group in groups:
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(group)*45), spacing=dp(5))
            for label, value in group:
                lbl = MDLabel(text=label)
                if HAS_FONT: lbl.font_name = "CustomFont"
                grid.add_widget(lbl)
                grid.add_widget(MDTextField(text=value, size_hint_y=None, height=dp(30)))
            layout.add_widget(grid)
            layout.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 투명 여백
            
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        scroll.add_widget(layout)
        self.add_widget(scroll)
    def back(self, *args): self.manager.current = 'main'

# 5. 케릭장비창 (한손무기~기타)
class EquipScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        scroll = MDScrollView()
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        for item in items:
            lbl = MDLabel(text=item)
            if HAS_FONT: lbl.font_name = "CustomFont"
            layout.add_widget(lbl)
            layout.add_widget(MDTextField(hint_text="정보 입력"))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        scroll.add_widget(layout)
        self.add_widget(scroll)
    def back(self, *args): self.manager.current = 'main'

# 6. 인벤토리창 (저장/삭제 및 수정)
class InvenScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        row = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        row.add_widget(MDTextField(text="아이템 정보 수정", mode="line"))
        row.add_widget(MDRaisedButton(text="저장"))
        row.add_widget(MDRaisedButton(text="삭제"))
        layout.add_widget(row)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

# 7. 사진선택창 (다중선택/업다운로드/저장삭제)
class PhotoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_bg(self)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDLabel(text="사진 관리 (Priston Tale)", halign="center"))
        for t in ["사진 선택(여러장)", "업로드", "다운로드", "저장", "삭제"]:
            layout.add_widget(MDRaisedButton(text=t, size_hint=(1, None)))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

# [앱 실행부] 이름: PristonTaleApp
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
