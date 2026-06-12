# -*- coding: utf-8 -*-
"""
explicate.py  —  解析几何剖面法 · 可复用引擎
=================================================
把 V3 年轮三切法蒸馏出的通用积木：
  · 韵律生成      rhythm_radii()           —— 用叠加正弦造"疏密有律"的序列（本体的纹理节奏）
  · 本体绘制      draw_cylinder() / draw_rings_top()
  · 解析求交      Plane / intersect_circle_plane() / oblique_ellipse()  —— 闭式导出显象曲线
  · 审美系统      AESTHETIC, setup_fonts(), save_fig(), panel_3d(), dim_arrow()
设计意图：搭新原理时 `from explicate import *`，按 SKILL.md 的七步拼装即可。
直接运行本文件会产出一张"通用最小示范图"，验证引擎可用。
"""

import os
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# ============================================================
# 审美 DNA —— 详见 references/aesthetic-system.md
# ============================================================
AESTHETIC = {
    "bg_cream":   "#faf5ee",          # 主奶油底
    "bg_tints":   ["#fff5f0", "#f0f0ff", "#f0fff0"],   # 三切法族的极淡背景
    "accents":    ["#8B4513", "#333399", "#2d6b2d"],   # 三切法族主色：暖棕/靛蓝/松绿
    "accents_hi": ["red", "blue", "green"],            # 在体定位时的高饱和标注色
    "wood_line":  "#8B6914",          # 年轮主线（暖金）
    "wood_dark":  "#5a3e00",          # 顶面年轮深线
    "shell":      "#c8a876",          # 半透明外壳
    "edge":       "#6b4c1e",          # 轮廓
    "lw_base":    0.4,                # 线宽基准
    "lw_span":    1.5,                # 线宽随疏密的浮动幅度
    "dpi":        200,
}


