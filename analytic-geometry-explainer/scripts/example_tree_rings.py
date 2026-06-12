# -*- coding: utf-8 -*-
"""
example_tree_rings.py  —  年轮三切法 · 参考实现（V3 原法，蒸馏自骨架）
======================================================================
这是"解析几何剖面法"的标准范例，复刻 V3 系列五图：
  V3_01 在体定位   —— 树干 + 三切面位置
  V3_02 单面纹理   —— 三种切面各自的年轮纹理立体
  V3_03 爆炸对应   —— 切法 ↔ 纹理 一一对应（连线）
  V3_04 规整标注   —— 从自然年轮到建筑铝板（带尺寸）
  V3_05 多角度旋转 —— 三种造型板 × 四视角

搭新原理时，把它当骨架：保留"本体→切法→解析求交→多视图→规整→审美"的结构，
替换 ① 本体（这里是圆柱+同心环）② 切法 ③ 每种切法的闭式交线。

用法:  python example_tree_rings.py --out "C:\\输出目录"
依赖:  numpy, matplotlib；可与 explicate.py 同目录（本文件自包含，不强制 import）
"""

import os
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


# ----- 第1步：本体纹理的韵律（疏密有律，叠加正弦） -----
def ring_radii(n=20):
    spacings = []
    for i in range(n):
        sp = 0.25 + 0.15 * np.sin(i * 0.6) + 0.08 * np.sin(i * 1.7) + 0.05 * np.sin(i * 3.2)
        spacings.append(max(0.1, sp))
    return np.cumsum(spacings)


