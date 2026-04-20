import os
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivy.core.text import LabelBase

# 폰트 등록 (보내주신 font.ttf 적용)
# 파일이 없을 경우를 대비해 예외처리를 두었으나, 같은 폴더에 두시면 적용됩니다.
font_path = "font.ttf"
if os.path.exists(font_path):
    LabelBase.register(name="CustomFont", fn_regular=font_path)

# 배경화면 위젯 공통 설정
class BackgroundLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        with self.canvas.before:
            # bg.png를 배경으로 꽉 채움
            self.bg_image = Image(
                source='bg.png',
                allow_stretch=True,
                keep_ratio=False,
                opacity=0.6  # 글씨가 잘 보이도록 배경 투명도 조절
            )
            self.add_widget(self.bg_image)

# 1. 메인 메뉴 화면 (기본 토대 목록 고정)
class MainMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 배경 레이아웃 생성
        root = BoxLayout(orientation='vertical')
        
        # 배경 이미지 배치
        bg = Image(source='bg.png', allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
        self.add_widget(bg)
        
        # 실제 콘텐츠 레이아웃 (배경 위에 띄움)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        title = MDLabel(
            text="PT1 Manager 기본 토대", 
            halign="center", 
            font_style="H5",
            font_name="CustomFont" if os.path.exists(font_path) else "Roboto"
        )
        layout.add_widget(title)
        
        # 제1 원칙: 목록과 창 구조 절대 보존
        menus = [
            ("계정생성창", "account_screen"),
            ("케릭선택창", "char_select_screen"),
            ("케릭정보창", "char_info_screen"),
            ("케릭장비창", "equip_screen"),
            ("인벤토리창", "inven_screen"),
            ("사진선택창", "photo_screen")
        ]
        
        for name, screen_name in menus:
            btn = MDRaisedButton(
                text=name, 
                size_hint=(1, None), 
                height=dp(55),
                font_name="CustomFont" if os.path.exists(font_path) else "Roboto",
                on_release=lambda x, sn=screen_name: self.change_screen(sn)
            )
            layout.add_widget(btn)
        
        self.add_widget(layout)

    def change_screen(self, screen_name):
        self.manager.current = screen_name

# 2. 계정생성창
class AccountScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Image(source='bg.png', allow_stretch=True, keep_ratio=False, opacity=0.4))
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        layout.add_widget(MDTextField(hint_text="계정전체검색바", mode="rectangle"))
        layout.add_widget(MDTextField(hint_text="계정ID선택창", mode="helper"))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

# 3. 케릭선택창 (6개의 선택창)
class CharSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Image(source='bg.png', allow_stretch=True, keep_ratio=False, opacity=0.4))
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10))
        for i in range(1, 7):
            layout.add_widget(MDRaisedButton(text=f"케릭 선택창 {i}", size_hint=(1, 1)))
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

# 4. 케릭정보창 (요청하신 상세 구조 고정)
class CharInfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Image(source='bg.png', allow_stretch=True, keep_ratio=False, opacity=0.3))
        scroll = MDScrollView()
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # 지시하신 그룹화 및 간격 유지
        groups = [
            [('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
            [('생명력', ''), ('기력', ''), ('근력', '')],
            [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
            [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]
        ]
        
        for group in groups:
            grid = GridLayout(cols=2, size_hint_y=None, height=dp(len(group)*45), spacing=dp(5))
            for label, value in group:
                grid.add_widget(MDLabel(text=label, font_name="CustomFont" if os.path.exists(font_path) else "Roboto"))
                grid.add_widget(MDTextField(text=value, size_hint_y=None, height=dp(30)))
            layout.add_widget(grid)
            layout.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 화면에 안보이는 한칸 띄기

        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        scroll.add_widget(layout)
        self.add_widget(scroll)
    def back(self, *args): self.manager.current = 'main'

# 5. 케릭장비창
class EquipScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Image(source='bg.png', allow_stretch=True, keep_ratio=False, opacity=0.4))
        scroll = MDScrollView()
        layout = GridLayout(cols=2, padding=dp(20), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        for item in items:
            layout.add_widget(MDLabel(text=item, font_name="CustomFont" if os.path.exists(font_path) else "Roboto"))
            layout.add_widget(MDTextField(hint_text="장비 정보"))
            
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        scroll.add_widget(layout)
        self.add_widget(scroll)
    def back(self, *args): self.manager.current = 'main'

# 6. 인벤토리창 (수정/저장/삭제)
class InvenScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Image(source='bg.png', allow_stretch=True, keep_ratio=False, opacity=0.4))
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # 저장/삭제 버튼이 포함된 한 줄 예시
        row = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        row.add_widget(MDTextField(text="아이템 정보 수정", mode="line"))
        row.add_widget(MDRaisedButton(text="저장", size_hint_x=None, width=dp(60)))
        row.add_widget(MDRaisedButton(text="삭제", size_hint_x=None, width=dp(60)))
        
        layout.add_widget(row)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

# 7. 사진선택창 (다중선택/업로드/다운로드)
class PhotoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Image(source='bg.png', allow_stretch=True, keep_ratio=False, opacity=0.4))
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        layout.add_widget(MDLabel(text="사진 관리 시스템", halign="center", font_style="H6"))
        layout.add_widget(MDRaisedButton(text="핸드폰 사진 선택(여러장)", size_hint=(1, None)))
        layout.add_widget(MDRaisedButton(text="업로드", size_hint=(1, None)))
        layout.add_widget(MDRaisedButton(text="다운로드", size_hint=(1, None)))
        
        btn_box = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        btn_box.add_widget(MDRaisedButton(text="저장", size_hint_x=0.5))
        btn_box.add_widget(MDRaisedButton(text="삭제", size_hint_x=0.5))
        
        layout.add_widget(btn_box)
        layout.add_widget(MDRectangleFlatButton(text="뒤로가기", on_release=self.back))
        self.add_widget(layout)
    def back(self, *args): self.manager.current = 'main'

class PT1ManagerApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        sm = ScreenManager()
        # 모든 창 등록
        sm.add_widget(MainMenu(name='main'))
        sm.add_widget(AccountScreen(name='account_screen'))
        sm.add_widget(CharSelectScreen(name='char_select_screen'))
        sm.add_widget(CharInfoScreen(name='char_info_screen'))
        sm.add_widget(EquipScreen(name='equip_screen'))
        sm.add_widget(InvenScreen(name='inven_screen'))
        sm.add_widget(PhotoScreen(name='photo_screen'))
        return sm

if __name__ == '__main__':
    PT1ManagerApp().run()
