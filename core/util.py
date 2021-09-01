#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import copy

import cv2 as cv
import numpy as np
from PIL import Image


def execute_grabcut(
    image,
    mask,
    bgd_model,
    fgd_model,
    iteration,
    mask_alpha,
    mask_beta,
    roi=None,
):
    # GrabCut実施
    if roi is not None:
        mask, bgd_model, fgd_model = cv.grabCut(image, mask, roi, bgd_model,
                                                fgd_model, iteration,
                                                cv.GC_INIT_WITH_RECT)
    else:
        mask, bgd_model, fgd_model = cv.grabCut(image, mask, None, bgd_model,
                                                fgd_model, iteration,
                                                cv.GC_INIT_WITH_MASK)

    # デバッグ用マスク重畳画像
    mask2 = copy.deepcopy(mask)
    mask2 = np.where((mask2 == 2) | (mask2 == 0), 0, 1).astype('uint8')
    debug_image = image * mask2[:, :, np.newaxis]
    debug_image = cv.addWeighted(debug_image, mask_alpha, image, mask_beta, 0)

    return mask, bgd_model, fgd_model, debug_image


def get_palette():
    palette = [[0, 0, 0], [128, 0, 0], [0, 128, 0], [128, 128, 0], [0, 0, 128],
               [128, 0, 128], [0, 128, 128], [128, 128, 128], [64, 0, 0],
               [192, 0, 0], [64, 128, 0], [192, 128, 0], [64, 0, 128],
               [192, 0, 128], [64, 128, 128], [192, 128, 128], [0, 64, 0],
               [128, 64, 0], [0, 192, 0], [128, 192, 0], [0, 64, 128],
               [128, 64, 128]]
    return np.asarray(palette)


def save_index_color_png(output_path, filename, mask_image):
    # ファイル名(拡張子無し)取得
    base_filename = os.path.splitext(os.path.basename(filename))[0]

    # 保存先パス作成
    save_path = os.path.join(output_path, base_filename + '.png')

    # インデックスカラーモードで保存
    color_palette = get_palette().flatten()
    color_palette = color_palette.tolist()
    with Image.fromarray(mask_image, mode="P") as png_image:
        png_image.putpalette(color_palette)
        png_image.save(save_path)


def save_resize_image(output_path, filename, image):
    # ファイル名(拡張子無し)取得
    base_filename = os.path.splitext(os.path.basename(filename))[0]

    # 保存先パス作成
    save_path = os.path.join(output_path, base_filename + '.png')

    cv.imwrite(save_path, image)


def save_image_and_mask(
    output_image_path,
    image,
    output_annotation_path,
    mask_list,
    image_file_path,
    output_size,
):
    # セマンティックセグメンテーション カラーパレット取得
    color_palette = get_palette().flatten()
    color_palette = color_palette.tolist()

    # 各クラスを統合した画像を生成
    debug_mask = copy.deepcopy(mask_list[0])
    for index, mask in enumerate(mask_list):
        temp_mask = copy.deepcopy(mask)
        debug_mask = np.where((temp_mask == 2) | (temp_mask == 0), debug_mask,
                              index).astype('uint8')

    # リサイズ
    resize_image = cv.resize(image, output_size)
    resize_mask = cv.resize(debug_mask, output_size)

    save_index_color_png(output_annotation_path, image_file_path, resize_mask)
    save_resize_image(output_image_path, image_file_path, resize_image)