# ============================================================
# 图1：在体定位 —— 完整树干 + 三个切面位置
# ============================================================
def fig1_full_log_with_cuts(OUT):
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('年轮立体模型 — 树干与三种切面位置', fontsize=22, fontweight='bold', y=0.95)
    ax = fig.add_subplot(111, projection='3d')

    R_log, H_log = 5.0, 16.0

    theta = np.linspace(0, 2 * np.pi, 80)
    z_cyl = np.linspace(0, H_log, 40)
    Theta, Z = np.meshgrid(theta, z_cyl)
    ax.plot_surface(R_log * np.cos(Theta), R_log * np.sin(Theta), Z, color='#c8a876',
                    alpha=0.12, rstride=2, cstride=2, linewidth=0.3, edgecolor='#a08050')

    t_outline = np.linspace(0, 2 * np.pi, 200)
    ax.plot(R_log * np.cos(t_outline), R_log * np.sin(t_outline),
            np.ones_like(t_outline) * H_log, color='#6b4c1e', linewidth=2.0, alpha=0.8)
    ax.plot(R_log * np.cos(t_outline), R_log * np.sin(t_outline),
            np.zeros_like(t_outline), color='#6b4c1e', linewidth=2.0, alpha=0.6)
    for angle in np.linspace(0, 2 * np.pi, 12, endpoint=False):
        ax.plot([R_log * np.cos(angle)] * 2, [R_log * np.sin(angle)] * 2,
                [0, H_log], color='#8b6c3e', linewidth=0.8, alpha=0.35)

    radii = ring_radii(18)
    for r in radii:
        if r < R_log:
            t = np.linspace(0, 2 * np.pi, 200)
            noise = 0.03 * r * np.sin(t * 3 + r * 0.5)
            ax.plot((r + noise) * np.cos(t), (r + noise) * np.sin(t),
                    np.ones_like(t) * H_log, color='#5a3e00', linewidth=1.8, alpha=0.75)

    # 切面1 径切（过圆心 y=0）→ 红
    x_rad = np.linspace(-R_log, R_log, 2); z_rad = np.linspace(0, H_log, 2)
    X_rad, Z_rad = np.meshgrid(x_rad, z_rad); Y_rad = np.zeros_like(X_rad)
    ax.plot_surface(X_rad, Y_rad, Z_rad, color='red', alpha=0.25, zorder=10)
    ax.plot([-R_log, R_log, R_log, -R_log, -R_log], [0, 0, 0, 0, 0],
            [0, 0, H_log, H_log, 0], color='red', linewidth=2.5, zorder=11)
    ax.text(R_log + 0.5, 0, H_log / 2, '径切面\n(过圆心)', fontsize=12, color='red', fontweight='bold')

    # 切面2 弦切（偏移 y=3.2）→ 蓝
    y_tang = 3.2
    x_tang_max = np.sqrt(R_log**2 - y_tang**2)
    x_tang = np.linspace(-x_tang_max, x_tang_max, 2); z_tang = np.linspace(0, H_log, 2)
    X_tang, Z_tang = np.meshgrid(x_tang, z_tang); Y_tang = np.ones_like(X_tang) * y_tang
    ax.plot_surface(X_tang, Y_tang, Z_tang, color='blue', alpha=0.25, zorder=10)
    ax.plot([-x_tang_max, x_tang_max, x_tang_max, -x_tang_max, -x_tang_max], [y_tang] * 5,
            [0, 0, H_log, H_log, 0], color='blue', linewidth=2.5, zorder=11)
    ax.text(x_tang_max + 0.5, y_tang, H_log / 2, '弦切面\n(偏离圆心)', fontsize=12, color='blue', fontweight='bold')

    # 切面3 斜切（z = 8 + 0.5x + 0.3y）→ 绿
    u = np.linspace(-R_log, R_log, 20); v = np.linspace(-R_log, R_log, 20)
    U, V = np.meshgrid(u, v)
    Z_oblique = 8 + 0.5 * U + 0.3 * V
    mask = np.sqrt(U**2 + V**2) <= R_log
    ax.plot_surface(U, V, np.where(mask, Z_oblique, np.nan), color='green', alpha=0.3,
                    zorder=10, rstride=1, cstride=1)
    t_ell = np.linspace(0, 2 * np.pi, 200)
    x_ell = R_log * np.cos(t_ell); y_ell = R_log * np.sin(t_ell)
    ax.plot(x_ell, y_ell, 8 + 0.5 * x_ell + 0.3 * y_ell, color='green', linewidth=2.5, zorder=11)
    ax.text(0, -R_log - 1.5, 8, '斜切面\n(45度角)', fontsize=12, color='green', fontweight='bold')

    ax.plot([0, 0], [0, 0], [0, H_log], color='#4a3000', linewidth=1.5, linestyle='--', alpha=0.5)
    ax.text(0.3, 0.3, H_log + 0.5, '树心', fontsize=10, color='#4a3000')

    ax.view_init(elev=22, azim=-50)
    ax.set_xlim(-8, 8); ax.set_ylim(-8, 8); ax.set_zlim(-1, H_log + 2)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z (树干方向)')
    ax.set_title('三维树干模型 — 三种切面位置关系', fontsize=16, pad=20)
    _save(fig, OUT, 'V3_01_树干立体切面位置.png')


