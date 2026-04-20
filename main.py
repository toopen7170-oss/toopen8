import os
import sys
from kivy.config import Config

# [전수검사] S26 울트라 가로세로비 유지 및 자판 위로 입력창 자동 올림
Config.set('kivy', 'keyboard_mode', 'system_and_dock')
Config.set('softinput_mode', 'pan')

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar
from kivy.core.window import Window

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def get_path(filename):
    return os.path.join(BASE_PATH, filename)

class PristonTaleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Amber"
        self.sm = ScreenManager(transition=FadeTransition())
        
        # [제1원칙] 6개 주요 화면 등록
        self.sm.add_widget(AccountScreen(name='acc'))
        self.sm.add_widget(CharSelectScreen(name='sel'))
        self.sm.add_widget(CharInfoScreen(name='info'))
        self.sm.add_widget(EquipScreen(name='equ'))
        self.sm.add_widget(InvenScreen(name='inv'))
        self.sm.add_widget(PhotoScreen(name='pho'))
        
        # [최우선] 자가 진단 시스템 (시동 1.5초 후 강제 보고)
        Clock.schedule_once(self.run_final_diagnostic, 1.5)
        return self.sm

    def run_final_diagnostic(self, dt):
        logs = []
        if not os.path.exists(get_path("icon.png")): logs.append("❌ 아이콘(icon.png) 누락")
        if not os.path.exists(get_path("bg.png")): logs.append("❌ 배경(bg.png) 누락")
        if not os.path.exists(get_path("font.ttf")): logs.append("❌ 폰트(font.ttf) 누락")
        
        if logs:
            self.diag_dialog = MDDialog(
                title="🚨 자가 진단 보고",
                text="시스템 환경에 문제가 발견되었습니다:\n\n" + "\n".join(logs),
                buttons=[MDRaisedButton(text="확인", on_release=lambda x: self.diag_dialog.dismiss())]
            )
            self.diag_dialog.open()
        else:
            MDSnackbar(text="✅ 모든 시스템 및 리소스 정상 가동!", bg_color=(0.1, 0.5, 0.1, 1)).open()

# --- 배경 공통 클래스 ---
class BaseScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self.set_bg, 0.1)
    def set_bg(self, dt):
        p = get_path("bg.png")
        if os.path.exists(p) and not any(isinstance(w, Image) for w in self.children):
            self.add_widget(Image(source=p, allow_stretch=True, keep_ratio=False, opacity=0.25), index=len(self.children))

# 1. 계정생성창
class AccountScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="계정 관리 시스템", halign="center", font_style="H5"))
        
        # 전체 검색바
        self.search_bar = MDTextField(hint_text="계정 전체 검색", mode="rectangle", icon_right="magnify")
        l.add_widget(self.search_bar)
        
        # 계정 ID 생성부
        self.acc_input = MDTextField(hint_text="새 계정ID 입력", helper_text="생성할 이름을 입력하세요", helper_text_mode="on_focus")
        l.add_widget(self.acc_input)
        
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_row.add_widget(MDRaisedButton(text="계정 생성", size_hint_x=0.5, on_release=self.confirm_save))
        btn_row.add_widget(MDRaisedButton(text="계정 삭제", size_hint_x=0.5, md_bg_color=(0.8, 0.2, 0.2, 1), on_release=self.confirm_delete))
        l.add_widget(btn_row)
        
        # 계정 리스트 (임시)
        l.add_widget(MDLabel(text="[등록된 계정 목록]", font_style="Caption"))
        self.acc_list = MDRectangleFlatButton(text="test_account_01 (클릭 시 케릭선택 이동)", size_hint_x=1, 
                                             on_release=lambda x: setattr(self.manager, 'current', 'sel'))
        l.add_widget(self.acc_list)
        l.add_widget(BoxLayout()) # 여백
        self.add_widget(l)

    def confirm_save(self, x):
        MDDialog(title="알림", text="저장하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog_close(x)),
            MDRaisedButton(text="저장", on_release=lambda x: self.dialog_close(x))
        ]).open()

    def confirm_delete(self, x):
        MDDialog(title="경고", text="삭제하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: self.dialog_close(x)),
            MDRaisedButton(text="삭제", md_bg_color=(0.8, 0.2, 0.2, 1), on_release=lambda x: self.dialog_close(x))
        ]).open()

    def dialog_close(self, instance):
        instance.parent.parent.parent.parent.dismiss()

