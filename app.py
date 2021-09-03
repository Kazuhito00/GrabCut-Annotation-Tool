#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import gc
import glob
import copy
import json
import argparse

import cv2 as cv
import numpy as np
from PIL import Image

import core.gui as gui
import core.util as util

image_list, mask_list, debug_image_list = [], [], []
bgd_model_list, fgd_model_list = [], []
prev_class_id = -1


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=str,
        default='input',
    )
    parser.add_argument(
        "--output_image",
        type=str,
        default='output/image',
    )
    parser.add_argument(
        "--output_annotation",
        type=str,
        default='output/annotation',
    )
    parser.add_argument(
        "--config",
        type=str,
        default='config.json',
    )

    args = parser.parse_args()

    return args


def initialize_grabcut_list(class_num, image, mask):
    global image_list, mask_list, bgd_model_list, fgd_model_list, \
            debug_image_list

    if len(image_list) == 0:
        for index in range(class_num):
            image_list.append(copy.deepcopy(image))
            debug_image_list.append(copy.deepcopy(image))
            mask_list.append(copy.deepcopy(mask))
            bgd_model_list.append(np.zeros((1, 65), dtype=np.float64))
            fgd_model_list.append(np.zeros((1, 65), dtype=np.float64))
    else:
        for index in range(class_num):
            image_list[index] = copy.deepcopy(image)
            debug_image_list[index] = copy.deepcopy(image)
            mask_list[index] = copy.deepcopy(mask)
            bgd_model_list[index] = np.zeros((1, 65), dtype=np.float64)
            fgd_model_list[index] = np.zeros((1, 65), dtype=np.float64)

    gc.collect()


# 既存のマスクファイルを読み込む
def load_mask_image(output_annotation_path, mask_filename, class_num):
    global mask_list

    filename = os.path.splitext(os.path.basename(mask_filename))[0]
    mask_file_path = os.path.join(output_annotation_path, filename + '.png')
    if os.path.exists(mask_file_path):
        pil_image = Image.open(mask_file_path)
        mask = np.asarray(pil_image).astype('uint8')

        for index in range(class_num):
            mask_list[index] = np.where((mask == index), 1, 0).astype('uint8')

    return mask_list


# ROI Mode描画
def draw_roi_mode_image(image, roi=None):
    debug_image = copy.deepcopy(image)

    cv.putText(debug_image, "Select ROI", (5, 25), cv.FONT_HERSHEY_SIMPLEX,
               0.9, (255, 255, 255), 3, cv.LINE_AA)
    cv.putText(debug_image, "Select ROI", (5, 25), cv.FONT_HERSHEY_SIMPLEX,
               0.9, (103, 82, 51), 1, cv.LINE_AA)

    if roi is not None:
        cv.rectangle(
            debug_image,
            (roi[0], roi[1]),
            (roi[2], roi[3]),
            (255, 255, 255),
            thickness=3,
        )
        cv.rectangle(
            debug_image,
            (roi[0], roi[1]),
            (roi[2], roi[3]),
            (103, 82, 51),
            thickness=2,
        )

    return debug_image


# GrabCut Mode描画
def draw_grabcut_mode_image(
    image,
    color,
    mask,
    mask_color,
    point01=None,
    point02=None,
    thickness=4,
):
    debug_image = copy.deepcopy(image)
    debug_mask = copy.deepcopy(mask)

    if point01 is not None and point02 is not None:
        cv.line(debug_image, point01, point02, color, thickness)
        cv.line(debug_mask, point01, point02, mask_color, thickness)

    return debug_image, debug_mask


# 処理中表示
def draw_processing_image(image):
    image_width, image_height = image.shape[1], image.shape[0]

    # 処理中表示
    loading_image = copy.deepcopy(image)
    loading_mask = np.zeros(image.shape[:2], dtype=np.uint8)
    loading_image = loading_image * loading_mask[:, :, np.newaxis]
    loading_image = cv.addWeighted(loading_image, 0.7, image, 0.3, 0)
    cv.putText(loading_image, "PROCESSING...",
               (int(image_width / 2) - (6 * 18), int(image_height / 2)),
               cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 4, cv.LINE_AA)
    cv.putText(loading_image, "PROCESSING...",
               (int(image_width / 2) - (6 * 18), int(image_height / 2)),
               cv.FONT_HERSHEY_SIMPLEX, 1.0, (103, 82, 51), 2, cv.LINE_AA)

    return loading_image


