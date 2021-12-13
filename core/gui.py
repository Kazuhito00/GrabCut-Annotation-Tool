#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import os
import copy
import json

import cv2 as cv
import numpy as np
from PIL import Image
import PySimpleGUI as sg

import core.util as util


class AppGui(object):
    _layout, _window = None, None
    _event, _values = None, None

    _file_paths = None

    _class_id = 0
    _file_currrent_index = 0

    _DISPLAY_IMAGE_SIZE = (512, 512)
    _graph_image_id = None
    _graph_mask_id = None

    MOUSE_EVENT_NONE = 0
    MOUSE_EVENT_DRAG_START = 1
    MOUSE_EVENT_DRAG = 2
    MOUSE_EVENT_DRAG_END = 3
    _mouse_drag_count = 0
    _mouse_event = MOUSE_EVENT_NONE
    _mouse_point = None

    ROI_MODE = 0
    GRABCUT_MODE = 1
    mode = ROI_MODE

    def __init__(self, file_paths):
        self._file_paths = file_paths
        file_list = [os.path.basename(file_path) for file_path in file_paths]

        # クラスIDラジオボタン定義
        radio_dict = {
            '-00-': 0,
            '-01-': 1,
            '-02-': 2,
            '-03-': 3,
            '-04-': 4,
            '-05-': 5,
            '-06-': 6,
            '-07-': 7,
            '-08-': 8,
            '-09-': 9,
            '-10-': 10,
            '-11-': 11,
            '-12-': 12,
            '-13-': 13,
            '-14-': 14,
            '-15-': 15,
            '-16-': 16,
            '-17-': 17,
            '-18-': 18,
            '-19-': 19,
            '-20-': 20
        }

        # GUIテーマ設定
        sg.theme('DarkBlue')

        # オリジナル画像/マスク画像表示フレーム
        frame_image = sg.Frame('',
                               layout=[[
                                   sg.Graph(
                                       (512, 512),
                                       (0, 0),
                                       (512, 512),
                                       change_submits=True,
                                       drag_submits=True,
                                       key='-IMAGE ORIGINAL-',
                                   ),
                                   sg.Graph(
                                       (512, 512),
                                       (0, 0),
                                       (512, 512),
                                       change_submits=True,
                                       drag_submits=True,
                                       key='-IMAGE MASK-',
                                   ),
                               ]],
                               border_width=0)

        # クラスID選択フレーム
        frame_class_select = sg.Frame('Class ID',
                                      layout=[[
                                          sg.Radio(
                                              item[1],
                                              key=item[0],
                                              group_id='0',
                                              enable_events=True,
                                          ) for item in radio_dict.items()
                                      ]],
                                      border_width=1)

        # メイン(ファイルリスト以外)
        frame_main = sg.Frame(
            '',
            layout=[[frame_image], [frame_class_select],
                    [
                        sg.Spin(
                            [format(i * 0.1, '.1f') for i in range(1, 10)],
                            initial_value=0.7,
                            key='-SPIN MASK ALPHA-',
                            enable_events=True,
                        ),
                        sg.Text('Mask alpha    '),
                        sg.Spin(
                            [i for i in range(1, 10)],
                            initial_value=5,
                            key='-SPIN ITERATION-',
                            enable_events=True,
                        ),
                        sg.Text('Iteration    '),
                        sg.Spin(
                            [i for i in range(1, 10)],
                            initial_value=4,
                            key='-SPIN DRAW THICKNESS-',
                            enable_events=True,
                        ),
                        sg.Text('Draw thickness    '),
                        sg.Spin(
                            [i for i in [32, 64, 128, 256, 512, 1024]],
                            initial_value=512,
                            key='-SPIN OUTPUT WIDTH-',
                            enable_events=True,
                        ),
                        sg.Text('Output width    '),
                        sg.Spin(
                            [i for i in [32, 64, 128, 256, 512, 1024]],
                            initial_value=512,
                            key='-SPIN OUTPUT HEIGHT-',
                            enable_events=True,
                        ),
                        sg.Text('Output height      '),
                        sg.Checkbox('Auto save     ',
                                    enable_events=True,
                                    key='-CHECKBOX AUTO SAVE-'),
                        sg.Checkbox('Manually label background',
                                    enable_events=True,
                                    key='-CHECKBOX BACKGROUND-'),
                    ]],
            border_width=0)

        self._layout = [
            [
                sg.Listbox(
                    file_list,
                    size=(15, 50),
                    bind_return_key=True,
                    enable_events=True,
                    key='-LISTBOX FILE-',
                ),
                frame_main,
            ],
        ]

        # ウィンドウの生成
        self._window = sg.Window(
            'GrabCut Annotation Tool',
            self._layout,
            size=(1220, 620),
            return_keyboard_events=True,
            finalize=True,
            location=(50, 50),
        )

        # GUI初期設定
        self._file_currrent_index = 0

        self._window['-01-'].update(True)  # クラスID：1
        self._window.Element('-LISTBOX FILE-').Update(
            set_to_index=self._file_currrent_index)  # ファイルリスト：先頭
        self._window['-CHECKBOX BACKGROUND-'].Update(value=True)  # 前景後景指定

        self._event = None
        self._values = None

        self._class_id = 0

    # 廃止予定
    def legacy_get_window(self):
        return self._window

    # PySimpleGUIイベント読み取り
    def read_window(self, timeout=None):
        self._event, self._values = self._window.read(timeout=timeout)

        if timeout is None:
            # マウスイベント確認
            self._check_mouse_event(self._event, self._values)

        return self._event, self._values

    # マウスイベント確認(window.read() Timeout指定無し時に使用する想定)
    def _check_mouse_event(self, event, values):
        if event == '-IMAGE ORIGINAL-':
            if self._mouse_drag_count == 0:
                self._mouse_event = self.MOUSE_EVENT_DRAG_START
            else:
                self._mouse_event = self.MOUSE_EVENT_DRAG

            imaga_width = self._DISPLAY_IMAGE_SIZE[0]
            imaga_height = self._DISPLAY_IMAGE_SIZE[1]

            moues_x = values['-IMAGE ORIGINAL-'][0]
            moues_y = imaga_height - values['-IMAGE ORIGINAL-'][1]
            if moues_x < 1:
                moues_x = 1
            if imaga_width < moues_x:
                moues_x = imaga_width
            if moues_y < 1:
                moues_y = 1
            if imaga_height < moues_y:
                moues_y = imaga_height
            self._mouse_point = (moues_x, moues_y)

            self._mouse_drag_count += 1
        else:
            if self._mouse_drag_count > 0:
                self._mouse_event = self.MOUSE_EVENT_DRAG_END
                self._mouse_drag_count = 0
            elif self._mouse_event == self.MOUSE_EVENT_DRAG_END:
                self._mouse_event = self.MOUSE_EVENT_NONE
                self._mouse_point = None

    # マウスイベント読み取り
    def read_mouse_event(self):
        mouse_event = self._mouse_event
        mouse_point = self._mouse_point

        if self._mouse_event == self.MOUSE_EVENT_DRAG_END:
            self._mouse_event = self.MOUSE_EVENT_NONE
            self._mouse_point = None

        return mouse_event, mouse_point

    # 設定ファイル読み込み
    def load_config(self, config_file_name):
        # JSON読み出し
        with open(config_file_name, mode='rt', encoding='utf-8') as file:
            config_data = json.load(file)

        # 設定反映
        self._window['-SPIN MASK ALPHA-'].Update(
            value=config_data['MASK ALPHA'])
        self._window['-SPIN ITERATION-'].Update(value=config_data['ITERATION'])
        self._window['-SPIN DRAW THICKNESS-'].Update(
            value=config_data['DRAW THICKNESS'])
        self._window['-SPIN OUTPUT WIDTH-'].Update(
            value=config_data['OUTPUT WIDTH'])
        self._window['-SPIN OUTPUT HEIGHT-'].Update(
            value=config_data['OUTPUT HEIGHT'])
        if config_data['AUTO SAVE'] == 1:
            self._window['-CHECKBOX AUTO SAVE-'].Update(value=True)
        else:
            self._window['-CHECKBOX AUTO SAVE-'].Update(value=False)

        # GUI上の設定読み出し
        self._event, self._values = self._window.read(timeout=1)

        return config_data

    # GUIイベント取得
    def get_window_event(self):
        return self._event

    # GUI値取得
    def get_window_values(self):
        return self._values

    # 設定：クラスID
    def get_setting_class_id(self):
        if self._values['-00-']:
            self._class_id = 0
        elif self._values['-01-']:
            self._class_id = 1
        elif self._values['-02-']:
            self._class_id = 2
        elif self._values['-03-']:
            self._class_id = 3
        elif self._values['-04-']:
            self._class_id = 4
        elif self._values['-05-']:
            self._class_id = 5
        elif self._values['-06-']:
            self._class_id = 6
        elif self._values['-07-']:
            self._class_id = 7
        elif self._values['-08-']:
            self._class_id = 8
        elif self._values['-09-']:
            self._class_id = 9
        elif self._values['-10-']:
            self._class_id = 10
        elif self._values['-11-']:
            self._class_id = 11
        elif self._values['-12-']:
            self._class_id = 12
        elif self._values['-13-']:
            self._class_id = 13
        elif self._values['-14-']:
            self._class_id = 14
        elif self._values['-15-']:
            self._class_id = 15
        elif self._values['-16-']:
            self._class_id = 16
        elif self._values['-17-']:
            self._class_id = 17
        elif self._values['-18-']:
            self._class_id = 18
        elif self._values['-19-']:
            self._class_id = 19
        elif self._values['-255-']:
            self._class_id = 255
        else:
            self._class_id = 255

        return self._class_id

    # 設定：クラスID設定
    def set_setting_class_id(self, class_id=255):
        key_string = '-' + str(class_id).zfill(2) + '-'

        self._window[key_string].update(True)
        self._event, self._values = self._window.read(timeout=1)

        return self._class_id

    # 設定：GrabCut マスクα
    def get_setting_mask_alpha(self):
        return float(self._values['-SPIN MASK ALPHA-'])

    # 設定：GrabCut イテレーション回数
    def get_setting_iteration(self):
        return int(self._values['-SPIN ITERATION-'])

    # 設定：GrabCut 手動マスク描画線の太さ
    def get_setting_draw_thickness(self):
        return int(self._values['-SPIN DRAW THICKNESS-'])

    # 設定：オートセーブ
    def get_setting_auto_save(self):
        return self._values['-CHECKBOX AUTO SAVE-']

    # 設定：前景/後景指定
    def get_setting_lable_background(self):
        return self._values['-CHECKBOX BACKGROUND-']

    # 設定：前景/後景設定 設定
    def set_setting_lable_background(self, flag):
        self._window['-CHECKBOX BACKGROUND-'].Update(value=flag)
        self._event, self._values = self._window.read(timeout=1)

    # 設定：出力画像幅
    def get_setting_output_width(self):
        return self._values['-SPIN OUTPUT WIDTH-']

    # 設定：出力画像高さ
    def get_setting_output_height(self):
        return self._values['-SPIN OUTPUT HEIGHT-']

    # ファイルリストのインデックス取得
    def get_file_list_current_index(self):
        self._file_currrent_index = self._window.Element(
            '-LISTBOX FILE-').GetIndexes()[0]
        return self._file_currrent_index

    # ファイルリストのインデックス設定
    def set_file_list_current_index(self, index, scroll=False):
        self._file_currrent_index = index

        if scroll:
            self._window['-LISTBOX FILE-'].Update(
                set_to_index=self._file_currrent_index,
                scroll_to_index=self._file_currrent_index,
            )

    def get_listbox_size(self):
        return len(self._file_paths)

    def get_file_path_from_listbox(self, index):
        return self._file_paths[index]

    # 画像描画サイズ
    def get_display_image_size(self):
        return self._DISPLAY_IMAGE_SIZE

    # 画像描画
    def draw_image(self, image):
        # バイト列へ変換
        bytes_image = cv.imencode('.png', image)[1].tobytes()

        imaga_height = self._DISPLAY_IMAGE_SIZE[1]

        # 画面描画
        if self._graph_image_id is not None:
            self._window['-IMAGE ORIGINAL-'].delete_figure(
                self._graph_image_id)
        self._graph_image_id = self._window['-IMAGE ORIGINAL-'].draw_image(
            data=bytes_image,
            location=(0, imaga_height),
        )

    # マスク画像描画
    def draw_mask_image(self, mask_list):
        # セマンティックセグメンテーション カラーパレット取得
        color_palette = util.get_palette().flatten()
        color_palette = color_palette.tolist()

        # 各クラスを統合した画像を生成
        debug_mask = copy.deepcopy(mask_list[0])
        for index, mask in enumerate(mask_list):
            temp_mask = copy.deepcopy(mask)
            debug_mask = np.where((temp_mask == 2) | (temp_mask == 0),
                                  debug_mask, index).astype('uint8')

        # バイト列へ変換
        with Image.fromarray(debug_mask, mode="P") as png_image:
            png_image.putpalette(color_palette)

            bytes_image = io.BytesIO()
            png_image.save(bytes_image, format='PNG')
            bytes_image = bytes_image.getvalue()

        imaga_height = self._DISPLAY_IMAGE_SIZE[1]

        # 画面描画
        if self._graph_mask_id is not None:
            self._window['-IMAGE MASK-'].delete_figure(self._graph_mask_id)
        self._graph_mask_id = self._window['-IMAGE MASK-'].draw_image(
            data=bytes_image,
            location=(0, imaga_height),
        )

    def __del__(self):
        self._window.close()