# 2. 케릭선택창 (6개 슬롯)
class CharSelectScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        l.add_widget(MDLabel(text="케릭 선택 (6 Slot)", halign="center", font_style="H6"))
        
        grid = GridLayout(cols=2, spacing=dp(15))
        for i in range(1, 7):
            btn = MDRaisedButton(text=f"Slot {i}\n(미설정)", size_hint=(1, 1), 
                                 on_release=self.go_to_char_menu)
            grid.add_widget(btn)
        l.add_widget(grid)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'acc')))
        self.add_widget(l)

    def go_to_char_menu(self, x):
        # 케릭 메뉴 팝업 (정보, 장비, 인벤, 사진)
        self.menu = MDDialog(
            title="작업 선택",
            type="confirmation",
            items=[
                MDRectangleFlatButton(text="케릭 정보창", size_hint_x=1, on_release=lambda x: self.nav('info')),
                MDRectangleFlatButton(text="케릭 장비창", size_hint_x=1, on_release=lambda x: self.nav('equ')),
                MDRectangleFlatButton(text="인벤토리창", size_hint_x=1, on_release=lambda x: self.nav('inv')),
                MDRectangleFlatButton(text="사진 선택창", size_hint_x=1, on_release=lambda x: self.nav('pho')),
            ],
        )
        self.menu.open()

    def nav(self, screen_name):
        self.menu.dismiss()
        self.manager.current = screen_name

# 3. 케릭정보창 (19종 그룹화)
class CharInfoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        groups = [
            [('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
            [('생명력', ''), ('기력', ''), ('근력', '')],
            [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
            [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]
        ]
        
        for group in groups:
            grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(10))
            grid.bind(minimum_height=grid.setter('height'))
            for label, val in group:
                row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
                row.add_widget(MDLabel(text=label, size_hint_x=0.3, halign="center"))
                txt = MDTextField(text=val, size_hint_x=0.7, halign="center", mode="fill", fill_color_normal=(1,1,1,0.1))
                grid.add_widget(row)
            l.add_widget(grid)
            l.add_widget(BoxLayout(size_hint_y=None, height=dp(20))) # 비가시적 한칸 띄우기

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_row.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(0.8, 0.2, 0.2, 1), size_hint_x=1, on_release=self.confirm_del))
        l.add_widget(btn_row)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        
        sv.add_widget(l)
        self.add_widget(sv)

    def confirm_del(self, x):
        MDDialog(title="경고", text="삭제하겠습니까?", buttons=[
            MDRaisedButton(text="취소", on_release=lambda x: x.parent.parent.parent.parent.dismiss()),
            MDRaisedButton(text="삭제", md_bg_color=(0.8, 0.2, 0.2, 1))
        ]).open()

# 4. 케릭장비창 (11종 고정)
class EquipScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        sv = MDScrollView()
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint_y=None)
        l.bind(minimum_height=l.setter('height'))
        
        items = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(55))
            row.add_widget(MDLabel(text=item, size_hint_x=0.4, halign="center"))
            row.add_widget(MDTextField(hint_text="아이템명", size_hint_x=0.6, halign="center"))
            l.add_widget(row)
            
        l.add_widget(MDRaisedButton(text="전체 삭제", md_bg_color=(0.8, 0.2, 0.2, 1), size_hint_x=1, on_release=lambda x: MDSnackbar(text="삭제하겠습니까?").open()))
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        sv.add_widget(l)
        self.add_widget(sv)

# 5. 인벤토리창 (한줄씩 클릭 수정)
class InvenScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20))
        l.add_widget(MDLabel(text="인벤토리 (클릭하여 수정)", halign="center", font_style="Subtitle1"))
        
        sv = MDScrollView()
        grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        for i in range(1, 21):
            btn = MDRectangleFlatButton(text=f"인벤토리 항목 {i} : 내용 없음", size_hint_x=1, halign="left")
            grid.add_widget(btn)
        
        sv.add_widget(grid)
        l.add_widget(sv)
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

# 6. 사진선택창 (권한 및 업로드/다운로드)
class PhotoScreen(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        l.add_widget(MDLabel(text="사진 관리 (다중 선택 가능)", halign="center"))
        
        row = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        row.add_widget(MDRaisedButton(text="사진 업로드", size_hint_x=0.5))
        row.add_widget(MDRaisedButton(text="사진 다운로드", size_hint_x=0.5))
        l.add_widget(row)
        
        l.add_widget(MDLabel(text="선택된 사진이 없습니다.", halign="center", theme_text_color="Hint"))
        
        l.add_widget(BoxLayout()) # 여백
        l.add_widget(MDRectangleFlatButton(text="뒤로가기", size_hint_x=1, on_release=lambda x: setattr(self.manager, 'current', 'sel')))
        self.add_widget(l)

if __name__ == '__main__':
    PristonTaleApp().run()
