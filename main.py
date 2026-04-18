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
from kivy.utils import platform

# 오류 핀포인트 전광판 (로그 기록)
def logger_output(exctype, value, tb):
    with open("error_log.txt", "a") as f:
        traceback.print_exception(exctype, value, tb, file=f)
    print(f"Error captured: {value}")

sys.excepthook = logger_output

class ProjectMasterApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # [1] 계정 생성창 (ID 선택 및 검색바)
        acc_box = BoxLayout(size_hint_y=None, height=50, spacing=5)
        self.acc_search = TextInput(hint_text='계정 전체 검색바', multiline=False)
        self.acc_id = Button(text='계정ID선택', size_hint_x=0.3)
        acc_box.add_widget(self.acc_search)
        acc_box.add_widget(self.acc_id)
        self.root.add_widget(acc_box)

        # [2] 캐릭터 선택창 (6개)
        char_sel_grid = GridLayout(cols=3, size_hint_y=None, height=100, spacing=5)
        for i in range(1, 7):
            char_sel_grid.add_widget(Button(text=f'캐릭터 {i}'))
        self.root.add_widget(char_sel_grid)

        # 메인 컨텐츠 스크롤 영역
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20)
        content.bind(minimum_height=content.setter('height'))

        # [3] 캐릭터 정보창 (제1원칙: 구조 불변)
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
                g_box.add_widget(Label(text=label, height=40, size_hint_y=None))
                g_box.add_widget(TextInput(text=value, multiline=False, height=40, size_hint_y=None))
            content.add_widget(g_box)
            # (한칸 띄어주고) - 투명 위젯으로 구현
            content.add_widget(BoxLayout(size_hint_y=None, height=20))

        # [4] 캐릭터 장비창 (11종)
        content.add_widget(Label(text="[ 캐릭터 장비창 ]", size_hint_y=None, height=40))
        equip_list = ["한손무기", "두손무기", "갑옷", "방패", "장갑", "부츠", "암릿", "링1", "링2", "아뮬랫", "기타"]
        equip_grid = GridLayout(cols=2, size_hint_y=None, spacing=5)
        equip_grid.bind(minimum_height=equip_grid.setter('height'))
        for eq in equip_list:
            equip_grid.add_widget(Label(text=eq, height=40, size_hint_y=None))
            equip_grid.add_widget(TextInput(hint_text=f"{eq} 정보", multiline=False, height=40, size_hint_y=None))
        content.add_widget(equip_grid)

        # [5] 인벤토리창 (라인별 저장/삭제/상세수정)
        content.add_widget(Label(text="[ 인벤토리 ]", size_hint_y=None, height=40))
        for i in range(5):
            inv_line = BoxLayout(size_hint_y=None, height=50, spacing=5)
            btn_detail = Button(text=f"아이템 {i+1} (클릭 시 상세수정)")
            btn_save = Button(text="저장", size_hint_x=0.2)
            btn_del = Button(text="삭제", size_hint_x=0.2)
            inv_line.add_widget(btn_detail)
            inv_line.add_widget(btn_save)
            inv_line.add_widget(btn_del)
            content.add_widget(inv_line)

        # [6] 사진 선택 및 업로드/다운로드 (Android 14 권한 처리 포함)
        content.add_widget(Label(text="[ 사진 관리 ]", size_hint_y=None, height=40))
        photo_ctrl = BoxLayout(size_hint_y=None, height=50, spacing=5)
        photo_ctrl.add_widget(Button(text="사진 선택", on_release=self.open_file_chooser))
        photo_ctrl.add_widget(Button(text="업로드"))
        photo_ctrl.add_widget(Button(text="다운로드"))
        content.add_widget(photo_ctrl)

        scroll.add_widget(content)
        self.root.add_widget(scroll)
        return self.root

    def open_file_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        chooser = FileChooserIconView(multiselect=True)
        content.add_widget(chooser)
        
        btn_layout = BoxLayout(size_hint_y=None, height=50)
        btn_save = Button(text="저장")
        btn_del = Button(text="삭제")
        btn_close = Button(text="닫기")
        
        btn_layout.add_widget(btn_save)
        btn_layout.add_widget(btn_del)
        btn_layout.add_widget(btn_close)
        content.add_widget(btn_layout)

        popup = Popup(title="사진 선택 (다중 선택 가능)", content=content, size_hint=(0.9, 0.9))
        btn_close.bind(on_release=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    if platform == 'android':
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES])
    ProjectMasterApp().run()
