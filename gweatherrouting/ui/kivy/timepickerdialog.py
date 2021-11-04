# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""
from kivy.properties import BooleanProperty, ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import IRightBodyTouch, TwoLineIconListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.picker import MDTimePicker, MDDatePicker


class TimePickerDialogContent(MDBoxLayout):
    def __init__(self, datetime):
        super().__init__()
        self.datetime = datetime

    def openTimePicker(self):
        time_dialog = MDTimePicker()
        time_dialog.set_time(self.datetime)
        # time_dialog.bind(time=self.get_time)
        time_dialog.open()

    def openDatePicker(self):
        date_dialog = MDDatePicker(year=self.datetime.year, month=self.datetime.month, day=self.datetime.day)
        # date_dialog.bind(time=self.get_time)
        date_dialog.open()


class TimePickerDialog(MDDialog):
    def __init__(self, datetime):
        self.pickerContent = TimePickerDialogContent(datetime)

        super().__init__(
            title="Set Date and Time",
            type="custom",
            content_cls= self.pickerContent,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    # theme_text_color="Custom",
                    # text_color=self.theme_cls.primary_color,
                ),
                MDFlatButton(
                    text="SET",
                    # theme_text_color="Custom",
                    # text_color=self.theme_cls.primary_color,
                ),
            ],
        )