# ============================================================
# 图2：单面纹理 —— 三个切面各自的年轮纹理
# ============================================================
def fig2_three_cut_surfaces(OUT):
    fig = plt.figure(figsize=(24, 8))
    fig.suptitle('三种切面上的年轮纹理 — 立体几何效果', fontsize=20, fontweight='bold', y=1.02)
    radii = ring_radii(20); R_log = 5.0
    spacings_vis = np.diff(np.concatenate([[0], radii]))
    H_panel = 12

    # 径切 → 平行线
    ax1 = fig.add_subplot(1, 3, 1, projection='3d'); ax1.set_facecolor('#faf5ee')
    x_f = np.array([-R_log, R_log, R_log, -R_log]); z_f = np.array([0, 0, H_panel, H_panel])
    ax1.add_collection3d(Poly3DCollection([list(zip(x_f, np.zeros(4), z_f))], alpha=0.15,
                         facecolor='#e8d8b8', edgecolor='#8B6914', linewidth=1))
    z_pos = 0
    for i, sp in enumerate(spacings_vis):
        z_pos += sp * (H_panel / max(radii))
        if z_pos > H_panel: break
        x_line = np.linspace(-R_log * 0.95, R_log * 0.95, 100)
        z_line = z_pos + 0.05 * np.sin(x_line * 0.3 + i * 0.5)
        lw = 0.4 + sp / max(spacings_vis) * 1.5
        ax1.plot(x_line, np.ones_like(x_line) * 0.001, z_line, color='#8B6914', linewidth=lw, alpha=0.7)
    ax1.view_init(elev=15, azim=-70); ax1.set_xlim(-6, 6); ax1.set_ylim(-2, 4); ax1.set_zlim(-1, H_panel + 1)
    ax1.set_title('径切面板\n平行线 + 疏密韵律', fontsize=14, color='red', pad=15); ax1.axis('off')

    # 弦切 → 山形纹（抛物线）
    ax2 = fig.add_subplot(1, 3, 2, projection='3d'); ax2.set_facecolor('#faf5ee')
    y_offset = 3.2; x_max = np.sqrt(R_log**2 - y_offset**2)
    x_t = np.array([-x_max, x_max, x_max, -x_max]); z_t = np.array([0, 0, H_panel, H_panel])
    ax2.add_collection3d(Poly3DCollection([list(zip(x_t, np.zeros(4), z_t))], alpha=0.15,
                         facecolor='#e8d8b8', edgecolor='#8B6914', linewidth=1))
    for i, r in enumerate(radii):
        if r <= y_offset: continue
        x_cross = min(np.sqrt(r**2 - y_offset**2), x_max)
        x_para = np.linspace(-x_cross * 0.95, x_cross * 0.95, 150)
        z_base = (r - y_offset) * (H_panel / (max(radii) - y_offset + 0.1))
        amp = 1.0 + 0.5 * (r / max(radii))
        z_para = z_base + amp * (1 - (x_para / (x_cross + 0.01))**2)
        valid = (z_para > 0) & (z_para < H_panel)
        if np.sum(valid) > 5:
            sp = spacings_vis[min(i, len(spacings_vis) - 1)]
            ax2.plot(x_para[valid], np.ones(np.sum(valid)) * 0.001, z_para[valid],
                     color='#8B6914', linewidth=0.4 + sp / max(spacings_vis) * 1.2, alpha=0.7)
    ax2.view_init(elev=15, azim=-70); ax2.set_xlim(-5, 5); ax2.set_ylim(-2, 4); ax2.set_zlim(-1, H_panel + 1)
    ax2.set_title('弦切面板\n山形纹 / 大教堂纹', fontsize=14, color='blue', pad=15); ax2.axis('off')

    # 斜切 → 同心椭圆
    ax3 = fig.add_subplot(1, 3, 3, projection='3d'); ax3.set_facecolor('#faf5ee')
    cut_angle = 40
    t_ell = np.linspace(0, 2 * np.pi, 100)
    a_ell = R_log; b_ell = R_log / np.cos(np.radians(cut_angle))
    x_panel = a_ell * np.cos(t_ell); z_panel = b_ell * np.sin(t_ell)
    ax3.plot(x_panel, np.zeros_like(t_ell), z_panel, color='#8B6914', linewidth=1.5, alpha=0.8)
    for j in range(len(t_ell) - 1):
        tri = [[0, 0, 0], [x_panel[j], 0, z_panel[j]], [x_panel[j + 1], 0, z_panel[j + 1]]]
        ax3.add_collection3d(Poly3DCollection([tri], alpha=0.08, facecolor='#e8d8b8', edgecolor='none'))
    for i, r in enumerate(radii):
        if r >= R_log: break
        rr = r / R_log
        x_ring = rr * a_ell * np.cos(t_ell); z_ring = rr * b_ell * np.sin(t_ell)
        noise = 0.02 * r * np.sin(t_ell * 3 + r * 0.7)
        x_ring += noise * np.cos(t_ell); z_ring += noise * np.sin(t_ell)
        sp = spacings_vis[min(i, len(spacings_vis) - 1)]
        ax3.plot(x_ring, np.ones_like(t_ell) * 0.001, z_ring, color='#8B6914',
                 linewidth=0.3 + sp / max(spacings_vis) * 1.0, alpha=0.6)
    ax3.view_init(elev=20, azim=-65); ax3.set_xlim(-7, 7); ax3.set_ylim(-3, 5); ax3.set_zlim(-8, 8)
    ax3.set_title('斜切面板\n椭圆弧 / 拉伸年轮', fontsize=14, color='green', pad=15); ax3.axis('off')

    plt.tight_layout()
    _save(fig, OUT, 'V3_02_三种切面纹理立体.png')


