# -*- coding: utf-8 -*-
# 房屋收租管理系统（Kivy 触屏版）—— 用于打包安卓 APK
# 功能：添加租客 / 查看租客 / 录入缴费 / 查询缴费 / 修改租客 / 删除租客
# 数据保存在应用私有目录 rent_data.json（安卓沙箱内，重启不丢失）
import json
import os
from datetime import date

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'assets', 'fonts', 'NotoSansSC-Regular.otf')
LabelBase.register(name='NotoSansSC', fn_regular=FONT_PATH)


# ---------- 数据层（统一键名，修复原脚本 ID_No. / ID_No / ID No 不一致 bug） ----------
def fmt_amount(v):
    """金额显示：1500 -> 1500，1500.5 -> 1500.5"""
    return f"{v:g}"


def load_data(path):
    """加载数据文件，不存在或损坏则返回空结构"""
    if not os.path.exists(path):
        return {"tenants": [], "records": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return {"tenants": [], "records": []}
    data.setdefault("tenants", [])
    data.setdefault("records", [])
    return data


def save_data(path, data):
    """保存数据"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_tenant(data, tenant_id):
    for t in data["tenants"]:
        if t["id"] == tenant_id:
            return t
    return None


# ---------- 通用弹窗 ----------
def show_info(title, msg, on_dismiss=None):
    popup = Popup(title=title, title_font='NotoSansSC',
                  content=Label(text=msg), size_hint=(0.8, 0.35))
    if on_dismiss:
        popup.bind(on_dismiss=lambda *_: on_dismiss())
    popup.open()


def show_confirm(title, msg, on_yes):
    box = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
    box.add_widget(Label(text=msg))
    btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
    popup = Popup(title=title, title_font='NotoSansSC',
                  content=box, size_hint=(0.8, 0.35))

    def _yes(*_):
        popup.dismiss()
        on_yes()

    yes = Button(text='确认')
    no = Button(text='取消')
    yes.bind(on_press=_yes)
    no.bind(on_press=popup.dismiss)
    btns.add_widget(yes)
    btns.add_widget(no)
    box.add_widget(btns)
    popup.open()


def make_row_label(text):
    """列表行信息标签（左对齐、垂直居中、可换行）"""
    lb = Label(text=text, halign='left', valign='middle', font_size=dp(14))
    lb.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
    return lb


# ---------- 六个屏幕 ----------
class MenuScreen(Screen):
    pass


class AddTenantScreen(Screen):
    def on_pre_enter(self, *args):
        """每次进入清空表单"""
        for f in ('name_f', 'idno_f', 'phone_f', 'addr_f', 'rent_f', 'term_f'):
            self.ids[f].ids.ti.text = ''


class TenantListScreen(Screen):
    pass


class EditTenantScreen(Screen):
    tenant_id = NumericProperty(0)

    def on_pre_enter(self, *args):
        """进入时用租客原值预填表单"""
        app = App.get_running_app()
        t = find_tenant(app.data, self.tenant_id)
        ids = self.ids
        if not t:
            for f in ('name_f', 'idno_f', 'phone_f', 'addr_f', 'rent_f', 'term_f'):
                ids[f].ids.ti.text = ''
            return
        ids.name_f.ids.ti.text = t['name']
        ids.idno_f.ids.ti.text = t['id_no']
        ids.phone_f.ids.ti.text = t['phone']
        ids.addr_f.ids.ti.text = t['address']
        ids.rent_f.ids.ti.text = fmt_amount(t['rent'])
        ids.term_f.ids.ti.text = t['term']


class PayRentScreen(Screen):
    def on_pre_enter(self, *args):
        """进入时刷新租客下拉框，日期默认今天"""
        App.get_running_app().refresh_pay()


class QueryScreen(Screen):
    def on_pre_enter(self, *args):
        """进入时刷新下拉框和记录列表"""
        App.get_running_app().refresh_query()


# ---------- 应用主体 ----------
class RentApp(App):
    title = '房屋收租管理'

    def build(self):
        # 安卓上 cwd 不可写，必须用应用私有目录
        self.data_file = os.path.join(self.user_data_dir, 'rent_data.json')
        self.data = load_data(self.data_file)
        return Builder.load_file(os.path.join(BASE_DIR, 'rent.kv'))

    # ---- 添加租客 ----
    def save_add_tenant(self):
        ids = self.root.get_screen('add_tenant').ids
        name = ids.name_f.ids.ti.text.strip()
        id_no = ids.idno_f.ids.ti.text.strip()
        phone = ids.phone_f.ids.ti.text.strip()
        address = ids.addr_f.ids.ti.text.strip()
        term = ids.term_f.ids.ti.text.strip()
        rent_str = ids.rent_f.ids.ti.text.strip()
        if not name:
            show_info('提示', '租客姓名不能为空')
            return
        try:
            rent = float(rent_str)
            if rent < 0:
                raise ValueError
        except ValueError:
            show_info('提示', '月租金必须是大于等于 0 的数字')
            return
        new_id = max((t['id'] for t in self.data['tenants']), default=0) + 1
        self.data['tenants'].append({
            'id': new_id, 'name': name, 'id_no': id_no, 'phone': phone,
            'address': address, 'rent': rent, 'term': term,
        })
        save_data(self.data_file, self.data)
        show_info('成功', f'租客添加成功，编号：{new_id}',
                  on_dismiss=lambda: setattr(self.root, 'current', 'menu'))

    # ---- 租客列表 ----
    def refresh_tenant_list(self):
        box = self.root.get_screen('tenant_list').ids.list_box
        box.clear_widgets()
        tenants = self.data['tenants']
        if not tenants:
            box.add_widget(make_row_label('暂无租客信息'))
            return
        for t in tenants:
            row = BoxLayout(size_hint_y=None, height=dp(64),
                            spacing=dp(8), padding=[dp(4), dp(2)])
            row.add_widget(make_row_label(
                f"#{t['id']}  {t['name']}  月租:{fmt_amount(t['rent'])}元\n"
                f"电话:{t['phone']}  地址:{t['address']}"))
            edit_btn = Button(text='编辑', size_hint_x=None, width=dp(72),
                              background_color=(0.2, 0.65, 0.3, 1))
            del_btn = Button(text='删除', size_hint_x=None, width=dp(72),
                             background_color=(0.85, 0.25, 0.25, 1))
            tid = t['id']  # 用局部变量绑定，避免循环闭包指向最后一个租客
            edit_btn.bind(on_press=lambda *_: self.goto_edit(tid))
            del_btn.bind(on_press=lambda *_: self.confirm_delete(tid))
            row.add_widget(edit_btn)
            row.add_widget(del_btn)
            box.add_widget(row)

    # ---- 编辑租客 ----
    def goto_edit(self, tenant_id):
        self.root.get_screen('edit_tenant').tenant_id = tenant_id
        self.root.current = 'edit_tenant'

    def save_edit_tenant(self):
        screen = self.root.get_screen('edit_tenant')
        t = find_tenant(self.data, screen.tenant_id)
        if not t:
            show_info('提示', '未找到该租客')
            self.root.current = 'tenant_list'
            return
        ids = screen.ids
        name = ids.name_f.ids.ti.text.strip()
        rent_str = ids.rent_f.ids.ti.text.strip()
        if not name:
            show_info('提示', '租客姓名不能为空')
            return
        try:
            rent = float(rent_str)
            if rent < 0:
                raise ValueError
        except ValueError:
            show_info('提示', '月租金必须是大于等于 0 的数字')
            return
        t['name'] = name
        t['id_no'] = ids.idno_f.ids.ti.text.strip()
        t['phone'] = ids.phone_f.ids.ti.text.strip()
        t['address'] = ids.addr_f.ids.ti.text.strip()
        t['rent'] = rent
        t['term'] = ids.term_f.ids.ti.text.strip()
        save_data(self.data_file, self.data)
        show_info('成功', '租客信息已更新',
                  on_dismiss=lambda: setattr(self.root, 'current', 'tenant_list'))

    # ---- 删除租客（同时删除其缴费记录） ----
    def confirm_delete(self, tenant_id):
        show_confirm('删除确认', f'确定删除租客 #{tenant_id} 吗？\n其缴费记录将一并删除',
                     on_yes=lambda: self.delete_tenant(tenant_id))

    def delete_tenant(self, tenant_id):
        before = len(self.data['tenants'])
        self.data['tenants'] = [t for t in self.data['tenants'] if t['id'] != tenant_id]
        if len(self.data['tenants']) == before:
            show_info('提示', '未找到该租客')
            return
        self.data['records'] = [r for r in self.data['records'] if r['tenant_id'] != tenant_id]
        save_data(self.data_file, self.data)
        show_info('成功', '租客已删除',
                  on_dismiss=lambda: self.refresh_tenant_list())

    # ---- 录入缴费 ----
    def refresh_pay(self):
        screen = self.root.get_screen('pay_rent')
        names = [t['name'] for t in self.data['tenants']]
        sp = screen.ids.tenant_sp
        if names:
            sp.values = names
            if sp.text not in names:
                sp.text = names[0]
        else:
            sp.values = ['（暂无租客）']
            sp.text = '（暂无租客）'
        screen.ids.date_f.ids.ti.text = date.today().isoformat()
        self.on_pay_tenant_selected(sp.text)

    def on_pay_tenant_selected(self, name):
        """选中租客后，金额默认填该租客的月租金"""
        screen = self.root.get_screen('pay_rent')
        for t in self.data['tenants']:
            if t['name'] == name:
                screen.ids.amount_f.ids.ti.text = fmt_amount(t['rent'])
                return
        screen.ids.amount_f.ids.ti.text = ''

    def save_pay(self):
        screen = self.root.get_screen('pay_rent')
        name = screen.ids.tenant_sp.text
        target = None
        for t in self.data['tenants']:
            if t['name'] == name:
                target = t
                break
        if not target:
            show_info('提示', '请先添加租客')
            return
        pay_date = screen.ids.date_f.ids.ti.text.strip()
        if pay_date:
            try:
                date.fromisoformat(pay_date)
            except ValueError:
                show_info('提示', '日期格式应为 2026-01-01')
                return
        else:
            pay_date = date.today().isoformat()
        try:
            money = float(screen.ids.amount_f.ids.ti.text)
            if money <= 0:
                raise ValueError
        except ValueError:
            show_info('提示', '缴费金额必须是大于 0 的数字')
            return
        self.data['records'].append({
            'tenant_id': target['id'], 'date': pay_date, 'amount': money,
        })
        save_data(self.data_file, self.data)
        show_info('成功', f"{target['name']} 的缴费记录已录入",
                  on_dismiss=lambda: setattr(self.root, 'current', 'menu'))

    # ---- 查询缴费 ----
    def refresh_query(self):
        screen = self.root.get_screen('query')
        names = [t['name'] for t in self.data['tenants']]
        sp = screen.ids.tenant_sp
        sp.values = ['全部'] + names
        if sp.text not in sp.values:
            sp.text = '全部'
        box = screen.ids.list_box
        box.clear_widgets()
        total = 0.0
        id_by_name = {t['name']: t['id'] for t in self.data['tenants']}
        name_by_id = {t['id']: t['name'] for t in self.data['tenants']}
        for r in self.data['records']:
            if sp.text != '全部' and r['tenant_id'] != id_by_name.get(sp.text):
                continue
            box.add_widget(make_row_label(
                f"{r['date']}   {name_by_id.get(r['tenant_id'], '?')}   "
                f"{fmt_amount(r['amount'])}元"))
            total += r['amount']
        if not box.children:
            box.add_widget(make_row_label('暂无缴费记录'))
        screen.ids.total_lb.text = f'累计已收租金：{fmt_amount(total)}元'


if __name__ == '__main__':
    RentApp().run()