def setup_fonts():
    """中文字体 + 负号。每个脚本开头调用一次。"""
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def save_fig(fig, out_dir, filename):
    """统一高清导出。"""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    fig.savefig(path, dpi=AESTHETIC["dpi"], bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  已保存: {path}")
    return path


# ============================================================
# 第1步积木 · 韵律生成（疏密有律，非随机）
# ============================================================
def rhythm_radii(n=20, base=0.25, harmonics=((0.15, 0.6), (0.08, 1.7), (0.05, 3.2)), floor=0.1):
    """
    用叠加正弦生成"疏密有节奏"的累积半径序列。
    这是本体纹理"有机却确定"的来源——改 harmonics 即换一种呼吸节奏。

    n         环数
    base      平均间距
    harmonics (振幅, 频率) 列表，叠加成间距调制
    floor     最小间距下限
    返回      长度 n 的累积半径数组（单调递增）
    """
    spacings = []
    for i in range(n):
        sp = base + sum(a * np.sin(i * f) for a, f in harmonics)
        spacings.append(max(floor, sp))
    return np.cumsum(spacings)


def spacings_of(radii):
    """从累积半径还原相邻间距（用于线宽随疏密变化）。"""
    return np.diff(np.concatenate([[0.0], radii]))


def rhythm_linewidth(sp, spacings, lo=None, span=None):
    """线宽 ∝ 间距：疏处粗、密处细，强化疏密韵律。"""
    lo = AESTHETIC["lw_base"] if lo is None else lo
    span = AESTHETIC["lw_span"] if span is None else span
    return lo + sp / max(spacings) * span


# ============================================================
# 第1步积木 · 本体绘制（圆柱树干 + 顶面年轮）
# ============================================================
def draw_cylinder(ax, R, H, color=None, alpha=0.12, edge=None, n_theta=80, n_z=40):
    """半透明圆柱外壳——通用"本体"容器。"""
    color = color or AESTHETIC["shell"]
    edge = edge or "#a08050"
    theta = np.linspace(0, 2 * np.pi, n_theta)
    z = np.linspace(0, H, n_z)
    Th, Z = np.meshgrid(theta, z)
    ax.plot_surface(R * np.cos(Th), R * np.sin(Th), Z,
                    color=color, alpha=alpha, rstride=2, cstride=2,
                    linewidth=0.3, edgecolor=edge)


def draw_rings_top(ax, radii, R, z_level, color=None, lw=1.6, alpha=0.7, wobble=0.03):
    """在 z=z_level 的横截面上画同心年轮（带极轻微自然扰动）。"""
    color = color or AESTHETIC["wood_dark"]
    t = np.linspace(0, 2 * np.pi, 200)
    for r in radii:
        if r < R:
            noise = wobble * r * np.sin(t * 3 + r * 0.5)
            ax.plot((r + noise) * np.cos(t), (r + noise) * np.sin(t),
                    np.full_like(t, z_level), color=color, linewidth=lw, alpha=alpha)


# ============================================================
# 第2-3步积木 · 解析求交（闭式导出显象曲线）
# ============================================================
class Plane:
    """
    切面 = 点 p0 + 法向 n。提供与同心环的解析交线。
    径切: Plane(point=(0,0,0), normal=(0,1,0))   过轴
    弦切: Plane(point=(0,y0,0), normal=(0,1,0))  偏移 y0
    斜切: 用 oblique_ellipse() 更直接
    """
    def __init__(self, point, normal):
        self.p0 = np.asarray(point, float)
        self.n = np.asarray(normal, float)
        self.n /= np.linalg.norm(self.n)


def intersect_circle_plane(r, y0):
    """
    半径 r 的圆 (x²+y²=r²) 与竖直面 y=y0 的交线半宽。
    返回 x_cross = √(r²−y0²)；若 r<=|y0| 返回 None（无交线，如实跳过）。
    径切是 y0=0 的特例 → x_cross=r（整条直径）。
    """
    if r <= abs(y0):
        return None
    return np.sqrt(r * r - y0 * y0)


def chord_parabola(r, y0, x_cross, x_panel, z_base, amp):
    """
    弦切显象：把交线在面板上展开成抛物线（山形纹/大教堂纹）。
    z = z_base + amp * (1 - (x_norm / x_cross)²)
    x_panel  面板横坐标采样
    返回      (z 数组)
    """
    x_norm = x_panel
    return z_base + amp * (1.0 - (x_norm / (x_cross + 1e-9)) ** 2)


def oblique_ellipse(r, R, angle_deg, n=120, wobble=0.0):
    """
    斜切显象：同心圆被角度 θ 的斜面切出椭圆，长轴按 1/cosθ 拉伸。
    返回参数曲线 (x, y)，半径比例 r/R 缩放，可选极轻噪声。
    """
    t = np.linspace(0, 2 * np.pi, n)
    a = R                                   # 短轴
    b = R / np.cos(np.radians(angle_deg))   # 长轴（拉伸）
    ratio = r / R
    x = ratio * a * np.cos(t)
    y = ratio * b * np.sin(t)
    if wobble:
        nz = wobble * r * np.sin(t * 3 + r * 0.7)
        x += nz * np.cos(t)
        y += nz * np.sin(t)
    return x, y


# ============================================================
# 第5步积木 · 规整化面板 + 尺寸标注
# ============================================================
def panel_3d(ax, W, H, thickness=0.3, face=None, edge="#555"):
    """画一块标准矩形造型板（正面+侧面+顶面），规整化显象的载体。"""
    face = face or AESTHETIC["bg_cream"]
    front = [list(zip([0, W, W, 0], [0, 0, 0, 0], [0, 0, H, H]))]
    ax.add_collection3d(Poly3DCollection(front, alpha=0.15, facecolor=face,
                                         edgecolor=edge, linewidth=1.5))
    side = [list(zip([W, W, W, W], [0, thickness, thickness, 0], [0, 0, H, H]))]
    ax.add_collection3d(Poly3DCollection(side, alpha=0.2, facecolor="#d0d0d0",
                                         edgecolor=edge, linewidth=0.8))
    top = [list(zip([0, W, W, 0], [0, 0, thickness, thickness], [H, H, H, H]))]
    ax.add_collection3d(Poly3DCollection(top, alpha=0.15, facecolor="#ddd",
                                         edgecolor=edge, linewidth=0.8))


def dim_arrow(ax2d, p0, p1, label, color="#333", offset_text=0.4, rotation=0):
    """2D 双箭头尺寸标注。p0,p1 为端点。"""
    ax2d.annotate("", xy=p1, xytext=p0,
                  arrowprops=dict(arrowstyle="<->", color=color, lw=1))
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    ax2d.text(mid[0] + offset_text * (rotation == 90),
              mid[1] - offset_text * (rotation == 0),
              label, fontsize=9, color=color, ha="center", va="center",
              rotation=rotation)


# ============================================================
# 通用最小示范（运行本文件即产出，验证引擎）
# ============================================================
def _demo(out_dir):
    setup_fonts()
    radii = rhythm_radii(18)
    sp = spacings_of(radii)
    R = 5.0

    fig = plt.figure(figsize=(18, 6))
    fig.suptitle("解析几何剖面法 · 引擎自检：同一本体，三种切法三种显象",
                 fontsize=16, fontweight="bold")

    # 径切 → 平行线
    ax1 = fig.add_subplot(1, 3, 1); ax1.set_facecolor(AESTHETIC["bg_tints"][0])
    z = 0
    for i, s in enumerate(sp):
        z += s
        ax1.plot([-R * .95, R * .95], [z, z], color=AESTHETIC["accents"][0],
                 lw=rhythm_linewidth(s, sp), alpha=0.8)
    ax1.set_title("径切 → 平行线", color=AESTHETIC["accents"][0]); ax1.axis("off")
    ax1.set_xlim(-R, R); ax1.set_ylim(0, radii[-1] + 1)

    # 弦切 → 嵌套抛物线
    ax2 = fig.add_subplot(1, 3, 2); ax2.set_facecolor(AESTHETIC["bg_tints"][1])
    y0 = 3.2
    xp = np.linspace(-1, 1, 150)
    for i, r in enumerate(radii):
        xc = intersect_circle_plane(r, y0)
        if xc is None:
            continue
        zb = (r - y0) / (R - y0 + 1e-9) * 8
        zc = chord_parabola(r, y0, 1.0, xp, zb, 1.0 + 0.5 * r / R)
        ax2.plot(xp * xc, zc, color=AESTHETIC["accents"][1],
                 lw=rhythm_linewidth(sp[min(i, len(sp) - 1)], sp), alpha=0.8)
    ax2.set_title("弦切 → 嵌套抛物线（山形纹）", color=AESTHETIC["accents"][1]); ax2.axis("off")

    # 斜切 → 拉伸椭圆
    ax3 = fig.add_subplot(1, 3, 3); ax3.set_facecolor(AESTHETIC["bg_tints"][2])
    for i, r in enumerate(radii):
        if r >= R:
            break
        x, y = oblique_ellipse(r, R, 40, wobble=0.02)
        ax3.plot(x, y, color=AESTHETIC["accents"][2],
                 lw=rhythm_linewidth(sp[min(i, len(sp) - 1)], sp), alpha=0.7)
    ax3.set_title("斜切 → 拉伸椭圆", color=AESTHETIC["accents"][2])
    ax3.set_aspect("equal"); ax3.axis("off")

    plt.tight_layout()
    save_fig(fig, out_dir, "ENGINE_self_check.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="解析几何剖面法引擎自检")
    ap.add_argument("--out", default=os.path.join(os.getcwd(), "explicate_out"),
                    help="输出目录")
    args = ap.parse_args()
    print("引擎自检中……")
    _demo(args.out)
    print("完成。若三张图正常显示，引擎可用。")