# ============================================================
# 图3：爆炸对应 —— 切法 ↔ 纹理 连线
# ============================================================
def fig3_exploded_view(OUT):
    fig = plt.figure(figsize=(22, 18))
    fig.suptitle('年轮切面爆炸视图 — 切法与纹理对应关系', fontsize=22, fontweight='bold', y=0.97)
    ax = fig.add_subplot(111, projection='3d')
    R_log, H_log = 5.0, 14.0
    radii = ring_radii(18)
    spacings_vis = np.diff(np.concatenate([[0], radii]))

    theta = np.linspace(0, 2 * np.pi, 60); z_cyl = np.linspace(0, H_log, 30)
    Theta, Z = np.meshgrid(theta, z_cyl)
    ax.plot_surface(R_log * np.cos(Theta), R_log * np.sin(Theta), Z, color='#c8a876',
                    alpha=0.06, rstride=2, cstride=2, linewidth=0.05, edgecolor='#c8a876')
    for r in radii:
        if r < R_log:
            t = np.linspace(0, 2 * np.pi, 200)
            noise = 0.02 * r * np.sin(t * 3 + r)
            ax.plot((r + noise) * np.cos(t), (r + noise) * np.sin(t),
                    np.ones_like(t) * H_log, color='#5a3e00', linewidth=1.0, alpha=0.55)

    # 径切 → 右
    ox = 15
    x_r = np.array([-R_log, R_log, R_log, -R_log]) + ox; z_r = np.array([0, 0, H_log, H_log])
    ax.add_collection3d(Poly3DCollection([list(zip(x_r, np.zeros(4), z_r))], alpha=0.2,
                        facecolor='#ffe0e0', edgecolor='red', linewidth=2))
    x_pos = -R_log * 0.9
    for i, sp in enumerate(spacings_vis):
        x_pos += sp * (2 * R_log * 0.9 / max(radii))
        if x_pos > R_log * 0.9: break
        z_line = np.linspace(0.3, H_log - 0.3, 80)
        x_line = x_pos + 0.04 * np.sin(z_line / H_log * np.pi + i * 0.3) + ox
        ax.plot(x_line, np.ones_like(z_line) * 0.01, z_line, color='#8B4513',
                linewidth=0.7 + sp / max(spacings_vis) * 1.5, alpha=0.8)
    ax.plot([R_log * 0.5, ox - R_log], [0, 0], [H_log / 2, H_log / 2], color='red',
            linewidth=0.8, linestyle=':', alpha=0.5)
    ax.text(ox, 0, H_log + 1, '径切面\n平行纹', fontsize=13, color='red', fontweight='bold', ha='center')

    # 弦切 → 前
    oy = -12; y_offset = 3.2; x_max = np.sqrt(R_log**2 - y_offset**2)
    x_t = np.array([-x_max, x_max, x_max, -x_max]); y_t = np.full(4, oy); z_t = np.array([0, 0, H_log, H_log])
    ax.add_collection3d(Poly3DCollection([list(zip(x_t, y_t, z_t))], alpha=0.2,
                        facecolor='#e0e0ff', edgecolor='blue', linewidth=2))
    for i, r in enumerate(radii):
        if r <= y_offset: continue
        z_cross = min(np.sqrt(r**2 - y_offset**2), H_log / 2)
        z_para = np.linspace(-z_cross * 0.9, z_cross * 0.9, 120) + H_log / 2
        x_base_val = (r - y_offset) * (2 * x_max / (max(radii) - y_offset + 0.1))
        amp = 0.6 + 0.3 * (r / max(radii))
        z_rel = z_para - H_log / 2
        x_para = -x_max + x_base_val + amp * (1 - (z_rel / (z_cross + 0.01))**2)
        valid = (x_para > -x_max + 0.1) & (x_para < x_max - 0.1) & (z_para > 0.2) & (z_para < H_log - 0.2)
        if np.sum(valid) > 5:
            sp = spacings_vis[min(i, len(spacings_vis) - 1)]
            ax.plot(x_para[valid], np.full(np.sum(valid), oy + 0.01), z_para[valid],
                    color='#333399', linewidth=0.7 + sp / max(spacings_vis) * 1.3, alpha=0.8)
    ax.plot([0, 0], [-y_offset, oy + 1], [H_log / 2, H_log / 2], color='blue',
            linewidth=0.8, linestyle=':', alpha=0.5)
    ax.text(0, oy, H_log + 1, '弦切面\n山形纹', fontsize=13, color='blue', fontweight='bold', ha='center')

    # 斜切 → 上
    oox, ooz = -10, 4
    t_ell = np.linspace(0, 2 * np.pi, 100)
    a_ell = R_log; b_ell = R_log / np.cos(np.radians(40))
    x_ell = a_ell * np.cos(t_ell) + oox; y_ell = b_ell * np.sin(t_ell)
    z_ell = np.ones_like(t_ell) * (H_log + ooz)
    ax.plot(x_ell, y_ell, z_ell, color='green', linewidth=2, alpha=0.8)
    for j in range(0, len(t_ell) - 1, 2):
        tri = [[oox, 0, H_log + ooz], [x_ell[j], y_ell[j], z_ell[j]],
               [x_ell[j + 1], y_ell[j + 1], z_ell[j + 1]]]
        ax.add_collection3d(Poly3DCollection([tri], alpha=0.12, facecolor='#e0ffe0', edgecolor='none'))
    for i, r in enumerate(radii):
        if r >= R_log: break
        rr = r / R_log
        x_ring = rr * a_ell * np.cos(t_ell) + oox; y_ring = rr * b_ell * np.sin(t_ell)
        noise = 0.015 * r * np.sin(t_ell * 3 + r)
        x_ring += noise * np.cos(t_ell); y_ring += noise * np.sin(t_ell)
        sp = spacings_vis[min(i, len(spacings_vis) - 1)]
        ax.plot(x_ring, y_ring, np.ones_like(t_ell) * (H_log + ooz) + 0.01, color='#2d6b2d',
                linewidth=0.6 + sp / max(spacings_vis) * 1.0, alpha=0.75)
    ax.plot([0, oox], [0, 0], [H_log * 0.7, H_log + ooz - 0.5], color='green',
            linewidth=0.8, linestyle=':', alpha=0.5)
    ax.text(oox, 0, H_log + ooz + 1.5, '斜切面\n椭圆弧', fontsize=13, color='green', fontweight='bold', ha='center')

    ax.view_init(elev=25, azim=-45)
    ax.set_xlim(-16, 22); ax.set_ylim(-16, 10); ax.set_zlim(-2, H_log + 8); ax.axis('off')
    _save(fig, OUT, 'V3_03_爆炸视图.png')


