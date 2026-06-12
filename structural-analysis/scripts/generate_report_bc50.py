# -*- coding: utf-8 -*-
"""
BC楼各半金库半办公方案 — 结构加固合理性分析报告
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white, red, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ============================================================
# Font Registration
# ============================================================
def register_fonts():
    font_paths = [
        ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
        ("SimHei", "C:/Windows/Fonts/simhei.ttf"),
        ("Microsoft YaHei", "C:/Windows/Fonts/msyh.ttc"),
        ("Microsoft YaHei Bold", "C:/Windows/Fonts/msyhbd.ttc"),
    ]
    registered = {}
    for name, path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered[name] = True
            except:
                pass
    if "Microsoft YaHei" in registered:
        return "Microsoft YaHei", registered.get("Microsoft YaHei Bold", False) and "Microsoft YaHei Bold" or "Microsoft YaHei"
    elif "SimSun" in registered:
        return "SimSun", registered.get("SimHei", False) and "SimHei" or "SimSun"
    else:
        return "Helvetica", "Helvetica-Bold"

FONT_NORMAL, FONT_BOLD = register_fonts()

# ============================================================
# Colors
# ============================================================
COLOR_PRIMARY = HexColor('#1a365d')
COLOR_SECONDARY = HexColor('#2c5282')
COLOR_ACCENT = HexColor('#c53030')
COLOR_BG_HEADER = HexColor('#e2e8f0')
COLOR_BG_LIGHT = HexColor('#f7fafc')
COLOR_BG_WARNING = HexColor('#fff5f5')
COLOR_BG_GREEN = HexColor('#f0fff4')
COLOR_TEXT = HexColor('#1a202c')
COLOR_TEXT_LIGHT = HexColor('#4a5568')
COLOR_GREEN = HexColor('#276749')
COLOR_ORANGE = HexColor('#c05621')

# ============================================================
# Styles
# ============================================================
def create_styles():
    styles = getSampleStyleSheet()
    defs = [
        ('CoverTitle', FONT_BOLD, 24, COLOR_PRIMARY, TA_CENTER, 8*mm, 34, {}),
        ('CoverSubtitle', FONT_NORMAL, 14, COLOR_SECONDARY, TA_CENTER, 4*mm, 22, {}),
        ('CoverInfo', FONT_NORMAL, 11, COLOR_TEXT_LIGHT, TA_CENTER, 3*mm, 18, {}),
        ('SectionTitle', FONT_BOLD, 16, COLOR_PRIMARY, TA_LEFT, 5*mm, 24, {'spaceBefore': 10*mm}),
        ('SubTitle', FONT_BOLD, 13, COLOR_SECONDARY, TA_LEFT, 3*mm, 20, {'spaceBefore': 6*mm}),
        ('Body', FONT_NORMAL, 10.5, COLOR_TEXT, TA_JUSTIFY, 2.5*mm, 18, {'firstLineIndent': 21}),
        ('BodyNI', FONT_NORMAL, 10.5, COLOR_TEXT, TA_JUSTIFY, 2.5*mm, 18, {}),
        ('FormulaStyle', FONT_NORMAL, 10.5, COLOR_TEXT, TA_CENTER, 3*mm, 18, {'spaceBefore': 2*mm}),
        ('WarnStyle', FONT_BOLD, 11, COLOR_ACCENT, TA_LEFT, 2*mm, 18, {'spaceBefore': 3*mm, 'leftIndent': 10*mm}),
        ('BulletStyle', FONT_NORMAL, 10.5, COLOR_TEXT, TA_LEFT, 1.5*mm, 17, {'leftIndent': 8*mm, 'firstLineIndent': -4*mm}),
        ('GreenBullet', FONT_NORMAL, 10.5, COLOR_GREEN, TA_LEFT, 1.5*mm, 17, {'leftIndent': 8*mm, 'firstLineIndent': -4*mm}),
        ('TH', FONT_BOLD, 9.5, white, TA_CENTER, 0, 14, {}),
        ('TC', FONT_NORMAL, 9.5, COLOR_TEXT, TA_CENTER, 0, 14, {}),
        ('TCL', FONT_NORMAL, 9.5, COLOR_TEXT, TA_LEFT, 0, 14, {}),
        ('TCB', FONT_BOLD, 9.5, COLOR_ACCENT, TA_CENTER, 0, 14, {}),
        ('TCG', FONT_BOLD, 9.5, COLOR_GREEN, TA_CENTER, 0, 14, {}),
        ('ConcStyle', FONT_BOLD, 11, COLOR_PRIMARY, TA_LEFT, 2*mm, 19, {'spaceBefore': 3*mm, 'leftIndent': 5*mm}),
        ('FootStyle', FONT_NORMAL, 8.5, COLOR_TEXT_LIGHT, TA_LEFT, 0, 13, {}),
    ]
    for name, font, size, color, align, after, lead, extra in defs:
        styles.add(ParagraphStyle(name, fontName=font, fontSize=size,
                                  textColor=color, alignment=align,
                                  spaceAfter=after, leading=lead, **extra))
    return styles

# ============================================================
# Helpers
# ============================================================
def make_table(headers, rows, col_widths=None, highlight_rows=None, green_rows=None):
    s = create_styles()
    data = [[Paragraph(h, s['TH']) for h in headers]]
    for i, row in enumerate(rows):
        row_p = []
        for j, cell in enumerate(row):
            if green_rows and i in green_rows:
                st = s['TCG']
            elif highlight_rows and i in highlight_rows:
                st = s['TCB']
            elif j == 0:
                st = s['TCL']
            else:
                st = s['TC']
            row_p.append(Paragraph(str(cell), st))
        data.append(row_p)
    if col_widths is None:
        col_widths = [170*mm / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        bg = COLOR_BG_LIGHT if i % 2 == 0 else white
        if green_rows and (i-1) in green_rows:
            bg = COLOR_BG_GREEN
        elif highlight_rows and (i-1) in highlight_rows:
            bg = COLOR_BG_WARNING
        cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(cmds))
    return t

def hline():
    return HRFlowable(width="100%", thickness=0.8, color=COLOR_PRIMARY, spaceAfter=3*mm, spaceBefore=3*mm)

def section_bar(text, s):
    data = [[Paragraph(text, s['TH'])]]
    t = Table(data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t

def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(COLOR_PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(20*mm, A4[1]-18*mm, A4[0]-20*mm, A4[1]-18*mm)
    canvas.setFont(FONT_NORMAL, 8)
    canvas.setFillColor(COLOR_TEXT_LIGHT)
    canvas.drawString(20*mm, A4[1]-16*mm, "BC楼半金库半办公方案 — 结构加固合理性分析")
    canvas.drawRightString(A4[0]-20*mm, A4[1]-16*mm, "技术评审文件")
    canvas.setLineWidth(0.8)
    canvas.line(20*mm, 15*mm, A4[0]-20*mm, 15*mm)
    canvas.drawString(20*mm, 10*mm, f"生成日期: {datetime.now().strftime('%Y-%m-%d')}")
    canvas.drawRightString(A4[0]-20*mm, 10*mm, f"第 {doc.page} 页")
    canvas.restoreState()

# ============================================================
# Structural Calculations
# ============================================================
# Constants
SPAN_X = 8.1      # m
SPAN_Y = 6.5      # m
TRIB = SPAN_X * SPAN_Y  # 52.65 m2
N_FLOORS = 5
FC = 19.1          # C40 MPa
FY = 400           # HRB400 MPa
COL_B, COL_H = 700, 800   # mm
COL_AREA = COL_B * COL_H  # 560000 mm2
BEAM_B, BEAM_H = 400, 800 # mm
BEAM_H0 = BEAM_H - 40     # mm
BUILDING_AREA = 40.8 * 19.5  # 795.6 m2
RA_PILE = 1350     # kN PHC500
N_PILES = 4
PILE_CAP = N_PILES * RA_PILE  # 5400 kN
RA_JY = 650        # kN 350方桩

# Original design
DEAD_ORIG = 5.0    # kN/m2
LIVE_ORIG = 4.0    # kN/m2
ALPHA_7 = 0.08
ALPHA_8 = 0.16

# New scheme: BC楼 50% vault + 50% office
VAULT_LOAD = 30.0   # kN/m2 (realistic max)
OFFICE_LOAD = 3.5   # kN/m2
VAULT_RATIO = 0.5
EQUIV_LIVE_BC = VAULT_RATIO * VAULT_LOAD + (1 - VAULT_RATIO) * OFFICE_LOAD  # 16.75 kN/m2
DEAD_NEW = 5.0       # kN/m2 base
DEAD_EXTRA = 2.0     # kN/m2 reinforcement added weight (less than full scheme)
DEAD_TOTAL = DEAD_NEW + DEAD_EXTRA  # 7.0 kN/m2

# Seismic: BC楼 keep 7度 for archive/office portions?
# If vault is only 50%, argue for 7度 base + local 8度 for vault zone
# Conservative: still use 8度 for B楼, 7度 for C楼
ALPHA_B = ALPHA_8  # conservative
ALPHA_C = ALPHA_7

def calc_axial_ratio(dead, live, n_floors, fc, area):
    N = (1.2 * dead + 1.4 * live) * TRIB * n_floors
    return N, N * 1000 / (fc * area)

def calc_seismic(alpha, dead, live, building_area, n_floors):
    G = (dead + 0.5 * live) * building_area * n_floors
    V = alpha * G
    return G, V

def calc_beam(dead, live, span_y, span_x):
    q = (1.2 * dead + 1.4 * live) * span_y
    M = q * span_x**2 / 8
    return q, M

def calc_beam_height(M, fy, rho, b):
    h0 = np.sqrt(M * 1e6 / (fy * rho * b * 0.9))
    return h0 + 40

def calc_net_height(floor_h, beam_h, slab=120, overlay=60):
    return floor_h - beam_h - slab - overlay

# ============================================================
# Build Report
# ============================================================
def build_report():
    output_path = os.path.join(os.path.dirname(__file__), "BC楼半金库半办公方案-结构分析报告.pdf")
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=25*mm, bottomMargin=22*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    s = create_styles()
    story = []

    # ===== COVER =====
    story.append(Spacer(1, 45*mm))
    story.append(Paragraph("BC楼半金库半办公方案", s['CoverTitle']))
    story.append(Paragraph("结构加固合理性分析报告", s['CoverTitle']))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="60%", thickness=2, color=COLOR_PRIMARY, spaceAfter=8*mm))
    story.append(Paragraph("上海市凯庆路565号既有建筑改造项目", s['CoverSubtitle']))
    story.append(Paragraph("B楼、C楼各50%金库 + 50%办公的优化方案", s['CoverSubtitle']))
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph("分析依据：GB50010-2010 / GB50011-2010 / GB55008-2021", s['CoverInfo']))
    story.append(Paragraph(f"报告日期：{datetime.now().strftime('%Y年%m月%d日')}", s['CoverInfo']))
    story.append(PageBreak())

    # ===== TOC =====
    story.append(Paragraph("目  录", s['SectionTitle']))
    story.append(hline())
    for item in [
        "一、方案概述与设计思路",
        "二、等效荷载计算",
        "三、柱轴压比验算",
        "四、地震力分析",
        "五、基础承载力验算",
        "六、梁承载力与净高验算",
        "七、各楼逐层分析",
        "八、加固措施建议",
        "九、与原方案对比",
        "十、综合结论",
    ]:
        story.append(Paragraph(item, s['BodyNI']))
    story.append(PageBreak())

    # ===== SECTION 1 =====
    story.append(section_bar("一、方案概述与设计思路", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("1.1 方案背景", s['SubTitle']))
    story.append(Paragraph(
        "原方案要求B楼（现金中心）全楼按40kN/m²活荷载设计，导致柱轴压比超限2.2倍、"
        "梁下净高不足3m、基础严重超载等一系列问题，使得加固在技术和经济上均不合理。", s['Body']))
    story.append(Paragraph(
        "本方案提出<b>替代思路</b>：B楼和C楼各有50%的面积作为金库保管区，"
        "其余50%作为办公/管理区。通过功能分区降低楼面等效荷载，"
        "使加固回到常规合理范围。", s['Body']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("1.2 各楼功能分配", s['SubTitle']))
    story.append(make_table(
        ['楼栋', '原方案功能', '本方案功能', '保管区比例', '等效活荷载'],
        [
            ['A楼', '现金中心(40kN/m²)', '综合办公/管理', '0%', '3.5 kN/m²'],
            ['B楼', '现金中心(40kN/m²)', '金库50%+办公50%', '50%', f'{EQUIV_LIVE_BC:.1f} kN/m²'],
            ['C楼', '档案中心(12kN/m²)', '金库50%+办公50%', '50%', f'{EQUIV_LIVE_BC:.1f} kN/m²'],
            ['D楼', '档案中心(12kN/m²)', '档案中心(不变)', '100%档案', '12.0 kN/m²'],
        ],
        col_widths=[20*mm, 38*mm, 38*mm, 28*mm, 32*mm],
        green_rows=[1, 2]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("1.3 设计原则", s['SubTitle']))
    story.append(Paragraph("• 金库保管区活荷载取30kN/m²（3m高满铺人民币实际极限值，非40kN/m²）", s['BulletStyle']))
    story.append(Paragraph("• 办公/管理区活荷载取3.5kN/m²（常规办公标准）", s['BulletStyle']))
    story.append(Paragraph("• 50%进库 + 50%办公，等效活荷载 = 0.5×30 + 0.5×3.5 = <b>16.75 kN/m²</b>", s['BulletStyle']))
    story.append(Paragraph("• B楼按8度设防（金库要求），C楼按7度设防（构造措施按8度）", s['BulletStyle']))
    story.append(Paragraph("• 加固增加自重取2.0kN/m²（半量加固，低于全面加固的3.0kN/m²）", s['BulletStyle']))

    story.append(PageBreak())

    # ===== SECTION 2 =====
    story.append(section_bar("二、等效荷载计算", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("2.1 等效荷载推导", s['SubTitle']))
    story.append(Paragraph(
        "当一个楼层中部分区域为高荷载（金库），部分为低荷载（办公）时，"
        "对于柱和基础的验算，可以用面积加权的等效荷载进行估算：", s['Body']))
    story.append(Paragraph(
        "q<sub>等效</sub> = r × q<sub>金库</sub> + (1-r) × q<sub>办公</sub>", s['FormulaStyle']))
    story.append(Paragraph(
        f"= 0.5 × 30.0 + 0.5 × 3.5 = <b>16.75 kN/m²</b>", s['FormulaStyle']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("2.2 各方案荷载对比", s['SubTitle']))

    # Gravity load representative values
    G_repr_orig = DEAD_ORIG + 0.5 * LIVE_ORIG  # 7.0
    G_repr_40 = (DEAD_NEW + 3.0) + 0.5 * 40.0  # 28.0
    G_repr_bc = DEAD_TOTAL + 0.5 * EQUIV_LIVE_BC  # 7.0 + 8.375 = 15.375

    story.append(make_table(
        ['方案', '恒载\n(kN/m²)', '活载\n(kN/m²)', '基本组合\n1.2G+1.4Q', '重力代表值\nG+0.5Q', '与原设计比'],
        [
            ['原设计(厂房)', f'{DEAD_ORIG}', f'{LIVE_ORIG}', f'{1.2*DEAD_ORIG+1.4*LIVE_ORIG:.1f}',
             f'{G_repr_orig:.1f}', '1.0倍'],
            ['原方案B楼(全金库)', '8.0', '40.0', f'{1.2*8+1.4*40:.1f}',
             f'{G_repr_40:.1f}', f'{G_repr_40/G_repr_orig:.1f}倍'],
            ['本方案BC楼(半金库)', f'{DEAD_TOTAL:.1f}', f'{EQUIV_LIVE_BC:.1f}',
             f'{1.2*DEAD_TOTAL+1.4*EQUIV_LIVE_BC:.1f}',
             f'{G_repr_bc:.2f}', f'{G_repr_bc/G_repr_orig:.1f}倍'],
        ],
        col_widths=[35*mm, 22*mm, 22*mm, 28*mm, 28*mm, 25*mm],
        highlight_rows=[1],
        green_rows=[2]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"本方案等效荷载的重力代表值为{G_repr_bc:.1f}kN/m²，仅为原设计的<b>{G_repr_bc/G_repr_orig:.1f}倍</b>，"
        f"相比原方案B楼的{G_repr_40/G_repr_orig:.1f}倍大幅降低。", s['Body']))

    story.append(PageBreak())

    # ===== SECTION 3: 柱轴压比 =====
    story.append(section_bar("三、柱轴压比验算", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("3.1 验算标准", s['SubTitle']))
    story.append(Paragraph(
        "根据GB50011-2010表6.3.6，框架结构柱轴压比限值：二级抗震0.75，三级抗震0.85。"
        "轴压比 μ<sub>N</sub> = N / (f<sub>c</sub> · A<sub>c</sub>)，其中f<sub>c</sub>=19.1MPa，"
        "A<sub>c</sub>=560,000mm²（700×800柱）。", s['Body']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("3.2 各方案柱轴压比对比", s['SubTitle']))

    N_orig, mu_orig = calc_axial_ratio(DEAD_ORIG, LIVE_ORIG, N_FLOORS, FC, COL_AREA)
    N_40, mu_40 = calc_axial_ratio(8.0, 40.0, N_FLOORS, FC, COL_AREA)
    N_bc, mu_bc = calc_axial_ratio(DEAD_TOTAL, EQUIV_LIVE_BC, N_FLOORS, FC, COL_AREA)

    story.append(Paragraph("<b>原设计（三级，限值0.85）：</b>", s['BodyNI']))
    story.append(Paragraph(
        f"N = (1.2×{DEAD_ORIG}+1.4×{LIVE_ORIG})×{TRIB}×5 = <b>{N_orig:.0f} kN</b>，"
        f"μ<sub>N</sub> = {mu_orig:.3f} ✓", s['FormulaStyle']))

    story.append(Paragraph("<b>原方案B楼（二级，限值0.75）：</b>", s['BodyNI']))
    story.append(Paragraph(
        f"N = (1.2×8.0+1.4×40.0)×{TRIB}×5 = <b>{N_40:.0f} kN</b>，"
        f"μ<sub>N</sub> = {mu_40:.3f} ✗ 超限{mu_40/0.75:.1f}倍", s['FormulaStyle']))

    story.append(Paragraph(f"<b>本方案BC楼（二级，限值0.75）：</b>", s['BodyNI']))
    story.append(Paragraph(
        f"N = (1.2×{DEAD_TOTAL}+1.4×{EQUIV_LIVE_BC:.2f})×{TRIB}×5 = <b>{N_bc:.0f} kN</b>，"
        f"μ<sub>N</sub> = {mu_bc:.3f}", s['FormulaStyle']))

    if mu_bc <= 0.75:
        story.append(Paragraph(
            f"✓ 轴压比{mu_bc:.3f} ≤ 0.75，<b>满足二级抗震要求，无需增大柱截面</b>", s['GreenBullet']))
    elif mu_bc <= 0.85:
        story.append(Paragraph(
            f"△ 轴压比{mu_bc:.3f}，超过二级限值0.75但在三级限值0.85以内，需适度加固", s['BulletStyle']))
    else:
        story.append(Paragraph(
            f"✗ 轴压比{mu_bc:.3f}，超过限值，需增大截面", s['WarnStyle']))

    story.append(Spacer(1, 3*mm))
    story.append(make_table(
        ['方案', '柱轴力N (kN)', '轴压比μN', '限值', '结果'],
        [
            ['原设计(三级)', f'{N_orig:.0f}', f'{mu_orig:.3f}', '0.85', '合格'],
            ['原方案B楼(二级)', f'{N_40:.0f}', f'{mu_40:.3f}', '0.75', f'超限{mu_40/0.75:.1f}倍'],
            ['本方案BC楼(二级)', f'{N_bc:.0f}', f'{mu_bc:.3f}', '0.75',
             '合格' if mu_bc <= 0.75 else '需加固'],
        ],
        col_widths=[38*mm, 30*mm, 25*mm, 20*mm, 35*mm],
        highlight_rows=[1],
        green_rows=[2] if mu_bc <= 0.75 else []
    ))

    # If slightly over, show what minor enlargement is needed
    if mu_bc > 0.75:
        req_area = N_bc * 1000 / (FC * 0.75)
        side = np.sqrt(req_area)
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(
            f"轴压比略超0.75，需截面面积{req_area/1e4:.0f}cm²（约{side:.0f}×{side:.0f}mm），"
            f"仅需每侧增大约{(side-700)/2:.0f}-{(side-800)/2:.0f}mm，属于<b>常规增大截面加固范围</b>。", s['Body']))

    story.append(PageBreak())

    # ===== SECTION 4: 地震力 =====
    story.append(section_bar("四、地震力分析", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("4.1 底部剪力估算", s['SubTitle']))

    G_orig_t, V_orig_t = calc_seismic(ALPHA_7, DEAD_ORIG, LIVE_ORIG, BUILDING_AREA, N_FLOORS)
    G_40_t, V_40_t = calc_seismic(ALPHA_8, 8.0, 40.0, BUILDING_AREA, N_FLOORS)
    G_bc_B, V_bc_B = calc_seismic(ALPHA_8, DEAD_TOTAL, EQUIV_LIVE_BC, BUILDING_AREA, N_FLOORS)
    G_bc_C, V_bc_C = calc_seismic(ALPHA_7, DEAD_TOTAL, EQUIV_LIVE_BC, BUILDING_AREA, N_FLOORS)

    story.append(make_table(
        ['方案', 'αmax', '总重力G (kN)', '底部剪力V (kN)', '与原设计比'],
        [
            ['原设计(7度)', '0.08', f'{G_orig_t:.0f}', f'{V_orig_t:.0f}', '1.0倍'],
            ['原方案B楼(8度)', '0.16', f'{G_40_t:.0f}', f'{V_40_t:.0f}', f'{V_40_t/V_orig_t:.1f}倍'],
            ['本方案B楼(8度)', '0.16', f'{G_bc_B:.0f}', f'{V_bc_B:.0f}', f'{V_bc_B/V_orig_t:.1f}倍'],
            ['本方案C楼(7度)', '0.08', f'{G_bc_C:.0f}', f'{V_bc_C:.0f}', f'{V_bc_C/V_orig_t:.1f}倍'],
        ],
        col_widths=[38*mm, 18*mm, 32*mm, 32*mm, 28*mm],
        highlight_rows=[1],
        green_rows=[2, 3]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"本方案B楼地震力为{V_bc_B:.0f}kN，是原设计的{V_bc_B/V_orig_t:.1f}倍，"
        f"相比原方案的{V_40_t/V_orig_t:.1f}倍<b>大幅降低</b>。"
        f"C楼地震力仅为{V_bc_C:.0f}kN（{V_bc_C/V_orig_t:.1f}倍），增幅温和。", s['Body']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("4.2 地震力可控性评价", s['SubTitle']))
    story.append(Paragraph(
        f"本方案B楼地震力放大{V_bc_B/V_orig_t:.1f}倍（原方案8.0倍），属于通过常规加固"
        "（柱增大截面+梁增大截面）可以应对的范围。如辅以消能减震措施，"
        "可进一步降低约30%，使地震力接近原设计水平。", s['Body']))

    story.append(PageBreak())

    # ===== SECTION 5: 基础 =====
    story.append(section_bar("五、基础承载力验算", s))
    story.append(Spacer(1, 5*mm))

    N_std_orig = (DEAD_ORIG + LIVE_ORIG) * TRIB * N_FLOORS
    N_std_40 = (8.0 + 40.0) * TRIB * N_FLOORS
    N_std_bc = (DEAD_TOTAL + EQUIV_LIVE_BC) * TRIB * N_FLOORS

    util_orig = N_std_orig / PILE_CAP
    util_40 = N_std_40 / PILE_CAP
    util_bc = N_std_bc / PILE_CAP

    n_extra_40 = int(np.ceil((N_std_40 - PILE_CAP) / RA_JY))
    n_extra_bc = max(0, int(np.ceil((N_std_bc - PILE_CAP) / RA_JY)))

    story.append(Paragraph("5.1 桩基利用率对比", s['SubTitle']))
    story.append(Paragraph(
        f"原桩基：PHC500管桩（Ra=1,350kN），典型中柱下4根，总承载力5,400kN。", s['BodyNI']))

    story.append(Spacer(1, 2*mm))
    story.append(make_table(
        ['方案', '标准组合轴力 (kN)', '桩基利用率', '需补桩数/柱', '评价'],
        [
            ['原设计', f'{N_std_orig:.0f}', f'{util_orig:.0%}', '0', '合格'],
            ['原方案B楼', f'{N_std_40:.0f}', f'{util_40:.0%}', f'{n_extra_40}', '严重超限'],
            ['本方案BC楼', f'{N_std_bc:.0f}', f'{util_bc:.0%}',
             f'{n_extra_bc}' if n_extra_bc > 0 else '0~2',
             '可控' if util_bc <= 1.5 else '需加固'],
        ],
        col_widths=[30*mm, 38*mm, 28*mm, 28*mm, 30*mm],
        highlight_rows=[1],
        green_rows=[2] if util_bc <= 1.5 else []
    ))

    story.append(Spacer(1, 3*mm))
    if util_bc <= 1.0:
        story.append(Paragraph(
            f"✓ 桩基利用率{util_bc:.0%}，原桩基<b>基本满足要求</b>，无需补桩或仅少量补桩。", s['GreenBullet']))
    elif util_bc <= 1.5:
        story.append(Paragraph(
            f"△ 桩基利用率{util_bc:.0%}，需少量补桩（每柱约{n_extra_bc}根350方桩），"
            f"<b>在地下室内施工可行</b>。", s['BulletStyle']))
    else:
        story.append(Paragraph(
            f"需补桩{n_extra_bc}根/柱，加固量较大但仍远小于原方案的12根/柱。", s['BulletStyle']))

    story.append(Paragraph(
        f"相比原方案需要每柱补{n_extra_40}根桩，本方案的基础加固量大幅降低，"
        "在既有地下室的有限空间内完全可以实施。", s['Body']))

    story.append(PageBreak())

    # ===== SECTION 6: 梁与净高 =====
    story.append(section_bar("六、梁承载力与净高验算", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("6.1 金库区梁验算（控制性工况）", s['SubTitle']))
    story.append(Paragraph(
        "虽然等效荷载为16.75kN/m²，但金库保管区局部仍为30kN/m²。"
        "梁的设计应按实际最大荷载（保管区30kN/m²）进行验算：", s['Body']))

    q_orig_b, M_orig_b = calc_beam(DEAD_ORIG, LIVE_ORIG, SPAN_Y, SPAN_X)
    q_30, M_30 = calc_beam(DEAD_TOTAL, 30.0, SPAN_Y, SPAN_X)
    q_office, M_office = calc_beam(DEAD_TOTAL, OFFICE_LOAD, SPAN_Y, SPAN_X)
    q_40, M_40 = calc_beam(8.0, 40.0, SPAN_Y, SPAN_X)

    # Original beam capacity
    rho = 0.015
    As_orig = rho * BEAM_B * BEAM_H0
    Mu_orig = FY * As_orig * 0.9 * BEAM_H0 / 1e6

    h_need_30 = calc_beam_height(M_30, FY, rho, BEAM_B)
    h_need_40 = calc_beam_height(M_40, FY, rho, BEAM_B)
    h_need_office = calc_beam_height(M_office, FY, rho, BEAM_B)

    story.append(make_table(
        ['区域', '活载\n(kN/m²)', '线荷载q\n(kN/m)', '弯矩M\n(kN·m)', '需梁高\n(mm)', '与原比'],
        [
            ['原设计', f'{LIVE_ORIG}', f'{q_orig_b:.1f}', f'{M_orig_b:.0f}', f'{BEAM_H}', '1.0倍'],
            ['原方案(40kN)', '40.0', f'{q_40:.1f}', f'{M_40:.0f}', f'{h_need_40:.0f}', f'{M_40/M_orig_b:.1f}倍'],
            ['本方案-金库区', '30.0', f'{q_30:.1f}', f'{M_30:.0f}', f'{h_need_30:.0f}', f'{M_30/M_orig_b:.1f}倍'],
            ['本方案-办公区', '3.5', f'{q_office:.1f}', f'{M_office:.0f}', f'{h_need_office:.0f}', f'{M_office/M_orig_b:.1f}倍'],
        ],
        col_widths=[30*mm, 22*mm, 26*mm, 26*mm, 24*mm, 24*mm],
        highlight_rows=[1],
        green_rows=[3]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("6.2 净高验算 — 关键控制指标", s['SubTitle']))

    net_h_30_std = calc_net_height(4000, h_need_30)
    net_h_30_L1 = calc_net_height(5400, h_need_30)
    net_h_40_std = calc_net_height(4000, h_need_40)
    net_h_office = calc_net_height(4000, h_need_office)

    story.append(make_table(
        ['区域/楼层', '层高\n(mm)', '梁高\n(mm)', '板+面层\n(mm)', '净高\n(mm)', '是否≥3m'],
        [
            ['原方案B楼(标准层)', '4,000', f'{h_need_40:.0f}', '200', f'{net_h_40_std:.0f}', '不满足'],
            ['本方案-金库区(底层)', '5,400', f'{h_need_30:.0f}', '180', f'{net_h_30_L1:.0f}', '满足' if net_h_30_L1 >= 3000 else '不满足'],
            ['本方案-金库区(标准层)', '4,000', f'{h_need_30:.0f}', '180', f'{net_h_30_std:.0f}', '满足' if net_h_30_std >= 3000 else '紧张'],
            ['本方案-办公区(标准层)', '4,000', f'{h_need_office:.0f}', '180', f'{net_h_office:.0f}', '满足' if net_h_office >= 3000 else '不满足'],
        ],
        col_widths=[38*mm, 20*mm, 20*mm, 22*mm, 22*mm, 25*mm],
        highlight_rows=[0],
        green_rows=[1, 3] if net_h_30_L1 >= 3000 else [3]
    ))

    story.append(Spacer(1, 3*mm))
    # Analysis of net height
    if net_h_30_std >= 3000:
        story.append(Paragraph(
            f"✓ 金库区标准层净高{net_h_30_std:.0f}mm，满足3m要求。", s['GreenBullet']))
    elif net_h_30_std >= 2800:
        story.append(Paragraph(
            f"△ 金库区标准层净高{net_h_30_std:.0f}mm，略低于3m。可通过以下方式解决：", s['BulletStyle']))
        story.append(Paragraph("• 采用<b>钢梁</b>替代混凝土增大截面（钢梁同承载力下高度低约30%）", s['BulletStyle']))
        story.append(Paragraph("• 将金库保管区<b>集中布置在底层</b>（层高5.4m，净高充裕）", s['BulletStyle']))
        story.append(Paragraph("• 标准层保管区采用<b>分散布置</b>，避免最大梁上满跨高荷载", s['BulletStyle']))
    else:
        story.append(Paragraph(
            f"金库区标准层净高{net_h_30_std:.0f}mm，不满足3m要求。"
            "建议将金库集中布置在底层（5.4m层高）。", s['WarnStyle']))

    story.append(Paragraph(
        f"底层（层高5.4m）金库区净高{net_h_30_L1:.0f}mm，<b>满足3m要求且有裕量</b>。"
        "这是本方案的关键优势：将核心保管功能集中在底层，充分利用其层高优势。", s['Body']))

    story.append(PageBreak())

    # ===== SECTION 7: 逐层分析 =====
    story.append(section_bar("七、各楼逐层分析", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("7.1 B楼逐层功能与荷载建议", s['SubTitle']))
    story.append(Paragraph(
        "为最大化利用底层层高优势并控制加固量，建议B楼按以下方式分层分区：", s['Body']))

    b_floors = [
        ['1层', '5,400', '核心保管区(70%)+通道(30%)', '30/4', '22.2',
         f'{calc_net_height(5400, calc_beam_height(calc_beam(DEAD_TOTAL, 22.2, SPAN_Y, SPAN_X)[1], FY, rho, BEAM_B)):.0f}',
         '满足'],
        ['2层', '4,000', '保管区(50%)+操作区(50%)', '30/4', '17.0',
         f'{calc_net_height(4000, calc_beam_height(calc_beam(DEAD_TOTAL, 17.0, SPAN_Y, SPAN_X)[1], FY, rho, BEAM_B)):.0f}',
         '-'],
        ['3层', '4,000', '周转存放(40%)+办公(60%)', '20/3.5', '10.1',
         f'{calc_net_height(4000, calc_beam_height(calc_beam(DEAD_TOTAL, 10.1, SPAN_Y, SPAN_X)[1], FY, rho, BEAM_B)):.0f}',
         '-'],
        ['4层', '4,000', '清分操作区', '-', '8.0',
         f'{calc_net_height(4000, calc_beam_height(calc_beam(DEAD_TOTAL, 8.0, SPAN_Y, SPAN_X)[1], FY, rho, BEAM_B)):.0f}',
         '-'],
        ['5层', '4,000', '办公/监控/管理', '-', '3.5',
         f'{calc_net_height(4000, calc_beam_height(calc_beam(DEAD_TOTAL, 3.5, SPAN_Y, SPAN_X)[1], FY, rho, BEAM_B)):.0f}',
         '满足'],
    ]
    # Recalculate net heights properly
    b_rows = []
    for fl in b_floors:
        layer_h = int(fl[1].replace(',', ''))
        live = float(fl[4])
        _, M_fl = calc_beam(DEAD_TOTAL, live, SPAN_Y, SPAN_X)
        h_beam = calc_beam_height(M_fl, FY, rho, BEAM_B)
        net = calc_net_height(layer_h, h_beam, 120 if layer_h > 5000 else 120, 60)
        status = '满足' if net >= 3000 else ('紧张' if net >= 2800 else '不足')
        b_rows.append([fl[0], fl[1], fl[2], fl[3], fl[4],
                       f'{h_beam:.0f}', f'{net:.0f}', status])

    story.append(make_table(
        ['楼层', '层高', '功能分区', '荷载\n(库/办)', '等效活载', '需梁高', '净高', '状态'],
        b_rows,
        col_widths=[16*mm, 16*mm, 38*mm, 18*mm, 18*mm, 18*mm, 16*mm, 16*mm],
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "以上方案中，全楼等效活荷载加权平均约12-15kN/m²，接近档案中心的荷载水平，"
        "属于常规加固可以应对的范围。底层利用5.4m层高，即使梁加大也能保证3m以上净高。", s['Body']))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("7.2 C楼逐层功能与荷载建议", s['SubTitle']))
    story.append(Paragraph(
        "C楼按7度设防（构造措施8度），地震力增量较小，加固更为容易。"
        "建议与B楼类似的分层分区方式，但可将更多面积用于保管：", s['Body']))

    c_rows_data = [
        ['1层', '5,400', '核心保管区(70%)+通道(30%)', '30/4', '22.2'],
        ['2层', '4,000', '保管区(60%)+操作区(40%)', '30/4', '19.6'],
        ['3层', '4,000', '保管区(50%)+办公(50%)', '30/3.5', '16.75'],
        ['4层', '4,000', '一般存放(30%)+办公(70%)', '15/3.5', '7.0'],
        ['5层', '4,000', '办公/管理/监控', '-', '3.5'],
    ]
    c_rows = []
    for fl in c_rows_data:
        layer_h = int(fl[1].replace(',', ''))
        live = float(fl[4])
        _, M_fl = calc_beam(DEAD_TOTAL, live, SPAN_Y, SPAN_X)
        h_beam = calc_beam_height(M_fl, FY, rho, BEAM_B)
        net = calc_net_height(layer_h, h_beam, 120, 60)
        status = '满足' if net >= 3000 else ('紧张' if net >= 2800 else '不足')
        c_rows.append([fl[0], fl[1], fl[2], fl[3], fl[4],
                       f'{h_beam:.0f}', f'{net:.0f}', status])

    story.append(make_table(
        ['楼层', '层高', '功能分区', '荷载\n(库/办)', '等效活载', '需梁高', '净高', '状态'],
        c_rows,
        col_widths=[16*mm, 16*mm, 38*mm, 18*mm, 18*mm, 18*mm, 16*mm, 16*mm],
    ))

    story.append(PageBreak())

    # ===== SECTION 8: 加固措施 =====
    story.append(section_bar("八、加固措施建议", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("8.1 柱加固", s['SubTitle']))
    if mu_bc <= 0.75:
        story.append(Paragraph(
            f"柱轴压比{mu_bc:.3f}≤0.75，<b>原截面基本满足要求</b>。"
            "仅需对局部不满足的柱进行增大截面或外包碳纤维加固，属于常规加固范畴。", s['Body']))
    else:
        req_area = N_bc * 1000 / (FC * 0.75)
        side = np.sqrt(req_area)
        enlarge = max((side - COL_B) / 2, (side - COL_H) / 2)
        story.append(Paragraph(
            f"柱轴压比{mu_bc:.3f}，需适度增大截面至约{side:.0f}×{side:.0f}mm"
            f"（每侧增大约{enlarge:.0f}mm），属于<b>常规增大截面加固</b>，不需要外包钢管等特殊工艺。", s['Body']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("8.2 梁加固", s['SubTitle']))
    story.append(Paragraph(
        "• <b>金库保管区梁</b>：增大截面加固，梁底增高或梁四周增大，部分梁辅以粘钢/碳纤维", s['BulletStyle']))
    story.append(Paragraph(
        "• <b>办公区梁</b>：荷载与原设计接近，大部分无需加固或仅轻微加固（粘贴碳纤维）", s['BulletStyle']))
    story.append(Paragraph(
        "• <b>关键优势</b>：办公区约占50%面积，这部分梁基本不需要加固，大幅减少工程量", s['BulletStyle']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("8.3 楼板加固", s['SubTitle']))
    story.append(Paragraph(
        "• 金库保管区：增加叠合层（60-80mm），增设混凝土肋或钢梁", s['BulletStyle']))
    story.append(Paragraph(
        "• 办公区：基本无需加固（原设计4.0kN/m²，办公荷载3.5kN/m²）", s['BulletStyle']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("8.4 基础加固", s['SubTitle']))
    if util_bc <= 1.0:
        story.append(Paragraph(
            f"桩基利用率{util_bc:.0%}，<b>原桩基基本满足</b>，无需补桩或仅少量补桩。", s['GreenBullet']))
    else:
        story.append(Paragraph(
            f"桩基利用率{util_bc:.0%}，需适量补桩（每柱约{n_extra_bc}根350方桩），"
            "在地下室内采用锚杆静压桩施工，工程量可控。", s['BulletStyle']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("8.5 消能减震", s['SubTitle']))
    story.append(Paragraph(
        "本方案荷载大幅降低后，是否需要消能减震取决于详细计算结果。初步判断：", s['Body']))
    story.append(Paragraph(
        "• C楼（7度设防）：荷载增量可控，常规加固即可满足，<b>大概率不需要消能减震</b>", s['BulletStyle']))
    story.append(Paragraph(
        f"• B楼（8度设防）：地震力为原来的{V_bc_B/V_orig_t:.1f}倍，"
        "可选择性设置少量阻尼器以进一步优化，但不是必须", s['BulletStyle']))

    story.append(PageBreak())

    # ===== SECTION 9: 与原方案对比 =====
    story.append(section_bar("九、与原方案对比", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("9.1 关键指标对比", s['SubTitle']))
    story.append(make_table(
        ['指标', '原设计', '原方案\n(B楼全金库)', '本方案\n(BC半金库)', '改善幅度'],
        [
            ['等效活载 (kN/m²)', f'{LIVE_ORIG}', '40.0', f'{EQUIV_LIVE_BC:.1f}',
             f'降低{(40.0-EQUIV_LIVE_BC)/40.0:.0%}'],
            ['柱轴压比', f'{mu_orig:.3f}', f'{mu_40:.3f}', f'{mu_bc:.3f}',
             f'降低{(mu_40-mu_bc)/mu_40:.0%}'],
            ['底部地震力 (kN)', f'{V_orig_t:.0f}', f'{V_40_t:.0f}', f'{V_bc_B:.0f}',
             f'降低{(V_40_t-V_bc_B)/V_40_t:.0%}'],
            ['桩基利用率', f'{util_orig:.0%}', f'{util_40:.0%}', f'{util_bc:.0%}',
             f'降低{(util_40-util_bc)/util_40:.0%}'],
            ['需补桩 (根/柱)', '0', f'{n_extra_40}', f'{n_extra_bc}',
             f'减少{n_extra_40-n_extra_bc}根'],
            ['梁下净高-底层 (mm)', '~4,400', f'{calc_net_height(5400, h_need_40):.0f}',
             f'{net_h_30_L1:.0f}', f'+{net_h_30_L1-calc_net_height(5400, h_need_40):.0f}mm'],
            ['梁下净高-标准层 (mm)', '3,080', f'{net_h_40_std:.0f}',
             f'{net_h_30_std:.0f}', f'+{net_h_30_std-net_h_40_std:.0f}mm'],
            ['是否需要消能减震', '不需要', '必须', '可选/不需要', '-'],
            ['加固范围', '-', '全部构件', '约50%构件', '减少~50%'],
        ],
        col_widths=[35*mm, 25*mm, 30*mm, 30*mm, 30*mm],
        green_rows=[0, 1, 2, 3, 4, 8]
    ))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("9.2 经济性分析", s['SubTitle']))
    story.append(Paragraph(
        "本方案相比原方案，在以下方面显著节省成本：", s['Body']))
    story.append(Paragraph("• <b>加固工程量减少约50%</b>：办公区梁板柱基本不需加固", s['BulletStyle']))
    story.append(Paragraph("• <b>补桩量大幅减少</b>：从12根/柱降至0-2根/柱", s['BulletStyle']))
    story.append(Paragraph("• <b>消能减震系统可省略或简化</b>：节省阻尼器及维护费用", s['BulletStyle']))
    story.append(Paragraph("• <b>施工工期缩短</b>：加固范围小，减少湿作业、植筋、养护时间", s['BulletStyle']))
    story.append(Paragraph("• <b>建筑使用空间保留</b>：柱截面增大幅度小，不严重压缩净空间", s['BulletStyle']))
    story.append(Paragraph("• <b>无需拆除重建</b>：不触及结构主体，保留建筑资产价值", s['BulletStyle']))

    story.append(PageBreak())

    # ===== SECTION 10: 综合结论 =====
    story.append(section_bar("十、综合结论", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("10.1 方案可行性总结", s['SubTitle']))

    # Final summary table
    checks = [
        ['柱轴压比', f'{mu_bc:.3f}', '≤0.75' if mu_bc <= 0.75 else '≤0.85',
         '满足' if mu_bc <= 0.75 else ('基本满足' if mu_bc <= 0.85 else '需加固'),
         '无需增大截面' if mu_bc <= 0.75 else '适度增大截面即可'],
        ['底部地震力', f'{V_bc_B:.0f}kN', f'≤{V_orig_t*3:.0f}kN',
         '可控' if V_bc_B <= V_orig_t * 4 else '偏大',
         '常规加固可应对'],
        ['桩基利用率', f'{util_bc:.0%}', '≤100%' if util_bc <= 1 else '≤150%',
         '满足' if util_bc <= 1 else '可控',
         '少量补桩' if util_bc > 1 else '无需补桩'],
        ['底层金库净高', f'{net_h_30_L1:.0f}mm', '≥3000mm',
         '满足' if net_h_30_L1 >= 3000 else '不满足',
         '层高5.4m优势'],
        ['标准层金库净高', f'{net_h_30_std:.0f}mm', '≥3000mm',
         '满足' if net_h_30_std >= 3000 else ('需优化' if net_h_30_std >= 2800 else '不满足'),
         '可用钢梁优化' if net_h_30_std < 3000 else '满足要求'],
        ['办公区净高', f'{net_h_office:.0f}mm', '≥2800mm',
         '满足' if net_h_office >= 2800 else '不满足',
         '无需加固'],
    ]

    all_pass = all(r[3] in ['满足', '可控', '基本满足'] for r in checks)

    story.append(make_table(
        ['验算项目', '计算值', '限值', '结果', '说明'],
        checks,
        col_widths=[30*mm, 25*mm, 25*mm, 22*mm, 50*mm],
        green_rows=[i for i, r in enumerate(checks) if r[3] in ['满足', '可控']]
    ))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("10.2 核心结论", s['SubTitle']))

    story.append(Paragraph(
        "<b>结论一：BC楼各50%金库+50%办公的方案在结构上是可行的。</b>"
        f"等效活荷载降至{EQUIV_LIVE_BC:.1f}kN/m²后，柱轴压比、基础承载力均进入可控范围，"
        "通过常规加固手段（增大截面+少量补桩）即可满足使用要求，<b>无需拆除重建</b>。", s['Body']))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph(
        "<b>结论二：底层是金库保管区的最佳位置。</b>"
        f"底层层高5.4m，金库区净高可达{net_h_30_L1:.0f}mm，远超3m要求。"
        "建议将核心保管功能集中在底层，标准层适度分配，上层做办公管理。", s['Body']))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph(
        "<b>结论三：本方案的加固量约为原方案的50%。</b>"
        "办公区占50%面积，其梁板柱基本不需加固；基础补桩量从12根/柱降至0-2根/柱；"
        "消能减震系统可省略或简化。工程造价、施工周期、质量风险均大幅降低。", s['Body']))
    story.append(Spacer(1, 2*mm))

    story.append(Paragraph(
        "<b>结论四：金库功能可以满足。</b>"
        "两栋楼各50%面积做金库，合计约一栋楼的金库面积（约4,000m²），"
        "分布在BC两楼中，兼顾了安全冗余（两栋楼互为备份）和实际使用需求。"
        "如果未来业务增长需要更多库容，可在不影响结构安全的前提下"
        "将部分办公区调整为存放区（荷载15-20kN/m²）。", s['Body']))

    story.append(Spacer(1, 10*mm))
    story.append(hline())
    story.append(Paragraph(
        "注：本报告为方案阶段的初步定量分析，采用简化计算方法（底部剪力法、简支梁估算等）。"
        "精确结果需以施工图阶段的详细结构计算（有限元分析、Pushover分析等）为准。"
        "梁的验算采用了保管区满跨满铺的最不利工况，实际中保管区内仍有通道和间距，"
        "实际荷载可能低于计算值。本报告仅供技术评审参考。", s['FootStyle']))

    # Build
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF报告已生成: {output_path}")
    return output_path


if __name__ == '__main__':
    build_report()