# マウスのドラッグ開始点/終了点を取得
def get_mouse_start_end_point(appgui, mosue_info):
    mouse_event = mosue_info[0]
    mouse_start_point = mosue_info[1]
    mouse_end_point = mosue_info[2]
    mouse_prev_point = mosue_info[3]

    mouse_event, mouse_point = appgui.read_mouse_event()

    if mouse_event == appgui.MOUSE_EVENT_DRAG_START:
        mouse_start_point = mouse_point
        mouse_prev_point = mouse_point
    elif mouse_event == appgui.MOUSE_EVENT_DRAG:
        mouse_prev_point = mouse_end_point
        mouse_end_point = mouse_point
    elif mouse_event == appgui.MOUSE_EVENT_DRAG_END:
        mouse_prev_point = mouse_end_point
        mouse_end_point = mouse_point
    elif mouse_event == appgui.MOUSE_EVENT_NONE:
        mouse_start_point = None
        mouse_end_point = None
        mouse_prev_point = None

    return (mouse_event, mouse_start_point, mouse_end_point, mouse_prev_point)


# ROIモード時の処理
def process_select_roi_mode(
    appgui,
    mosue_info,
    image,
    debug_image,
    mask,
    bgd_model,
    fgd_model,
):
    global mask_list

    # マウス情報取得
    mouse_event = mosue_info[0]
    mouse_start_point = mosue_info[1]
    mouse_end_point = mosue_info[2]

    # GUI上の設定を取得
    mask_alpha = appgui.get_setting_mask_alpha()
    mask_beta = 1 - mask_alpha
    iteration = appgui.get_setting_iteration()

    roi = None
    grabcut_execute = False

    # ROI取得
    if (mouse_start_point is not None and mouse_end_point is not None):
        min_x = (mouse_start_point[0]) if (
            mouse_start_point[0] < mouse_end_point[0]) else (
                mouse_end_point[0])
        man_x = (mouse_start_point[0]) if (
            mouse_start_point[0] > mouse_end_point[0]) else (
                mouse_end_point[0])
        min_y = (mouse_start_point[1]) if (
            mouse_start_point[1] < mouse_end_point[1]) else (
                mouse_end_point[1])
        man_y = (mouse_start_point[1]) if (
            mouse_start_point[1] > mouse_end_point[1]) else (
                mouse_end_point[1])
        roi = [min_x, min_y, man_x, man_y]

    # マウスドラッグ開始時
    if mouse_event == appgui.MOUSE_EVENT_DRAG:
        debug_image = draw_roi_mode_image(image)

    # マウスドラッグ中の場合、ROI領域を描画
    if mouse_event == appgui.MOUSE_EVENT_DRAG:
        debug_image = draw_roi_mode_image(image, roi)

    # マウスドラッグ終了時にGrabCutを実施
    if mouse_event == appgui.MOUSE_EVENT_DRAG_END:
        # 処理中表示
        loading_image = draw_processing_image(image)
        appgui.draw_image(loading_image)
        appgui.read_window(timeout=100)

        # GrabCut実施
        mask, bgd_model, fgd_model, debug_image = util.execute_grabcut(
            image,
            mask,
            bgd_model,
            fgd_model,
            iteration,
            mask_alpha,
            mask_beta,
            roi,
        )

        # 前景/後景の手修正するモード(GRABCUT_MODE)へ遷移
        appgui.mode = appgui.GRABCUT_MODE

        # 前景/背景情報提示
        label_background = appgui.get_setting_lable_background()
        if label_background:
            color = (0, 0, 255)
        else:
            color = (255, 0, 0)
        cv.rectangle(debug_image, (0, 0), (511, 511), color=color, thickness=3)

        grabcut_execute = True

    # 画像描画
    appgui.draw_image(debug_image)
    appgui.draw_mask_image(mask_list)

    return grabcut_execute, mask, bgd_model, fgd_model, debug_image