# ============================================================
# 图4：规整标注 —— 从自然年轮到建筑铝板
# ============================================================
def fig4_regularized_panels(OUT):
    fig = plt.figure(figsize=(24, 20))
    fig.suptitle('规整化几何造型板 — 从自然年轮到建筑铝板', fontsize=22, fontweight='bold', y=0.98)
    radii = ring_radii(20)
    spacings_vis = np.diff(np.concatenate([[0], radii]))
    panel_W, panel_H = 8, 12
    titles = ['径切规整板\n（平行韵律线）', '弦切规整板\n（山形纹/拱形）', '斜切规整板\n（椭圆弧/流线）']
    colors_main = ['#8B4513', '#333399', '#2d6b2d']
    colors_bg = ['#fff5f0', '#f0f0ff', '#f0fff0']
    R_log = 5.0; y_offset = 3.2

    def draw_panel_3d(ax, bg):
        x_f = np.array([0, panel_W, panel_W, 0]); z_f = np.array([0, 0, panel_H, panel_H])
        ax.add_collection3d(Poly3DCollection([list(zip(x_f, np.zeros(4), z_f))], alpha=0.15,
                            facecolor=bg, edgecolor='#555', linewidth=1.5))
        ax.add_collection3d(Poly3DCollection([list(zip([panel_W]*4, [0, .3, .3, 0], z_f))],
                            alpha=0.2, facecolor='#d0d0d0', edgecolor='#555', linewidth=0.8))

    for col in range(3):
        ax3d = fig.add_subplot(2, 3, col + 1, projection='3d'); ax3d.set_facecolor(colors_bg[col])
        draw_panel_3d(ax3d, colors_bg[col])
        if col == 0:
            z_pos = 0
            for i, sp in enumerate(spacings_vis):
                z_pos += sp * (panel_H / max(radii))
                if z_pos > panel_H: break
                x_line = np.linspace(0.2, panel_W - 0.2, 80)
                z_line = z_pos + 0.03 * np.sin(np.pi * x_line / panel_W)
                ax3d.plot(x_line, np.ones_like(x_line) * 0.001, z_line, color=colors_main[0],
                          linewidth=0.5 + sp / max(spacings_vis) * 1.5, alpha=0.8)
        elif col == 1:
            for i, r in enumerate(radii):
                if r <= y_offset or r >= R_log: continue
                x_cross = np.sqrt(r**2 - y_offset**2)
                x_para = np.linspace(0.3, panel_W - 0.3, 120)
                x_norm = (x_para - panel_W / 2) / (panel_W / 2) * x_cross
                z_base = (r - y_offset) / (R_log - y_offset) * panel_H * 0.7 + panel_H * 0.05
                z_para = z_base + 1.5 * (r / R_log) * (1 - (x_norm / (x_cross + 0.01))**2)
                v = (z_para > 0.3) & (z_para < panel_H - 0.3)
                if np.sum(v) > 5:
                    sp = spacings_vis[min(i, len(spacings_vis) - 1)]
                    ax3d.plot(x_para[v], np.ones(np.sum(v)) * 0.001, z_para[v],
                              color=colors_main[1], linewidth=0.5 + sp / max(spacings_vis) * 1.0, alpha=0.8)
        else:
            for i, r in enumerate(radii):
                rr = r / max(radii)
                if rr > 0.95: break
                t = np.linspace(-0.8 * np.pi, 0.8 * np.pi, 150)
                x_arc = panel_W / 2 + panel_W * 0.45 * rr * np.cos(t)
                z_arc = panel_H / 2 + panel_H * 0.4 * rr * np.sin(t)
                v = (x_arc > 0.3) & (x_arc < panel_W - 0.3) & (z_arc > 0.3) & (z_arc < panel_H - 0.3)
                if np.sum(v) > 5:
                    sp = spacings_vis[min(i, len(spacings_vis) - 1)]
                    ax3d.plot(x_arc[v], np.ones(np.sum(v)) * 0.001, z_arc[v],
                              color=colors_main[2], linewidth=0.4 + sp / max(spacings_vis) * 0.8, alpha=0.7)
        ax3d.view_init(elev=12, azim=-72)
        ax3d.set_xlim(-1, panel_W + 2); ax3d.set_ylim(-1, 4); ax3d.set_zlim(-1, panel_H + 1)
        ax3d.set_title(titles[col], fontsize=14, color=colors_main[col], fontweight='bold', pad=15)
        ax3d.axis('off')

    for col in range(3):
        ax2d = fig.add_subplot(2, 3, col + 4); ax2d.set_facecolor(colors_bg[col]); ax2d.set_aspect('equal')
        ax2d.add_patch(plt.Rectangle((0, 0), panel_W, panel_H, fill=False, edgecolor='#333', linewidth=2))
        if col == 0:
            z_pos = 0; zs = []
            for i, sp in enumerate(spacings_vis):
                z_pos += sp * (panel_H / max(radii))
                if z_pos > panel_H: break
                zs.append(z_pos)
                x_line = np.linspace(0.1, panel_W - 0.1, 100)
                ax2d.plot(x_line, z_pos + 0.02 * np.sin(np.pi * x_line / panel_W),
                          color=colors_main[0], linewidth=0.5 + sp / 1.5 * 2, alpha=0.8)
            for k in [1, 5, 10]:
                if k < len(zs) - 1:
                    mid = (zs[k] + zs[k + 1]) / 2
                    ax2d.annotate('', xy=(panel_W + 0.3, zs[k]), xytext=(panel_W + 0.3, zs[k + 1]),
                                  arrowprops=dict(arrowstyle='<->', color='red', lw=1))
                    ax2d.text(panel_W + 0.6, mid, f'{zs[k + 1] - zs[k]:.1f}', fontsize=8, color='red', va='center')
        elif col == 1:
            for i, r in enumerate(radii):
                if r <= y_offset or r >= R_log: continue
                x_cross = np.sqrt(r**2 - y_offset**2)
                x_para = np.linspace(0.2, panel_W - 0.2, 150)
                x_norm = (x_para - panel_W / 2) / (panel_W / 2) * x_cross
                z_base = (r - y_offset) / (R_log - y_offset) * panel_H * 0.7 + panel_H * 0.05
                z_para = z_base + 1.5 * (r / R_log) * (1 - (x_norm / (x_cross + 0.01))**2)
                v = (z_para > 0.2) & (z_para < panel_H - 0.2)
                if np.sum(v) > 5:
                    sp = spacings_vis[min(i, len(spacings_vis) - 1)]
                    ax2d.plot(x_para[v], z_para[v], color=colors_main[1], linewidth=0.5 + sp / max(spacings_vis) * 1.0, alpha=0.8)
        else:
            for i, r in enumerate(radii):
                rr = r / max(radii)
                if rr > 0.95: break
                t = np.linspace(-0.75 * np.pi, 0.75 * np.pi, 150)
                x_arc = panel_W / 2 + panel_W * 0.42 * rr * np.cos(t)
                z_arc = panel_H / 2 + panel_H * 0.4 * rr * np.sin(t)
                v = (x_arc > 0.2) & (x_arc < panel_W - 0.2) & (z_arc > 0.2) & (z_arc < panel_H - 0.2)
                if np.sum(v) > 5:
                    sp = spacings_vis[min(i, len(spacings_vis) - 1)]
                    ax2d.plot(x_arc[v], z_arc[v], color=colors_main[2], linewidth=0.4 + sp / max(spacings_vis) * 0.8, alpha=0.7)
        ax2d.annotate('', xy=(0, -0.8), xytext=(panel_W, -0.8), arrowprops=dict(arrowstyle='<->', color='#333', lw=1))
        ax2d.text(panel_W / 2, -1.3, f'{panel_W}m', fontsize=10, ha='center')
        ax2d.annotate('', xy=(-0.8, 0), xytext=(-0.8, panel_H), arrowprops=dict(arrowstyle='<->', color='#333', lw=1))
        ax2d.text(-1.5, panel_H / 2, f'{panel_H}m', fontsize=10, ha='center', rotation=90)
        ax2d.set_xlim(-2.5, panel_W + 2); ax2d.set_ylim(-2, panel_H + 1)
        ax2d.set_title(f'正面视图 — {titles[col].split(chr(10))[1]}', fontsize=12, pad=10); ax2d.axis('off')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    _save(fig, OUT, 'V3_04_规整化几何造型板.png')


