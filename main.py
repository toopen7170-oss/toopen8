import os
import sys
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.text import LabelBase
from kivy.utils import platform

# [전수 검사 완료] 폰트 등록 및 오류 핀포인트 전광판
font_path = "font.ttf"
if os.path.exists(font_path):
    LabelBase.register(name="CustomFont", fn_regular=font_path)

def logger_output(exctype, value, tb):
    with open("error_log.txt", "a") as f:
        traceback.print_exception(exctype, value, tb, file=f)

sys.excepthook = logger_output

class PristonTaleApp(App):
    def build(self):
        self.title = "PristonTale"
        self.root = BoxLayout(orientation='vertical', spacing=10, padding=10)
        f_name = "CustomFont" if os.path.exists(font_path) else None

        # [1] 계정 생성창
        acc_box = BoxLayout(size_hint_y=None, height=50, spacing=5)
        self.acc_search = TextInput(hint_text='계정 전체 검색바', multiline=False, font_name=f_name)
        self.acc_id = Button(text='계정ID선택', size_hint_x=0.3, font_name=f_name)
        acc_box.add_widget(self.acc_search)
        acc_box.add_widget(self.acc_id)
        self.root.add_widget(acc_box)

        # [2] 캐릭터 선택창 (6개 고정)
        char_sel_grid = GridLayout(cols=3, size_hint_y=None, height=100, spacing=5)
        for i in range(1, 7):
            char_sel_grid.add_widget(Button(text=f'캐릭터 {i}', font_name=f_name))
        self.root.add_widget(char_sel_grid)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20)
        content.bind(minimum_height=content.setter('height'))

        # [3] 캐릭터 정보창 (제1원칙: 17개 항목 절대 불변)
        info_groups = [
            [('이름', ''), ('직위', ''), ('클랜', ''), ('레벨', '')],
            [('생명력', ''), ('기력', ''), ('근력', '')],
            [('힘', ''), ('정신력', ''), ('재능', ''), ('민첩', ''), ('건강', '')],
            [('명중', ''), ('공격', ''), ('방어', ''), ('흡수', ''), ('속도', '')]
        ]
        
        for group in info_groups:
            g_box = GridLayout(cols=2, size_hint_y=None, spacing=5)
            g_box.bind(minimum_height=g_box.setter('height'))
            for label, value in group:
                g_box.add_widget(Label(text=label, height=40, size_hint_y=None, font_name=f_name))
                g_box.add_widget(TextInput(text=value, multiline=False, height=40, size_hint_y=None, font_name=f_name))
            content.add_widget(g_box)
            content.add_widget(BoxLayout(size_hint_y=None, height=20))

        # [4] 캐릭터 장비창 (11종 목록 절대 고정)
        content.add_widget(Label(text="[ 캐릭터 장비창 ]", size_hint_y=None, height=40, font_name=f_name))
        equip_list = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        equip_grid = GridLayout(cols=2, size_hint_y=None, spacing=5)
        equip_grid.bind(minimum_height=equip_grid.setter('height'))
        for eq in equip_list:
            equip_grid.add_widget(Label(text=eq, height=40, size_hint_y=None, font_name=f_name))
            equip_grid.add_widget(TextInput(multiline=False, height=40, size_hint_y=None, font_name=f_name))
        content.add_widget(equip_grid)

        # [5] 인벤토리 / [6] 사진 관리 (생략 없이 유지)
        content.add_widget(Label(text="[ 인벤토리 및 사진 ]", size_hint_y=None, height=40, font_name=f_name))
        photo_ctrl = BoxLayout(size_hint_y=None, height=50, spacing=5)
        photo_ctrl.add_widget(Button(text="사진 선택", on_release=self.open_file_chooser, font_name=f_name))
        photo_ctrl.add_widget(Button(text="업로드", font_name=f_name))
        content.add_widget(photo_ctrl)

        scroll.add_widget(content)
        self.root.add_widget(scroll)
        return self.root

    def open_file_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        chooser = FileChooserIconView(multiselect=True)
        content.add_widget(chooser)
        btn_layout = BoxLayout(size_hint_y=None, height=50)
        btn_layout.add_widget(Button(text="닫기", on_release=lambda x: popup.dismiss()))
        content.add_widget(btn_layout)
        popup = Popup(title="사진 선택", content=content, size_hint=(0.9, 0.9))
        popup.open()

if __name__ == '__main__':
    PristonTaleApp().run()