# GrabCutモード時の処理
def process_grabcut_mode(
    appgui,
    mosue_info,
    image,
    debug_image,
    mask,
    bgd_model,
    fgd_model,
):
    global mask_list

    # マウス情報取得
    mouse_event = mosue_info[0]
    mouse_end_point = mosue_info[2]
    mouse_prev_point = mosue_info[3]

    # GUI上の設定を取得
    mask_alpha = appgui.get_setting_mask_alpha()
    mask_beta = 1 - mask_alpha
    iteration = appgui.get_setting_iteration()
    thickness = appgui.get_setting_draw_thickness()
    label_background = appgui.get_setting_lable_background()

    grabcut_execute = False

        if label_background:
            color = (0, 0, 255)
            manually_label_value = 0
        else:
            color = (255, 0, 0)
            manually_label_value = 1

    # マウスドラッグ中の場合、手修正指定を描画
    if mouse_event == appgui.MOUSE_EVENT_DRAG_START or \
            mouse_event == appgui.MOUSE_EVENT_DRAG:

        debug_image, mask = draw_grabcut_mode_image(
            debug_image,
            color,
            mask,
            manually_label_value,
            point01=mouse_prev_point,
            point02=mouse_end_point,
            thickness=thickness,
        )

    # マウスドラッグ終了時にGrabCutを実施
    if mouse_event == appgui.MOUSE_EVENT_DRAG_END:
        # 処理中表示
        loading_image = draw_processing_image(image)
        appgui.draw_image(loading_image)
        appgui.read_window(timeout=100)

        # GrabCut実施
        mask, bgd_model, fgd_model, debug_image = util.execute_grabcut(
            image,
            mask,
            bgd_model,
            fgd_model,
            iteration,
            mask_alpha,
            mask_beta,
        )

        # 前景/背景情報提示
        cv.rectangle(debug_image, (0, 0), (511, 511), color=color, thickness=3)

        grabcut_execute = True

    # 画像描画
    appgui.draw_image(debug_image)
    appgui.draw_mask_image(mask_list)

    return grabcut_execute, mask, bgd_model, fgd_model, debug_image


# イベント種別取得
def get_event_kind(event):
    event_kind = None

    if event.startswith('Up') or event.startswith('p'):
        event_kind = 'Up'
    elif event.startswith('Down') or event.startswith('n'):
        event_kind = 'Down'
    elif event.startswith('0'):
        event_kind = '-00-'
    elif event.startswith('1'):
        event_kind = '-01-'
    elif event.startswith('2'):
        event_kind = '-02-'
    elif event.startswith('3'):
        event_kind = '-03-'
    elif event.startswith('4'):
        event_kind = '-04-'
    elif event.startswith('5'):
        event_kind = '-05-'
    elif event.startswith('6'):
        event_kind = '-06-'
    elif event.startswith('7'):
        event_kind = '-07-'
    elif event.startswith('8'):
        event_kind = '-08-'
    elif event.startswith('9'):
        event_kind = '-09-'
    elif event.startswith('s'):
        event_kind = 's'
    elif event.startswith('Control'):
        event_kind = 'Control'
    elif event.startswith('Escape'):
        event_kind = 'Escape'
    else:
        event_kind = event

    return event_kind


# イベントハンドラー：ファイルリスト選択
def event_handler_file_select(event_kind, appgui, scroll_count=0):
    global mask_list, output_annotation_path

    # インデックス位置を計算
    listbox_size = appgui.get_listbox_size()
    currrent_index = appgui.get_file_list_current_index()
    currrent_index = (currrent_index + scroll_count) % listbox_size

    # インデックス位置へリストを移動
    if scroll_count == 0:
        appgui.set_file_list_current_index(currrent_index, False)
    else:
        appgui.set_file_list_current_index(currrent_index, True)

    # 画像読み込み
    file_path = appgui.get_file_path_from_listbox(currrent_index)
    image = cv.imread(file_path)
    resize_image = cv.resize(image, (512, 512))
    mask = np.zeros(resize_image.shape[:2], dtype=np.uint8)

    # 初期描画
    class_num = 22
    initialize_grabcut_list(class_num, resize_image, mask)

    # 既存のマスクファイルを確認し、存在すれば読み込む
    mask_list = load_mask_image(output_annotation_path, file_path, class_num)

    debug_image = draw_roi_mode_image(resize_image)
    appgui.draw_image(debug_image)
    appgui.draw_mask_image(mask_list)

    # 設定リセット
    appgui.set_setting_class_id(1)
    appgui.set_setting_lable_background(True)

    # ROI選択モード(ROI_MODE)に遷移
    appgui.mode = appgui.ROI_MODE


# イベントハンドラー：ファイルリスト選択(キーアップ)
def event_handler_file_select_up(event_kind, appgui):
    event_handler_file_select(event_kind, appgui, scroll_count=-1)


# イベントハンドラー：ファイルリスト選択(キーダウン)
def event_handler_file_select_down(event_kind, appgui):
    event_handler_file_select(event_kind, appgui, scroll_count=1)