# ============================================================
# 图5：多角度旋转 —— 三种板 × 四视角
# ============================================================
def fig5_multi_angle(OUT):
    fig = plt.figure(figsize=(24, 16))
    fig.suptitle('规整造型板 — 多角度旋转视图', fontsize=20, fontweight='bold', y=0.98)
    radii = ring_radii(20)
    spacings_vis = np.diff(np.concatenate([[0], radii]))
    R_log = 5.0; panel_W, panel_H = 8, 12
    angles = [(15, -75), (15, -30), (15, 15), (75, -45)]
    angle_names = ['左前方', '正前方', '右前方', '俯视']
    colors_main = ['#8B4513', '#333399', '#2d6b2d']; y_off = 3.2

    for row in range(3):
        for col in range(4):
            ax = fig.add_subplot(3, 4, row * 4 + col + 1, projection='3d')
            x_f = np.array([0, panel_W, panel_W, 0]); z_f = np.array([0, 0, panel_H, panel_H])
            ax.add_collection3d(Poly3DCollection([list(zip(x_f, np.zeros(4), z_f))], alpha=0.1,
                                facecolor='#f0ece0', edgecolor='#888', linewidth=1))
            ax.add_collection3d(Poly3DCollection([list(zip([panel_W]*4, [0, .3, .3, 0], z_f))],
                                alpha=0.15, facecolor='#ddd', edgecolor='#888', linewidth=0.5))
            if row == 0:
                z_p = 0
                for i, sp in enumerate(spacings_vis):
                    z_p += sp * (panel_H / max(radii))
                    if z_p > panel_H: break
                    x_l = np.linspace(0.15, panel_W - 0.15, 60)
                    ax.plot(x_l, np.ones_like(x_l) * 0.001, z_p + 0.02 * np.sin(np.pi * x_l / panel_W),
                            color=colors_main[0], linewidth=0.4 + sp / 1.5 * 1.2, alpha=0.8)
            elif row == 1:
                for i, r in enumerate(radii):
                    if r <= y_off or r >= R_log: continue
                    x_cross = np.sqrt(r**2 - y_off**2)
                    x_p = np.linspace(0.3, panel_W - 0.3, 100)
                    x_n = (x_p - panel_W / 2) / (panel_W / 2) * x_cross
                    z_b = (r - y_off) / (R_log - y_off) * panel_H * 0.7 + panel_H * 0.05
                    z_p = z_b + 1.5 * (r / R_log) * (1 - (x_n / (x_cross + 0.01))**2)
                    v = (z_p > 0.3) & (z_p < panel_H - 0.3)
                    if np.sum(v) > 5:
                        sp = spacings_vis[min(i, len(spacings_vis) - 1)]
                        ax.plot(x_p[v], np.ones(np.sum(v)) * 0.001, z_p[v], color=colors_main[1],
                                linewidth=0.4 + sp / max(spacings_vis) * 0.8, alpha=0.8)
            else:
                for i, r in enumerate(radii):
                    rr = r / max(radii)
                    if rr > 0.95: break
                    t = np.linspace(-0.75 * np.pi, 0.75 * np.pi, 120)
                    x_a = panel_W / 2 + panel_W * 0.42 * rr * np.cos(t)
                    z_a = panel_H / 2 + panel_H * 0.4 * rr * np.sin(t)
                    v = (x_a > 0.2) & (x_a < panel_W - 0.2) & (z_a > 0.2) & (z_a < panel_H - 0.2)
                    if np.sum(v) > 5:
                        sp = spacings_vis[min(i, len(spacings_vis) - 1)]
                        ax.plot(x_a[v], np.ones(np.sum(v)) * 0.001, z_a[v], color=colors_main[2],
                                linewidth=0.3 + sp / max(spacings_vis) * 0.7, alpha=0.7)
            ax.view_init(elev=angles[col][0], azim=angles[col][1])
            ax.set_xlim(-1, panel_W + 2); ax.set_ylim(-1, 4); ax.set_zlim(-1, panel_H + 1); ax.axis('off')
            if row == 0:
                ax.set_title(angle_names[col], fontsize=11, pad=5)

    fig.text(0.01, 0.82, '径切板', fontsize=14, color='#8B4513', fontweight='bold', rotation=90, va='center')
    fig.text(0.01, 0.5, '弦切板', fontsize=14, color='#333399', fontweight='bold', rotation=90, va='center')
    fig.text(0.01, 0.18, '斜切板', fontsize=14, color='#2d6b2d', fontweight='bold', rotation=90, va='center')
    plt.tight_layout(rect=[0.03, 0, 1, 0.95])
    _save(fig, OUT, 'V3_05_多角度旋转视图.png')


def _save(fig, OUT, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  已保存: {path}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='年轮三切法 V3 五图参考实现')
    ap.add_argument('--out', default=os.path.join(os.getcwd(), 'tree_ring_out'), help='输出目录')
    args = ap.parse_args()
    print('=' * 60); print('  年轮立体几何模型生成器（解析几何剖面法 · 范例）'); print('=' * 60)
    print('[1/5] 在体定位…');   fig1_full_log_with_cuts(args.out)
    print('[2/5] 单面纹理…');   fig2_three_cut_surfaces(args.out)
    print('[3/5] 爆炸对应…');   fig3_exploded_view(args.out)
    print('[4/5] 规整标注…');   fig4_regularized_panels(args.out)
    print('[5/5] 多角度旋转…'); fig5_multi_angle(args.out)
    print('=' * 60); print(f'  全部完成！输出目录: {args.out}'); print('=' * 60)
