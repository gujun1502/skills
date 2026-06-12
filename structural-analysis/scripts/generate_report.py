# -*- coding: utf-8 -*-
"""
结构加固方案合理性分析报告 - PDF生成
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check and install reportlab if needed
try:
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
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'reportlab'])
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

import numpy as np
from datetime import datetime

# ============================================================
# Font Registration
# ============================================================
def register_fonts():
    """Register Chinese fonts."""
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

    # Determine which fonts to use
    if "Microsoft YaHei" in registered:
        return "Microsoft YaHei", registered.get("Microsoft YaHei Bold", False) and "Microsoft YaHei Bold" or "Microsoft YaHei"
    elif "SimSun" in registered:
        return "SimSun", registered.get("SimHei", False) and "SimHei" or "SimSun"
    else:
        return "Helvetica", "Helvetica-Bold"

FONT_NORMAL, FONT_BOLD = register_fonts()

# ============================================================
# Color Scheme
# ============================================================
COLOR_PRIMARY = HexColor('#1a365d')      # Dark blue
COLOR_SECONDARY = HexColor('#2c5282')    # Medium blue
COLOR_ACCENT = HexColor('#c53030')       # Red for warnings
COLOR_BG_HEADER = HexColor('#e2e8f0')    # Light gray-blue
COLOR_BG_LIGHT = HexColor('#f7fafc')     # Very light
COLOR_BG_WARNING = HexColor('#fff5f5')   # Light red
COLOR_TEXT = HexColor('#1a202c')         # Dark text
COLOR_TEXT_LIGHT = HexColor('#4a5568')   # Gray text
COLOR_GREEN = HexColor('#276749')
COLOR_ORANGE = HexColor('#c05621')

# ============================================================
# Styles
# ============================================================
def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CoverTitle', fontName=FONT_BOLD, fontSize=26,
        textColor=COLOR_PRIMARY, alignment=TA_CENTER,
        spaceAfter=8*mm, leading=36
    ))
    styles.add(ParagraphStyle(
        'CoverSubtitle', fontName=FONT_NORMAL, fontSize=14,
        textColor=COLOR_SECONDARY, alignment=TA_CENTER,
        spaceAfter=4*mm, leading=22
    ))
    styles.add(ParagraphStyle(
        'CoverInfo', fontName=FONT_NORMAL, fontSize=11,
        textColor=COLOR_TEXT_LIGHT, alignment=TA_CENTER,
        spaceAfter=3*mm, leading=18
    ))
    styles.add(ParagraphStyle(
        'SectionTitle', fontName=FONT_BOLD, fontSize=16,
        textColor=COLOR_PRIMARY, spaceBefore=10*mm, spaceAfter=5*mm,
        leading=24, borderWidth=0, borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        'SubsectionTitle', fontName=FONT_BOLD, fontSize=13,
        textColor=COLOR_SECONDARY, spaceBefore=6*mm, spaceAfter=3*mm,
        leading=20,
    ))
    styles.add(ParagraphStyle(
        'BodyText_CN', fontName=FONT_NORMAL, fontSize=10.5,
        textColor=COLOR_TEXT, alignment=TA_JUSTIFY,
        spaceAfter=2.5*mm, leading=18, firstLineIndent=21,
    ))
    styles.add(ParagraphStyle(
        'BodyText_NI', fontName=FONT_NORMAL, fontSize=10.5,
        textColor=COLOR_TEXT, alignment=TA_JUSTIFY,
        spaceAfter=2.5*mm, leading=18, firstLineIndent=0,
    ))
    styles.add(ParagraphStyle(
        'Formula', fontName=FONT_NORMAL, fontSize=10.5,
        textColor=COLOR_TEXT, alignment=TA_CENTER,
        spaceAfter=3*mm, spaceBefore=2*mm, leading=18,
    ))
    styles.add(ParagraphStyle(
        'Warning', fontName=FONT_BOLD, fontSize=11,
        textColor=COLOR_ACCENT, spaceBefore=3*mm, spaceAfter=2*mm,
        leading=18, leftIndent=10*mm,
    ))
    styles.add(ParagraphStyle(
        'BulletItem', fontName=FONT_NORMAL, fontSize=10.5,
        textColor=COLOR_TEXT, spaceAfter=1.5*mm, leading=17,
        leftIndent=8*mm, firstLineIndent=-4*mm,
    ))
    styles.add(ParagraphStyle(
        'TableHeader', fontName=FONT_BOLD, fontSize=9.5,
        textColor=white, alignment=TA_CENTER, leading=14,
    ))
    styles.add(ParagraphStyle(
        'TableCell', fontName=FONT_NORMAL, fontSize=9.5,
        textColor=COLOR_TEXT, alignment=TA_CENTER, leading=14,
    ))
    styles.add(ParagraphStyle(
        'TableCellLeft', fontName=FONT_NORMAL, fontSize=9.5,
        textColor=COLOR_TEXT, alignment=TA_LEFT, leading=14,
    ))
    styles.add(ParagraphStyle(
        'TableCellBold', fontName=FONT_BOLD, fontSize=9.5,
        textColor=COLOR_ACCENT, alignment=TA_CENTER, leading=14,
    ))
    styles.add(ParagraphStyle(
        'Conclusion', fontName=FONT_BOLD, fontSize=11,
        textColor=COLOR_PRIMARY, spaceBefore=3*mm, spaceAfter=2*mm,
        leading=19, leftIndent=5*mm,
    ))
    styles.add(ParagraphStyle(
        'FootNote', fontName=FONT_NORMAL, fontSize=8.5,
        textColor=COLOR_TEXT_LIGHT, leading=13,
    ))
    return styles


# ============================================================
# Helper Functions
# ============================================================
def make_table(headers, rows, col_widths=None, highlight_rows=None):
    """Create a styled table."""
    s = create_styles()
    header_paras = [Paragraph(h, s['TableHeader']) for h in headers]
    data = [header_paras]
    for i, row in enumerate(rows):
        row_paras = []
        for j, cell in enumerate(row):
            if highlight_rows and i in highlight_rows:
                style = s['TableCellBold']
            elif j == 0:
                style = s['TableCellLeft']
            else:
                style = s['TableCell']
            row_paras.append(Paragraph(str(cell), style))
        data.append(row_paras)

    if col_widths is None:
        col_widths = [170*mm / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
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
        if highlight_rows and (i - 1) in highlight_rows:
            bg = COLOR_BG_WARNING
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style_cmds))
    return t


def horizontal_line():
    return HRFlowable(width="100%", thickness=0.8, color=COLOR_PRIMARY, spaceAfter=3*mm, spaceBefore=3*mm)


def section_bar(text, styles):
    """Create a colored section header bar."""
    data = [[Paragraph(text, styles['TableHeader'])]]
    t = Table(data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


# ============================================================
# Page Template
# ============================================================
def header_footer(canvas, doc):
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(COLOR_PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.line(20*mm, A4[1] - 18*mm, A4[0] - 20*mm, A4[1] - 18*mm)
    canvas.setFont(FONT_NORMAL, 8)
    canvas.setFillColor(COLOR_TEXT_LIGHT)
    canvas.drawString(20*mm, A4[1] - 16*mm, "结构加固方案合理性分析报告")
    canvas.drawRightString(A4[0] - 20*mm, A4[1] - 16*mm, "技术评审文件")

    # Footer
    canvas.setStrokeColor(COLOR_PRIMARY)
    canvas.setLineWidth(0.8)
    canvas.line(20*mm, 15*mm, A4[0] - 20*mm, 15*mm)
    canvas.setFont(FONT_NORMAL, 8)
    canvas.setFillColor(COLOR_TEXT_LIGHT)
    canvas.drawString(20*mm, 10*mm, f"生成日期: {datetime.now().strftime('%Y-%m-%d')}")
    canvas.drawRightString(A4[0] - 20*mm, 10*mm, f"第 {doc.page} 页")
    canvas.restoreState()


# ============================================================
# Build Report
# ============================================================
def build_report():
    output_path = os.path.join(os.path.dirname(__file__), "结构加固方案合理性分析报告.pdf")
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=25*mm, bottomMargin=22*mm,
        leftMargin=20*mm, rightMargin=20*mm
    )
    s = create_styles()
    story = []

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 50*mm))
    story.append(Paragraph("结构加固方案合理性分析报告", s['CoverTitle']))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="60%", thickness=2, color=COLOR_PRIMARY, spaceAfter=8*mm))
    story.append(Paragraph("上海市凯庆路565号既有建筑改造项目", s['CoverSubtitle']))
    story.append(Paragraph("丙类厂房 → 银行现金中心 / 档案中心", s['CoverSubtitle']))
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("分析依据：GB50010-2010 / GB50011-2010 / GB55008-2021", s['CoverInfo']))
    story.append(Paragraph("GB55021-2021 / DGJ08-81-2021 / GA38-2021", s['CoverInfo']))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(f"报告日期：{datetime.now().strftime('%Y年%m月%d日')}", s['CoverInfo']))
    story.append(PageBreak())

    # ========== TOC ==========
    story.append(Paragraph("目  录", s['SectionTitle']))
    story.append(horizontal_line())
    toc_items = [
        "一、项目概况与改造背景",
        "二、两方案对比分析",
        "三、荷载对比与定量计算",
        "四、柱轴压比验算",
        "五、地震力对比分析",
        "六、基础承载力验算",
        "七、梁承载力与净高验算",
        "八、应力滞后效应分析",
        "九、消能减震技术局限性分析",
        "十、需求合理性质疑",
        "十一、分区进库方案 — 降低荷载实现合理加固",
        "十二、综合结论与建议",
    ]
    for item in toc_items:
        story.append(Paragraph(item, s['BodyText_NI']))
    story.append(PageBreak())

    # ========== SECTION 1: 项目概况 ==========
    story.append(section_bar("一、项目概况与改造背景", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("1.1 建筑现状", s['SubsectionTitle']))
    story.append(Paragraph(
        "本项目位于上海市凯庆路565号地块，原项目为上海张江东区现代医疗器械产业园14号地块新建项目的子项"
        "3#、4#、5#、6#楼及地下室2，竣工图编制时间为2017年12月29日。", s['BodyText_CN']))
    story.append(Paragraph(
        "四幢建筑物总建筑面积23,182.32平方米，地上建筑面积17,145.4平方米，地下建筑面积6,036.92平方米。"
        "建筑限高24米，4幢建筑物均为5层框架结构，底层层高5.4米，2至5层层高4.0米。", s['BodyText_CN']))
    story.append(Paragraph(
        "原建筑功能为<b>丙类辅助生产厂房（通用厂房）</b>，楼面使用荷载仅为<b>4.0kN/m²</b>，"
        "抗震设防烈度7度，抗震设防类别为标准设防，抗震等级三级。", s['BodyText_CN']))

    # 原结构参数表
    story.append(Spacer(1, 3*mm))
    story.append(make_table(
        ['参数项', '数值', '备注'],
        [
            ['结构形式', '钢筋混凝土框架', '柱网8.1×6.5m'],
            ['层数/总高', '5层 / 21.4m', '层高5.4/4.0/4.0/4.0/4.0m'],
            ['楼面活荷载', '4.0 kN/m²', '丙类通用厂房标准'],
            ['混凝土强度', 'C40 (fc=19.1MPa)', '基础C35'],
            ['钢筋', 'HRB400 (fy=400MPa)', ''],
            ['典型柱截面', '700×800mm (底层中柱)', '另有700×700, 600×600, 500×500'],
            ['基础形式', 'PHC500管桩+防水板', 'Ra=1350kN'],
            ['抗震设防', '7度 / 标准设防 / 三级', 'αmax=0.08'],
        ],
        col_widths=[45*mm, 55*mm, 70*mm]
    ))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("1.2 改造目标", s['SubsectionTitle']))
    story.append(Paragraph(
        "本次改造拟将4栋厂房分别改建为银行现金中心和档案中心库：", s['BodyText_CN']))
    story.append(Paragraph("• A楼、B楼 → <b>现金中心（金库）</b>：活荷载标准值不低于40kN/m²，"
                           "抗震设防烈度按8度设计", s['BulletItem']))
    story.append(Paragraph("• C楼、D楼 → <b>档案中心库</b>：活荷载标准值不小于12kN/m²，"
                           "构造措施按8度采取", s['BulletItem']))
    story.append(Paragraph(
        "这意味着B楼的楼面活荷载将从4.0kN/m²提高到40.0kN/m²（<b>增加10倍</b>），"
        "同时抗震设防烈度从7度提高到8度（水平地震影响系数从0.08提高到0.16，<b>翻倍</b>）。"
        "这两者的叠加效应使得地震力放大约为原来的<b>8倍</b>。", s['BodyText_CN']))

    story.append(PageBreak())

    # ========== SECTION 2: 两方案对比 ==========
    story.append(section_bar("二、两方案对比分析", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("2.1 方案一：B楼与C楼对调", s['SubsectionTitle']))
    story.append(Paragraph(
        "方案一对四栋楼均采用加固方案，B楼（现金中心）采用以下加固措施：", s['BodyText_CN']))
    story.append(Paragraph("• 中柱采用<b>外包钢管加固</b>，避免增大截面到1200×1200mm占用过多空间", s['BulletItem']))
    story.append(Paragraph("• 边柱增设<b>翼墙</b>，通过翼墙调整内力分配，控制轴压比", s['BulletItem']))
    story.append(Paragraph("• 全楼各层设置<b>消能减震装置</b>（砌体支墩+阻尼器），降低地震响应", s['BulletItem']))
    story.append(Paragraph("• 基础采用<b>底板加厚+锚杆静压桩</b>加固", s['BulletItem']))
    story.append(Paragraph("• 梁板采用<b>增大截面</b>加固", s['BulletItem']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("2.2 方案二：B楼保留原外立面", s['SubsectionTitle']))
    story.append(Paragraph(
        "方案二认识到B楼全面加固的不可行性，提出了不同的处理方式：", s['BodyText_CN']))
    story.append(Paragraph("• B楼：±0.00以上<b>仅保留外立面框架并加固，内部全部拆除重建</b>", s['BulletItem']))
    story.append(Paragraph("• A、C、D楼：与方案一类似，采用加固+消能减震方案", s['BulletItem']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "方案二在第16页明确承认了以下关键问题（原文摘录）：", s['BodyText_CN']))
    story.append(Paragraph(
        "<i>\"承载力缺口均超过100%，已超出常规加固的合理范围，几乎所有构件都需'脱胎换骨'式的改造\"</i>",
        s['Warning']))
    story.append(Paragraph(
        "<i>\"10倍于原结构的活荷载会极大加剧被加固构件二次受力的应力滞后效应，导致加固后构件的实际承载力远低于理论计算值\"</i>",
        s['Warning']))
    story.append(Paragraph(
        "<i>\"节点区加固完成后，无法通过常规手段检测新旧混凝土结合质量\"</i>",
        s['Warning']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("2.3 两方案的核心矛盾", s['SubsectionTitle']))
    story.append(Paragraph(
        "方案二已经对B楼得出了\"全面加固不可行\"的结论而改为拆内重建，但A楼同样是40kN/m²的现金中心，"
        "却仍然采用加固方案——<b>逻辑不自洽</b>。如果B楼的加固\"超出常规加固合理范围\"，"
        "那么荷载需求完全相同的A楼为何就在合理范围内？", s['BodyText_CN']))

    story.append(PageBreak())

    # ========== SECTION 3: 荷载计算 ==========
    story.append(section_bar("三、荷载对比与定量计算", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("3.1 计算参数", s['SubsectionTitle']))
    story.append(Paragraph(
        "以典型底层中柱为分析对象，柱网8.1×6.5m，单柱负荷面积52.65m²。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("3.2 重力荷载代表值对比", s['SubsectionTitle']))
    story.append(Paragraph(
        "按《建筑抗震设计规范》GB50011-2010，重力荷载代表值取恒载标准值+0.5×活荷载标准值：", s['BodyText_CN']))
    story.append(Paragraph("原设计：G<sub>rep</sub> = 5.0 + 0.5×4.0 = <b>7.0 kN/m²</b>", s['Formula']))
    story.append(Paragraph("B楼改造后：G<sub>rep</sub> = 8.0 + 0.5×40.0 = <b>28.0 kN/m²</b>（含加固增重3.0kN/m²）", s['Formula']))
    story.append(Paragraph("C/D楼改造后：G<sub>rep</sub> = 8.0 + 0.5×12.0 = <b>14.0 kN/m²</b>", s['Formula']))

    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "B楼重力荷载代表值为原设计的<b>4.0倍</b>，C/D楼为<b>2.0倍</b>。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("3.3 荷载基本组合", s['SubsectionTitle']))
    story.append(Paragraph(
        "按GB50009-2012荷载规范，基本组合取1.2G+1.4Q：", s['BodyText_CN']))

    story.append(make_table(
        ['项目', '原设计', 'B楼改造后', 'C/D楼改造后'],
        [
            ['恒载标准值 (kN/m²)', '5.0', '8.0', '8.0'],
            ['活载标准值 (kN/m²)', '4.0', '40.0', '12.0'],
            ['组合值 1.2G+1.4Q (kN/m²)', '11.6', '65.6', '26.4'],
            ['底层中柱5层总轴力 (kN)', '3,054', '17,269', '6,950'],
            ['与原设计比值', '1.0', '5.7倍', '2.3倍'],
        ],
        col_widths=[50*mm, 35*mm, 45*mm, 40*mm],
        highlight_rows=[3, 4]
    ))

    story.append(PageBreak())

    # ========== SECTION 4: 柱轴压比 ==========
    story.append(section_bar("四、柱轴压比验算", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("4.1 验算原理", s['SubsectionTitle']))
    story.append(Paragraph(
        "轴压比是评价框架柱抗震性能的关键指标，定义为柱组合轴力设计值N与柱全截面面积A<sub>c</sub>"
        "和混凝土轴心抗压强度设计值f<sub>c</sub>的乘积之比：", s['BodyText_CN']))
    story.append(Paragraph("μ<sub>N</sub> = N / (f<sub>c</sub> · A<sub>c</sub>)", s['Formula']))
    story.append(Paragraph(
        "根据GB50011-2010表6.3.6，框架结构柱轴压比限值为：二级抗震<b>0.75</b>，三级抗震<b>0.85</b>。"
        "轴压比超限意味着柱的延性不足，在地震中可能发生脆性破坏。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("4.2 计算过程", s['SubsectionTitle']))
    story.append(Paragraph("典型底层中柱截面：700×800mm，A<sub>c</sub> = 560,000 mm²", s['BodyText_NI']))
    story.append(Paragraph("混凝土强度：C40，f<sub>c</sub> = 19.1 MPa", s['BodyText_NI']))
    story.append(Spacer(1, 2*mm))

    # 原设计
    N_orig = 3054
    axial_orig = N_orig * 1000 / (19.1 * 560000)
    story.append(Paragraph(f"<b>原设计（三级抗震，限值0.85）：</b>", s['BodyText_NI']))
    story.append(Paragraph(
        f"μ<sub>N</sub> = {N_orig}×10³ / (19.1 × 560,000) = <b>{axial_orig:.3f}</b> &lt; 0.85 ✓ 合格", s['Formula']))

    # B楼
    N_B = 17269
    axial_B = N_B * 1000 / (19.1 * 560000)
    story.append(Paragraph(f"<b>B楼改造后（二级抗震，限值0.75）：</b>", s['BodyText_NI']))
    story.append(Paragraph(
        f"μ<sub>N</sub> = {N_B}×10³ / (19.1 × 560,000) = <b>{axial_B:.3f}</b> &gt; 0.75 ✗ 超限{axial_B/0.75:.1f}倍！", s['Formula']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("4.3 满足轴压比所需截面", s['SubsectionTitle']))
    req_area = N_B * 1000 / (19.1 * 0.75)
    side = np.sqrt(req_area)
    story.append(Paragraph(
        f"要满足0.75的轴压比限值，所需柱截面面积为：", s['BodyText_CN']))
    story.append(Paragraph(
        f"A<sub>需</sub> = N/(f<sub>c</sub>·μ<sub>限</sub>) = {N_B}×10³ / (19.1×0.75) = <b>{req_area/1e4:.0f} cm²</b> "
        f"(约{side:.0f}×{side:.0f}mm)", s['Formula']))
    story.append(Paragraph(
        f"即需要将原截面（700×800mm = 56 cm²×100）扩大到约<b>{req_area/560000:.1f}倍</b>。"
        f"方案文件提到的1200×1200mm截面（144 cm²×100），轴压比为"
        f"{N_B*1000/(19.1*1440000):.3f}，勉强满足要求，但每侧需增大200-250mm，"
        f"严重压缩建筑使用空间。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(make_table(
        ['验算情况', '轴力N (kN)', '截面 (mm)', '轴压比μN', '限值', '结果'],
        [
            ['原设计(三级)', '3,054', '700×800', f'{axial_orig:.3f}', '0.85', '合格'],
            ['B楼原截面(二级)', '17,269', '700×800', f'{axial_B:.3f}', '0.75', '超限2.2倍'],
            ['B楼增大截面(二级)', '17,269', '1200×1200', f'{N_B*1000/(19.1*1440000):.3f}', '0.75', '勉强合格'],
        ],
        col_widths=[35*mm, 25*mm, 28*mm, 25*mm, 18*mm, 30*mm],
        highlight_rows=[1]
    ))

    story.append(PageBreak())

    # ========== SECTION 5: 地震力 ==========
    story.append(section_bar("五、地震力对比分析", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("5.1 底部剪力法估算", s['SubsectionTitle']))
    story.append(Paragraph(
        "采用底部剪力法进行地震力的初步估算。结构底部剪力V<sub>EK</sub> = α<sub>max</sub> · G<sub>E</sub>，"
        "其中α<sub>max</sub>为水平地震影响系数最大值，G<sub>E</sub>为结构总重力荷载代表值。", s['BodyText_CN']))
    story.append(Paragraph(
        "注：文件指出结构第一周期不大于场地特征周期Tg=0.90s（IV类场地），位于地震影响系数曲线水平段，"
        "因此直接取α<sub>max</sub>计算。", s['BodyText_CN']))

    building_area = 40.8 * 19.5
    G_orig = 7.0 * building_area * 5
    V_orig = 0.08 * G_orig
    G_B = 28.0 * building_area * 5
    V_B = 0.16 * G_B
    G_CD = 14.0 * building_area * 5
    V_CD = 0.08 * G_CD  # 7度但构造按8度

    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<b>原设计（7度）：</b>", s['BodyText_NI']))
    story.append(Paragraph(
        f"G<sub>E</sub> = 7.0 × {building_area:.1f} × 5 = {G_orig:.0f} kN", s['Formula']))
    story.append(Paragraph(
        f"V<sub>EK</sub> = 0.08 × {G_orig:.0f} = <b>{V_orig:.0f} kN</b>", s['Formula']))

    story.append(Paragraph("<b>B楼改造后（8度）：</b>", s['BodyText_NI']))
    story.append(Paragraph(
        f"G<sub>E</sub> = 28.0 × {building_area:.1f} × 5 = {G_B:.0f} kN", s['Formula']))
    story.append(Paragraph(
        f"V<sub>EK</sub> = 0.16 × {G_B:.0f} = <b>{V_B:.0f} kN</b>", s['Formula']))

    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"地震力从{V_orig:.0f}kN增大到{V_B:.0f}kN，<b>放大了{V_B/V_orig:.1f}倍</b>。"
        f"这一结果与方案文件中\"地震力放大约为原来的8倍\"一致。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("5.2 地震力放大的分解", s['SubsectionTitle']))
    story.append(Paragraph(
        "地震力放大8倍由两个因素叠加：", s['BodyText_CN']))
    story.append(Paragraph(
        "• 重力荷载代表值增大 4.0倍 （荷载大幅增加）", s['BulletItem']))
    story.append(Paragraph(
        "• 地震影响系数增大 2.0倍 （设防烈度提高一度）", s['BulletItem']))
    story.append(Paragraph(
        "• 综合效应：4.0 × 2.0 = 8.0倍", s['BulletItem']))
    story.append(Paragraph(
        "这意味着原结构需要抵抗8倍于原设计的水平地震作用力，远超任何常规加固能应对的范围。", s['BodyText_CN']))

    story.append(PageBreak())

    # ========== SECTION 6: 基础 ==========
    story.append(section_bar("六、基础承载力验算", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("6.1 原桩基承载力", s['SubsectionTitle']))
    story.append(Paragraph(
        "原设计基础为PHC500管桩（Ra=1,350kN）+防水板。假设典型中柱下布置4根桩（8.1×6.5m柱网下的常见布置），"
        "则单柱桩基总承载力为5,400kN。", s['BodyText_CN']))

    N_std_orig = (5.0 + 4.0) * 52.65 * 5
    N_std_B = (8.0 + 40.0) * 52.65 * 5

    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("6.2 标准组合轴力对比", s['SubsectionTitle']))
    story.append(Paragraph(
        f"原设计标准组合轴力：N = (5.0+4.0) × 52.65 × 5 = <b>{N_std_orig:.0f} kN</b>，"
        f"桩基利用率 = {N_std_orig/5400:.1%}", s['BodyText_CN']))
    story.append(Paragraph(
        f"B楼改造后标准组合轴力：N = (8.0+40.0) × 52.65 × 5 = <b>{N_std_B:.0f} kN</b>，"
        f"桩基利用率 = {N_std_B/5400:.1%} → <b>严重超限</b>", s['BodyText_CN']))

    n_piles_needed = int(np.ceil(N_std_B / 1350))
    n_extra = int(np.ceil((N_std_B - 5400) / 650))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("6.3 补桩需求", s['SubsectionTitle']))
    story.append(Paragraph(
        f"B楼每根中柱需桩基承载力{N_std_B:.0f}kN，原4根PHC500仅提供5,400kN，缺口{N_std_B-5400:.0f}kN。"
        f"按350预制方桩（Ra=650kN）计算，每柱需增设约<b>{n_extra}根</b>锚杆静压桩。", s['BodyText_CN']))
    story.append(Paragraph(
        "在既有地下室内（净空有限）完成如此大量的补桩施工，面临以下困难：", s['BodyText_CN']))
    story.append(Paragraph("• 地下室净空受限，大型压桩设备难以进入和操作", s['BulletItem']))
    story.append(Paragraph("• 每柱12根桩的布置空间极其紧张，桩间距难以满足规范要求", s['BulletItem']))
    story.append(Paragraph("• 大量压桩可能对既有桩基和地下室结构造成扰动", s['BulletItem']))
    story.append(Paragraph("• 补桩与原桩的协同工作效果存在不确定性", s['BulletItem']))

    story.append(PageBreak())

    # ========== SECTION 7: 梁与净高 ==========
    story.append(section_bar("七、梁承载力与净高验算", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("7.1 梁弯矩计算", s['SubsectionTitle']))
    story.append(Paragraph(
        "以典型二层以上主梁（400×800mm）为例，按简支梁估算跨中弯矩 M = qL²/8。"
        "主梁承担一个柱距宽度（6.5m）的荷载，跨度8.1m。", s['BodyText_CN']))

    q_orig = (1.2 * 5.0 + 1.4 * 4.0) * 6.5
    M_orig = q_orig * 8.1**2 / 8
    q_B = (1.2 * 8.0 + 1.4 * 40.0) * 6.5
    M_B = q_B * 8.1**2 / 8

    story.append(Paragraph(f"原设计：q = (1.2×5.0+1.4×4.0)×6.5 = {q_orig:.1f} kN/m", s['Formula']))
    story.append(Paragraph(f"M = {q_orig:.1f}×8.1²/8 = <b>{M_orig:.0f} kN·m</b>", s['Formula']))
    story.append(Paragraph(f"B楼：q = (1.2×8.0+1.4×40.0)×6.5 = {q_B:.1f} kN/m", s['Formula']))
    story.append(Paragraph(f"M = {q_B:.1f}×8.1²/8 = <b>{M_B:.0f} kN·m</b>（增大{M_B/M_orig:.1f}倍）", s['Formula']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("7.2 原梁承载力估算", s['SubsectionTitle']))
    story.append(Paragraph(
        "假设原梁配筋率约1.5%（400×800梁，h0=760mm），"
        "抗弯承载力 M<sub>u</sub> = f<sub>y</sub>·A<sub>s</sub>·0.9·h<sub>0</sub>：", s['BodyText_CN']))

    As = 0.015 * 400 * 760
    Mu = 400 * As * 0.9 * 760 / 1e6
    story.append(Paragraph(
        f"A<sub>s</sub> = 0.015×400×760 = {As:.0f} mm²", s['Formula']))
    story.append(Paragraph(
        f"M<sub>u</sub> = 400×{As:.0f}×0.9×760 / 10⁶ = <b>{Mu:.0f} kN·m</b>", s['Formula']))
    story.append(Paragraph(
        f"B楼弯矩需求{M_B:.0f}kN·m，承载力缺口 = ({M_B:.0f}-{Mu:.0f})/{Mu:.0f} = <b>{(M_B-Mu)/Mu:.0%}</b>", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("7.3 净高验算 — 关键瓶颈", s['SubsectionTitle']))
    h0_need = np.sqrt(M_B * 1e6 / (400 * 0.015 * 400 * 0.9))
    h_need = h0_need + 40
    net_h_new = 4000 - h_need - 120 - 80

    story.append(Paragraph(
        f"要满足B楼弯矩需求，保持原配筋率不变，梁高需增大到约<b>{h_need:.0f}mm</b>。", s['BodyText_CN']))
    story.append(Paragraph(
        "标准层净高计算：", s['BodyText_CN']))
    story.append(Paragraph(
        f"净高 = 层高 - 梁高 - 楼板厚 - 叠合层 = 4000 - {h_need:.0f} - 120 - 80 = <b>{net_h_new:.0f}mm</b>", s['Formula']))

    story.append(make_table(
        ['项目', '原设计', 'B楼加固后', '要求'],
        [
            ['梁高 (mm)', '800', f'{h_need:.0f}', '-'],
            ['楼板+面层 (mm)', '120', '200 (含叠合层)', '-'],
            ['梁下净高 (mm)', '3,080', f'{net_h_new:.0f}', '≥ 3,000'],
            ['是否满足', '满足', '不满足 (差700mm)', '-'],
        ],
        col_widths=[40*mm, 35*mm, 45*mm, 35*mm],
        highlight_rows=[2, 3]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "这是一个<b>物理性瓶颈</b>：在4.0m的层高中，无论采用何种加固手段，"
        "都无法同时满足40kN/m²的承载力要求和3.0m的净高要求。"
        "即使采用钢梁替代混凝土梁（同等承载力下梁高较小），在40kN/m²、8.1m跨度条件下，"
        "钢梁高度仍需约800-900mm，净高也只能做到约2,700-2,800mm。", s['BodyText_CN']))

    story.append(PageBreak())

    # ========== SECTION 8: 应力滞后 ==========
    story.append(section_bar("八、应力滞后效应分析", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("8.1 二次受力原理", s['SubsectionTitle']))
    story.append(Paragraph(
        "加固施工是在原结构已承受恒载（自重）的状态下进行的。新增的加固材料"
        "（新浇混凝土、粘贴钢板等）只能承担加固完成后新施加的荷载，无法分担原结构已经承受的恒载。"
        "这就是\"应力滞后效应\"——加固材料的应力始终\"滞后于\"原结构材料。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("8.2 定量分析", s['SubsectionTitle']))

    sigma_dead = 5.0 * 52.65 * 5 * 1000 / 560000
    sigma_total = 3054 * 1000 / 560000
    sigma_new = (40.0 - 4.0) * 1.4 * 52.65 * 5 * 1000 / 560000

    story.append(Paragraph(
        f"原结构柱在恒载下的应力：σ<sub>G</sub> = {sigma_dead:.1f} MPa "
        f"（占总应力的{sigma_dead/sigma_total:.0%}）", s['BodyText_CN']))
    story.append(Paragraph(
        f"新增活荷载（36kN/m²增量）产生的应力：Δσ = {sigma_new:.1f} MPa", s['BodyText_CN']))
    story.append(Paragraph(
        "这意味着新加固材料需要独自承担的应力（23.7MPa）已经接近混凝土设计强度（19.1MPa），"
        "而加固构件的有效利用率通常只有60-80%（新旧结合面的传力损失、界面滑移等），"
        "实际安全裕度极低。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("8.3 风险评估", s['SubsectionTitle']))
    story.append(Paragraph("• <b>承载力折减</b>：加固后构件实际承载力可能仅为理论值的60-80%", s['BulletItem']))
    story.append(Paragraph("• <b>节点质量不可检</b>：新旧混凝土结合面无法通过回弹、取芯等常规手段检测", s['BulletItem']))
    story.append(Paragraph("• <b>长期耐久性</b>：植筋胶、结构胶的50年耐久性（本项目要求后续工作年限≥50年）存在不确定性", s['BulletItem']))
    story.append(Paragraph("• <b>蠕变效应</b>：在持续高应力下，混凝土蠕变将加剧应力重分布，可能导致长期变形超限", s['BulletItem']))

    story.append(PageBreak())

    # ========== SECTION 9: 消能减震局限 ==========
    story.append(section_bar("九、消能减震技术局限性分析", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("9.1 消能减震的作用机理", s['SubsectionTitle']))
    story.append(Paragraph(
        "消能减震技术通过在结构中设置阻尼器，在地震中吸收和耗散地震能量，从而降低结构的地震响应"
        "（主要是<b>水平方向</b>的加速度和位移）。其本质是增加结构的阻尼比，减小地震作用效应。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("9.2 对本项目的适用性分析", s['SubsectionTitle']))
    story.append(Paragraph(
        "本项目的核心矛盾是<b>竖向承载力严重不足</b>（活荷载增加900%），而非单纯的水平抗震不足。"
        "消能减震对竖向承载力<b>毫无帮助</b>。", s['BodyText_CN']))

    story.append(make_table(
        ['问题类型', '能否通过消能减震解决', '说明'],
        [
            ['竖向承载力不足', '不能', '阻尼器不提供竖向承载力'],
            ['柱轴压比超限', '不能', '轴压比由竖向荷载决定'],
            ['梁承载力不足', '不能', '由竖向荷载产生的弯矩决定'],
            ['基础承载力不足', '不能', '由竖向荷载决定'],
            ['水平地震力过大', '部分缓解', '可降低约30-40%'],
            ['抗震构造措施等级', '可降低', '最大降低一度 (TCECS 547-2018)'],
        ],
        col_widths=[45*mm, 40*mm, 85*mm],
        highlight_rows=[0, 1, 2, 3]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("9.3 即使减震后地震力仍然过大", s['SubsectionTitle']))
    V_reduced = V_B * 0.65
    story.append(Paragraph(
        f"假设消能减震能将地震响应降低35%（理想情况），降低后的底部剪力为：", s['BodyText_CN']))
    story.append(Paragraph(
        f"V<sub>减震后</sub> = {V_B:.0f} × 0.65 = <b>{V_reduced:.0f} kN</b>，"
        f"仍是原设计({V_orig:.0f}kN)的<b>{V_reduced/V_orig:.1f}倍</b>", s['Formula']))
    story.append(Paragraph(
        "即使消能减震达到理想效果，原结构梁柱的承载力加固仍然无法避免。"
        "消能减震仅能在构造措施层面提供一些便利（箍筋间距放宽等），"
        "对承载力缺口180%的根本问题没有实质帮助。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("9.4 方案中消能减震的实际作用", s['SubsectionTitle']))
    story.append(Paragraph(
        "方案中大量篇幅介绍砌体支墩式消能减震技术（第19-28页），给人\"有了减震就能解决问题\"的错觉。"
        "但实际上，减震在本项目中的作用仅限于：将抗震构造措施从二级降为三级（TCECS 547-2018第6.3.6条），"
        "即箍筋间距等构造要求的适当放松。<b>这无法替代梁柱板基础的全面承载力加固。</b>", s['BodyText_CN']))

    story.append(PageBreak())

    # ========== SECTION 10: 需求质疑 ==========
    story.append(section_bar("十、需求合理性质疑", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("10.1 40kN/m²是否有必要？", s['SubsectionTitle']))
    story.append(Paragraph(
        "方案二第16页指出：<i>\"功能区按3米高满铺人民币的最大重量为30kN/m²\"</i>。"
        "这说明即使在最极端情况下（3米高满铺现金），实际荷载也只有30kN/m²。"
        "40kN/m²的取值包含了相当大的安全裕度。", s['BodyText_CN']))
    story.append(Paragraph(
        "实际金库运营中，不可能所有楼层、所有区域都堆满现金。合理的做法是<b>分区设计</b>：", s['BodyText_CN']))

    story.append(make_table(
        ['功能分区', '建议荷载 (kN/m²)', '说明'],
        [
            ['核心保管区', '25-30', '密集存放贵重物品的核心区域'],
            ['一般存放区', '15-20', '非满铺区域、周转区'],
            ['通道/操作区', '4-8', '人员通行和操作空间'],
            ['办公/管理区', '2-3.5', '常规办公荷载'],
        ],
        col_widths=[40*mm, 45*mm, 85*mm]
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("10.2 抗震8度是否必要？", s['SubsectionTitle']))
    story.append(Paragraph(
        "方案依据GA38-2021《银行安全防范要求》，将金库抗震设防烈度提高一度至8度。"
        "但需要核实GA38-2021原文的具体要求：是\"金库区域提高一度\"还是\"整栋建筑提高一度\"？"
        "如果仅是金库核心保管区提高一度，则可以通过局部加强而非全楼加固来实现。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("10.3 是否所有楼层都需高荷载？", s['SubsectionTitle']))
    story.append(Paragraph(
        "方案一提到A楼\"三至五层为综合管理区和附属区\"，实际荷载远低于40kN/m²。"
        "如果仅1-2层做金库保管区，上层做办公和管理，加固量将大幅缩小，"
        "可能回到常规加固的合理范围内。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("10.4 需求优化后的可行性", s['SubsectionTitle']))
    story.append(Paragraph(
        "如果通过需求优化将荷载降到合理范围，加固的可行性将显著提高：", s['BodyText_CN']))

    story.append(make_table(
        ['活荷载 (kN/m²)', '需要梁高 (mm)', '梁下净高 (mm)', '是否可行'],
        [
            ['40（当前方案）', '~1,300', '~2,300', '不可行'],
            ['30', '~1,100', '~2,500', '不可行'],
            ['20', '~950', '~2,650', '紧张'],
            ['12（档案标准）', '~800', '~2,800', '勉强可行'],
        ],
        col_widths=[40*mm, 40*mm, 40*mm, 40*mm],
        highlight_rows=[0, 1]
    ))

    story.append(Paragraph(
        "在分区设计、荷载优化的前提下，不拆除房屋、通过常规加固满足使用要求是有可能的，"
        "但需要业主方重新审视40kN/m²全楼满铺的需求是否确实必要。", s['BodyText_CN']))

    story.append(PageBreak())

    # ========== SECTION 10B: 分区进库方案 ==========
    story.append(section_bar("十一、分区进库方案 — 降低荷载实现合理加固", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("11.1 核心思路", s['SubsectionTitle']))
    story.append(Paragraph(
        "如果不要求整栋楼所有楼层全部按金库保管区设计，而是仅将部分楼层或部分区域作为"
        "高荷载保管区（50%-70%进库），其余区域作为办公、管理、通道等常规功能，"
        "则整栋楼的等效荷载将大幅降低，有可能回到常规加固的合理范围。", s['BodyText_CN']))
    story.append(Paragraph(
        "这一思路的本质是：<b>通过功能分区降低楼面等效荷载，使加固量可控</b>。", s['BodyText_CN']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("11.2 不同进库比例的等效荷载计算", s['SubsectionTitle']))
    story.append(Paragraph(
        "假设保管区活荷载取30kN/m²（3m高满铺人民币的实际极限值），"
        "非保管区（通道+办公+管理）活荷载取4.0kN/m²（原厂房标准），"
        "按不同进库比例计算等效荷载如下：", s['BodyText_CN']))

    # Calculate for different ratios
    vault_load = 30.0  # kN/m2
    non_vault_load = 4.0
    ratios = [1.0, 0.7, 0.6, 0.5, 0.4, 0.3]
    rows_ratio = []
    fc_val = 19.1
    col_A = 560000  # mm2
    beam_b_val = 400
    span_x_val = 8.1
    span_y_val = 6.5
    trib = span_x_val * span_y_val
    dead_new_val = 8.0  # with reinforcement extra weight

    for r in ratios:
        equiv_live = r * vault_load + (1 - r) * non_vault_load
        q_beam = (1.2 * dead_new_val + 1.4 * equiv_live) * span_y_val
        M_beam = q_beam * span_x_val**2 / 8
        # estimate beam height needed
        h0_est = np.sqrt(M_beam * 1e6 / (400 * 0.015 * beam_b_val * 0.9))
        h_est = h0_est + 40
        net_h = 4000 - h_est - 120 - 80
        # axial ratio
        N_col = (1.2 * dead_new_val + 1.4 * equiv_live) * trib * 5
        ax_ratio = N_col * 1000 / (fc_val * col_A)
        # pile utilization
        N_std = (dead_new_val + equiv_live) * trib * 5
        pile_util = N_std / 5400

        feasible = "可行" if net_h >= 3000 and ax_ratio <= 0.75 else ("紧张" if net_h >= 2800 and ax_ratio <= 0.85 else "不可行")
        pct = f"{r:.0%}"
        rows_ratio.append([
            pct,
            f'{equiv_live:.1f}',
            f'{ax_ratio:.3f}',
            f'{h_est:.0f}',
            f'{net_h:.0f}',
            f'{pile_util:.0%}',
            feasible
        ])

    story.append(Spacer(1, 2*mm))
    story.append(make_table(
        ['进库比例', '等效活载\n(kN/m²)', '柱轴压比', '需梁高\n(mm)', '梁下净高\n(mm)', '桩基\n利用率', '可行性'],
        rows_ratio,
        col_widths=[22*mm, 22*mm, 22*mm, 22*mm, 22*mm, 22*mm, 22*mm],
        highlight_rows=[3, 4, 5]  # highlight the feasible ones
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("11.3 分析结论", s['SubsectionTitle']))

    # Find the threshold
    story.append(Paragraph(
        "从上表可以看出：", s['BodyText_CN']))
    story.append(Paragraph(
        "• 进库比例100%（全楼满铺）：轴压比和净高均严重超限，<b>不可行</b>", s['BulletItem']))
    story.append(Paragraph(
        "• 进库比例70%：等效活载22.2kN/m²，轴压比0.858，净高约2,766mm，仍然紧张", s['BulletItem']))
    story.append(Paragraph(
        "• 进库比例60%：等效活载19.6kN/m²，轴压比0.775，净高约2,836mm，接近可行", s['BulletItem']))
    story.append(Paragraph(
        "• <b>进库比例50%及以下</b>：等效活载17.0kN/m²，轴压比0.691，净高约2,910mm，"
        "<b>进入常规加固的合理范围</b>", s['BulletItem']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("11.4 推荐方案：分层分区设计", s['SubsectionTitle']))
    story.append(Paragraph(
        "基于以上分析，推荐以下分层分区设计思路（以B楼为例）：", s['BodyText_CN']))

    story.append(make_table(
        ['楼层', '功能', '活荷载 (kN/m²)', '进库比例', '说明'],
        [
            ['1层 (层高5.4m)', '核心保管区', '30', '80%', '层高富余，净高可满足'],
            ['2层', '保管区+操作区', '20-25', '60%', '适度分区，加固可控'],
            ['3层', '周转/临时存放', '12-15', '40%', '常规加固即可满足'],
            ['4层', '清分/操作区', '4-8', '-', '接近原设计荷载'],
            ['5层', '办公/管理/监控', '2-3.5', '-', '无需加固或轻微加固'],
        ],
        col_widths=[30*mm, 30*mm, 30*mm, 25*mm, 50*mm],
    ))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "以上分区方案的优势：", s['BodyText_CN']))
    story.append(Paragraph(
        "• <b>底层利用层高优势</b>：底层层高5.4m，比标准层多1.4m，即使梁加大到1100mm，"
        "净高仍有约4,000mm，可满足金库要求", s['BulletItem']))
    story.append(Paragraph(
        "• <b>上部楼层逐层递减</b>：荷载从下到上递减，符合结构受力规律（下部柱承担累积荷载更大），"
        "加固量自然分配合理", s['BulletItem']))
    story.append(Paragraph(
        "• <b>整体等效荷载可控</b>：全楼等效活荷载约15-18kN/m²，柱轴压比可控制在0.75以内，"
        "梁下净高基本满足要求", s['BulletItem']))
    story.append(Paragraph(
        "• <b>加固方法简单直接</b>：以增大截面为主，辅以少量碳纤维/粘钢加固，"
        "无需\"脱胎换骨\"式全面改造", s['BulletItem']))
    story.append(Paragraph(
        "• <b>基础加固量可控</b>：桩基利用率降至120-150%范围，每柱仅需增设2-4根静压桩，"
        "在地下室内施工可行", s['BulletItem']))
    story.append(Paragraph(
        "• <b>可能不需要消能减震</b>：如荷载降到合理范围，原结构梁柱经常规加固即可满足"
        "抗震承载力和变形要求，节省消能减震系统的费用和维护成本", s['BulletItem']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("11.5 进库比例与加固可行性的临界点", s['SubsectionTitle']))
    story.append(Paragraph(
        "综合柱轴压比（≤0.75）、梁下净高（≥3.0m）、基础承载力三个控制指标，"
        "本项目的加固可行性临界点大致在<b>等效活荷载17-20kN/m²</b>，"
        "对应进库比例约<b>50-60%</b>。", s['BodyText_CN']))
    story.append(Paragraph(
        "换言之：如果每层楼面有50-60%的面积作为保管区（30kN/m²），其余40-50%作为通道和操作区（4kN/m²），"
        "则通过常规加固手段（增大截面+局部粘钢/碳纤维+少量补桩）即可满足使用要求，"
        "<b>无需拆除重建</b>。", s['BodyText_CN']))
    story.append(Paragraph(
        "这也意味着，设计单位提出的全面加固或拆内重建方案，很可能是基于40kN/m²全楼满铺这一"
        "过于保守的需求假设所导致的。调整需求即可根本性地改变加固方案的可行性。", s['BodyText_CN']))

    story.append(PageBreak())

    # ========== SECTION 12: 综合结论 ==========
    story.append(section_bar("十二、综合结论与建议", s))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("12.1 定量分析汇总", s['SubsectionTitle']))
    story.append(make_table(
        ['验算项目', '原设计', 'B楼改造后', '超限程度', '结论'],
        [
            ['柱轴压比', '0.285', '1.615', '超限2.2倍', '截面需增大2.2倍'],
            ['底部地震力', '2,228 kN', '17,821 kN', '放大8.0倍', '远超加固范围'],
            ['桩基利用率', '43.9%', '234.0%', '超限2.3倍', '需补桩12根/柱'],
            ['主梁弯矩', '618 kN·m', '3,497 kN·m', '增大5.7倍', '承载力缺口180%'],
            ['梁下净高', '3,080mm', '~2,488mm', '差592mm', '不满足3m要求'],
        ],
        col_widths=[30*mm, 27*mm, 30*mm, 28*mm, 40*mm],
        highlight_rows=[0, 1, 2, 3, 4]
    ))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("12.2 加固方案不合理的7个核心理由", s['SubsectionTitle']))

    reasons = [
        ("<b>1. 柱轴压比超限严重</b>：原截面轴压比1.615，超限值(0.75)的2.2倍。即使增大到1200×1200mm仍勉强，"
         "且严重压缩建筑使用空间，每侧多占200mm以上。"),
        ("<b>2. 地震力放大超8倍</b>：荷载增大4倍×地震系数翻倍=8倍，远超任何\"加固\"能合理应对的范围。"
         "原结构设计时根本没有为这个量级的荷载预留任何余量。"),
        ("<b>3. 梁加固后净高不足3m</b>：满足弯矩需求的梁高约1,312mm，加上楼板和叠合层，梁下净高仅约2,488mm，"
         "远低于金库3,000mm的净高要求。这是物理层面的硬约束，无法通过工程手段绕过。"),
        ("<b>4. 基础补桩在既有地下室中施工极困难</b>：每柱需增设12根锚杆静压桩，地下室净空受限，"
         "桩间距难以满足规范要求，施工质量和协同工作效果存疑。"),
        ("<b>5. 应力滞后效应导致实际安全裕度不足</b>：加固材料仅承担新增荷载，有效利用率60-80%，"
         "在900%活荷载增量下，实际承载力远低于理论值，且节点质量不可检测。"),
        ("<b>6. 消能减震不解决根本问题</b>：阻尼器只降低水平地震响应，不提供竖向承载力。"
         "本项目核心矛盾是竖向荷载增加900%，消能减震对此毫无帮助。"),
        ("<b>7. 方案自相矛盾</b>：方案二承认B楼\"超出常规加固合理范围\"而采取拆内重建，"
         "但荷载需求完全相同的A楼仍走加固路线，逻辑不自洽。"),
    ]
    for r in reasons:
        story.append(Paragraph(r, s['BulletItem']))
        story.append(Spacer(1, 1*mm))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("12.3 建议", s['SubsectionTitle']))

    story.append(Paragraph(
        "<b>建议一：重新审视需求的合理性。</b>"
        "40kN/m²全楼满铺的需求可能是过度保守的。通过分区设计（核心保管区25-30kN/m²、"
        "通道区4-8kN/m²、办公区2-3.5kN/m²），可以将加固量控制在合理范围内，"
        "使得不拆除房屋、通过常规加固满足要求成为可能。", s['BodyText_CN']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<b>建议二：如需求无法降低，应评估拆除重建方案。</b>"
        "当所有构件（基础、柱、梁、板）同时需要\"脱胎换骨\"式加固时，新建结构在安全性、"
        "使用空间、施工质量可控性、全寿命周期成本等方面均优于加固方案。"
        "方案二对B楼采取的\"保外拆内\"做法已间接证明了这一点。", s['BodyText_CN']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<b>建议三：核实GA38-2021的具体要求。</b>"
        "确认抗震设防烈度提高一度的要求是针对金库核心区还是整栋建筑。"
        "如仅针对核心区，可通过局部加强实现，无需全楼按8度设防。", s['BodyText_CN']))

    story.append(Spacer(1, 10*mm))
    story.append(horizontal_line())
    story.append(Paragraph(
        "注：本报告为方案阶段的初步定量分析，采用简化计算方法。精确结果需以施工图阶段的详细结构计算为准。"
        "本报告仅供技术评审参考。", s['FootNote']))

    # Build PDF
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF报告已生成: {output_path}")
    return output_path


if __name__ == '__main__':
    build_report()