# イベントハンドラー：クラスID選択
def event_handler_select_class_id(event_kind, appgui):
    global prev_class_id, image_list, mask_list, debug_image_list

    class_id = int(event_kind.replace('-', ''))
    appgui.set_setting_class_id(class_id)

    # クラスID選択変更時
    if prev_class_id != class_id:
        # 描画更新
        debug_image = draw_roi_mode_image(image_list[class_id])
        debug_image_list[class_id] = debug_image

        appgui.draw_image(debug_image_list[class_id])
        appgui.draw_mask_image(mask_list)
        appgui.read_window(timeout=1)

        prev_class_id = class_id

        # 設定リセット
        appgui.set_setting_lable_background(True)

        # ROI選択モード(ROI_MODE)に遷移
        appgui.mode = appgui.ROI_MODE


# イベントハンドラー：前景/後景指定選択
def event_handler_change_manually_label(event_kind, appgui):
    global debug_image_list

    label_background = not appgui.get_setting_lable_background()
    appgui.set_setting_lable_background(label_background)
    label_background = appgui.get_setting_lable_background()

    # 前景/背景情報提示
    if appgui.mode == appgui.GRABCUT_MODE:
        class_id = appgui.get_setting_class_id()
        label_background = appgui.get_setting_lable_background()
        if label_background:
            color = (0, 0, 255)
        else:
            color = (255, 0, 0)
        cv.rectangle(debug_image_list[class_id], (0, 0), (511, 511),
                     color=color,
                     thickness=3)

        appgui.draw_image(debug_image_list[class_id])


# イベントハンドラー：設定変更
def event_handler_change_config(
    event_kind,
    appgui,
    config_file_name='config.json',
):
    config_data = {
        "MASK ALPHA": 0.7,
        "ITERATION": 5,
        "DRAW THICKNESS": 4,
        "OUTPUT WIDTH": 512,
        "OUTPUT HEIGHT": 512,
        "AUTO SAVE": 1
    }

    config_data['MASK ALPHA'] = appgui.get_setting_mask_alpha()

    config_data['ITERATION'] = appgui.get_setting_iteration()

    config_data['DRAW THICKNESS'] = appgui.get_setting_draw_thickness()

    config_data['OUTPUT WIDTH'] = appgui.get_setting_output_width()
    config_data['OUTPUT HEIGHT'] = appgui.get_setting_output_height()

    auto_save = appgui.get_setting_auto_save()
    if auto_save:
        config_data['AUTO SAVE'] = 1
    else:
        config_data['AUTO SAVE'] = 0

    with open(config_file_name, mode='wt', encoding='utf-8') as file:
        json.dump(config_data, file, ensure_ascii=False, indent=4)


# イベントハンドラー：NOP
def event_handler_change_nop(event_kind, appgui):
    pass


# イベントハンドラーリスト取得
def get_event_handler_list():
    event_handler = {
        '-IMAGE ORIGINAL-': event_handler_change_nop,
        '-IMAGE ORIGINAL-+UP': event_handler_change_nop,
        '-LISTBOX FILE-': event_handler_file_select,
        '-SPIN MASK ALPHA-': event_handler_change_config,
        '-SPIN ITERATION-': event_handler_change_config,
        '-SPIN DRAW THICKNESS-': event_handler_change_config,
        '-SPIN OUTPUT WIDTH-': event_handler_change_config,
        '-SPIN OUTPUT HEIGHT-': event_handler_change_config,
        '-CHECKBOX AUTO SAVE-': event_handler_change_config,
        '-00-': event_handler_select_class_id,
        '-01-': event_handler_select_class_id,
        '-02-': event_handler_select_class_id,
        '-03-': event_handler_select_class_id,
        '-04-': event_handler_select_class_id,
        '-05-': event_handler_select_class_id,
        '-06-': event_handler_select_class_id,
        '-07-': event_handler_select_class_id,
        '-08-': event_handler_select_class_id,
        '-09-': event_handler_select_class_id,
        '-10-': event_handler_select_class_id,
        '-11-': event_handler_select_class_id,
        '-12-': event_handler_select_class_id,
        '-13-': event_handler_select_class_id,
        '-14-': event_handler_select_class_id,
        '-15-': event_handler_select_class_id,
        '-16-': event_handler_select_class_id,
        '-17-': event_handler_select_class_id,
        '-18-': event_handler_select_class_id,
        '-19-': event_handler_select_class_id,
        '-255-': event_handler_select_class_id,
        'Up': event_handler_file_select_up,
        'Down': event_handler_file_select_down,
        's': event_handler_change_nop,
        'Control': event_handler_change_manually_label,
        'Escape': event_handler_change_nop,
    }

    return event_handler


def main():
    global image_list, mask_list, debug_image_list, bgd_model_list, \
            fgd_model_list, output_annotation_path, prev_class_id

    # 引数解析 #################################################################
    args = get_args()

    input_path = os.path.join(args.input, '*')
    output_image_path = args.output_image
    output_annotation_path = args.output_annotation
    config_file_name = args.config

    # 入力ファイルリスト作成 ####################################################
    file_paths = sorted([
        p for p in glob.glob(input_path)
        if re.search('/*\.(jpg|jpeg|png|gif|bmp)', str(p))
    ])

    # GUI初期化 ################################################################
    appgui = gui.AppGui(file_paths)
    _ = appgui.load_config(config_file_name)

    # 画像初期設定 ##############################################################
    grabcut_image_size = (512, 512)

    # オリジナル画像
    currrent_index = appgui.get_file_list_current_index()
    image = cv.imread(file_paths[currrent_index])
    resize_image = cv.resize(image, grabcut_image_size)

    debug_image = draw_roi_mode_image(resize_image)

    # マスク画像
    mask = np.zeros(resize_image.shape[:2], dtype=np.uint8)

    # GrubCut用変数初期化 ######################################################
    class_num = 22
    initialize_grabcut_list(class_num, resize_image, mask)

    # 既存のマスクファイルを確認し、存在すれば読み込む
    mask_list = load_mask_image(output_annotation_path,
                                file_paths[currrent_index], class_num)

    # 画面初期描画
    appgui.draw_image(debug_image)
    appgui.draw_mask_image(mask_list)

    # マウス座標 ###############################################################
    mouse_event = None
    mouse_start_point, mouse_end_point, mouse_prev_point = None, None, None
    mosue_info = [
        mouse_event,
        mouse_start_point,
        mouse_end_point,
        mouse_prev_point,
    ]

    # 動作モード ###############################################################
    appgui.mode = appgui.ROI_MODE

    process_func = [
        process_select_roi_mode,  # ROI_MODE
        process_grabcut_mode,  # GRABCUT_MODE
    ]

    # クラスID
    prev_class_id = appgui.get_setting_class_id()

    # イベントハンドラーリスト ##################################################
    event_handler_list = get_event_handler_list()

    while True:
        event, _ = appgui.read_window()
        auto_save = appgui.get_setting_auto_save()
        class_id = appgui.get_setting_class_id()
        output_width = appgui.get_setting_output_width()
        output_height = appgui.get_setting_output_height()

        # マウス座標
        mosue_info = get_mouse_start_end_point(
            appgui,
            mosue_info,
        )

        # モードに応じたGrabCut処理
        grabcut_exec, mask, bgd_model, fgd_model, debug_image = process_func[
            appgui.mode](
                appgui,
                mosue_info,
                image_list[class_id],
                debug_image_list[class_id],
                mask_list[class_id],
                bgd_model_list[class_id],
                fgd_model_list[class_id],
            )
        debug_image_list[class_id] = debug_image
        mask_list[class_id] = mask
        bgd_model_list[class_id] = bgd_model
        fgd_model_list[class_id] = fgd_model

        # GrubCut実行時
        if grabcut_exec:
            # リサイズ画像および、マスク画像保存
            currrent_index = appgui.get_file_list_current_index()
            file_path = appgui.get_file_path_from_listbox(currrent_index)
            if auto_save:
                util.save_image_and_mask(
                    output_image_path,
                    image_list[class_id],
                    output_annotation_path,
                    mask_list,
                    file_path,
                    (output_width, output_height),
                )

            # マウス状態初期化
            mosue_info = [None, None, None, None]

        # イベント種別取得
        event_kind = get_event_kind(event)
        # イベントに応じた処理を実行
        event_handler = event_handler_list.get(event_kind)
        if event_handler is not None:
            event_handler(event_kind, appgui)

        # 保存
        if event_kind == 's':
            # リサイズ画像および、マスク画像保存
            util.save_image_and_mask(
                output_image_path,
                image_list[class_id],
                output_annotation_path,
                mask_list,
                file_paths[currrent_index],
                (output_width, output_height),
            )
        # 終了
        if event_kind == 'Escape':
            break


if __name__ == '__main__':
    main()
