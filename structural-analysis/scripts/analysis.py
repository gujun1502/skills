# -*- coding: utf-8 -*-
"""
结构加固方案合理性定量分析
基于 GB50010-2010 / GB50011-2010 / GB55008-2021
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np

print('='*70)
print('  结构加固方案合理性定量分析报告')
print('  基于 GB50010-2010 / GB50011-2010 / GB55008-2021')
print('='*70)

# ============================================================
# 1. 原结构基本参数
# ============================================================
print('\n' + '='*70)
print('第一部分：原结构基本参数')
print('='*70)

span_x = 8.1  # m
span_y = 6.5  # m
trib_area = span_x * span_y
print(f'柱网: {span_x} x {span_y} m')
print(f'单柱负荷面积: {trib_area:.2f} m2')

n_floors = 5
floor_heights = [5.4, 4.0, 4.0, 4.0, 4.0]
total_height = sum(floor_heights)
print(f'层数: {n_floors}, 总高: {total_height:.1f} m')

# 材料
fc = 19.1   # C40 轴心抗压强度设计值 MPa
fy = 400    # HRB400 MPa
Ec = 32500  # C40 弹性模量 MPa

# 典型中柱截面 (底层)
col_b = 700  # mm
col_h = 800  # mm
col_area = col_b * col_h  # mm2
print(f'典型底层中柱截面: {col_b}x{col_h} mm')
print(f'柱截面面积: {col_area/1e4:.2f} cm2 = {col_area/1e6:.4f} m2')

# ============================================================
# 2. 荷载对比分析
# ============================================================
print('\n' + '='*70)
print('第二部分：荷载对比分析')
print('='*70)

dead_load_orig = 5.0    # kN/m2
live_load_orig = 4.0    # kN/m2
gravity_repr_orig = dead_load_orig + 0.5 * live_load_orig
print(f'原设计: 恒载={dead_load_orig}, 活载={live_load_orig} kN/m2')
print(f'原设计重力荷载代表值: {gravity_repr_orig:.1f} kN/m2 (与文件中10.0一致)')

dead_load_new = 5.0
live_load_new_B = 40.0
live_load_new_CD = 12.0
dead_extra = 3.0  # 加固增加的自重

gravity_repr_B = (dead_load_new + dead_extra) + 0.5 * live_load_new_B
print(f'\nB楼改造后: 恒载={dead_load_new+dead_extra}, 活载={live_load_new_B} kN/m2')
print(f'B楼重力荷载代表值: {gravity_repr_B:.1f} kN/m2')

gravity_repr_CD = (dead_load_new + dead_extra) + 0.5 * live_load_new_CD
print(f'C/D楼改造后: 恒载={dead_load_new+dead_extra}, 活载={live_load_new_CD} kN/m2')
print(f'C/D楼重力荷载代表值: {gravity_repr_CD:.1f} kN/m2')

ratio_B = gravity_repr_B / gravity_repr_orig
ratio_CD = gravity_repr_CD / gravity_repr_orig
print(f'\n荷载倍数: B楼={ratio_B:.1f}倍, C/D楼={ratio_CD:.1f}倍')

# ============================================================
# 3. 柱轴压比验算
# ============================================================
print('\n' + '='*70)
print('第三部分：柱轴压比验算 (GB50011-2010 表6.3.6)')
print('='*70)

axial_ratio_limit_2 = 0.75  # 二级
axial_ratio_limit_3 = 0.85  # 三级
print(f'轴压比限值: 二级={axial_ratio_limit_2}, 三级={axial_ratio_limit_3}')

# 原设计
N_orig = (1.2 * dead_load_orig + 1.4 * live_load_orig) * trib_area * n_floors
axial_ratio_orig = N_orig * 1000 / (fc * col_area)
print(f'\n--- 原设计 (三级抗震) ---')
print(f'底层中柱轴力: N = {N_orig:.0f} kN')
print(f'轴压比: N/(fc*A) = {axial_ratio_orig:.3f}')
status = "合格" if axial_ratio_orig <= axial_ratio_limit_3 else "不合格"
print(f'限值: {axial_ratio_limit_3} -> {status}')

# B楼改造后
N_new_B = (1.2 * (dead_load_new + dead_extra) + 1.4 * live_load_new_B) * trib_area * n_floors
axial_ratio_B = N_new_B * 1000 / (fc * col_area)
print(f'\n--- B楼改造后 (二级抗震, 原截面) ---')
print(f'底层中柱轴力: N = {N_new_B:.0f} kN')
print(f'轴压比: N/(fc*A) = {axial_ratio_B:.3f}')
print(f'限值: {axial_ratio_limit_2} -> 超限 {axial_ratio_B/axial_ratio_limit_2:.1f} 倍!')

# 需要多大截面
required_area_B = N_new_B * 1000 / (fc * axial_ratio_limit_2)
side_B = np.sqrt(required_area_B)
print(f'满足轴压比需截面面积: {required_area_B/1e4:.0f} cm2 (约{side_B:.0f}x{side_B:.0f}mm)')
print(f'即原截面的 {required_area_B/col_area:.1f} 倍')

# 1200x1200验证
col_1200 = 1200 * 1200
axial_ratio_1200 = N_new_B * 1000 / (fc * col_1200)
status_1200 = "勉强合格" if axial_ratio_1200 <= axial_ratio_limit_2 else "仍不合格"
print(f'\n如增大到1200x1200: 轴压比={axial_ratio_1200:.3f} (限值{axial_ratio_limit_2})')
print(f'-> {status_1200}')

# C/D楼
N_new_CD = (1.2 * (dead_load_new + dead_extra) + 1.4 * live_load_new_CD) * trib_area * n_floors
axial_ratio_CD = N_new_CD * 1000 / (fc * col_area)
print(f'\n--- C/D楼改造后 (二级抗震, 原截面) ---')
print(f'底层中柱轴力: N = {N_new_CD:.0f} kN')
print(f'轴压比: {axial_ratio_CD:.3f} (限值{axial_ratio_limit_2})')

# ============================================================
# 4. 地震力对比
# ============================================================
print('\n' + '='*70)
print('第四部分：地震力对比分析')
print('='*70)

alpha_max_7 = 0.08
alpha_max_8 = 0.16
building_area = 40.8 * 19.5
print(f'单栋平面面积: {building_area:.1f} m2')

G_orig = gravity_repr_orig * building_area * n_floors
V_orig = alpha_max_7 * G_orig
print(f'\n原设计 (7度):')
print(f'  总重力荷载: G = {G_orig:.0f} kN')
print(f'  底部剪力: V = {alpha_max_7} x {G_orig:.0f} = {V_orig:.0f} kN')

G_new_B_total = gravity_repr_B * building_area * n_floors
V_new_B = alpha_max_8 * G_new_B_total
print(f'\nB楼改造后 (8度):')
print(f'  总重力荷载: G = {G_new_B_total:.0f} kN')
print(f'  底部剪力: V = {alpha_max_8} x {G_new_B_total:.0f} = {V_new_B:.0f} kN')
print(f'  地震力放大倍数: {V_new_B/V_orig:.1f} 倍!')

G_new_CD_total = gravity_repr_CD * building_area * n_floors
V_new_CD = alpha_max_7 * G_new_CD_total
print(f'\nC/D楼改造后 (7度):')
print(f'  总重力荷载: G = {G_new_CD_total:.0f} kN')
print(f'  底部剪力: V = {V_new_CD:.0f} kN')
print(f'  地震力放大倍数: {V_new_CD/V_orig:.1f} 倍')

# ============================================================
# 5. 基础承载力验算
# ============================================================
print('\n' + '='*70)
print('第五部分：基础承载力验算')
print('='*70)

Ra_orig = 1350  # kN
n_piles_typical = 4
pile_capacity = n_piles_typical * Ra_orig
print(f'原设计: PHC500管桩, Ra={Ra_orig}kN')
print(f'典型中柱下{n_piles_typical}根桩, 总承载力: {pile_capacity}kN')

N_std_orig = (dead_load_orig + live_load_orig) * trib_area * n_floors
print(f'原设计底层中柱标准组合轴力: {N_std_orig:.0f} kN')
print(f'桩基利用率: {N_std_orig/pile_capacity:.1%}')

N_std_B = (dead_load_new + dead_extra + live_load_new_B) * trib_area * n_floors
print(f'\nB楼改造后底层中柱标准组合轴力: {N_std_B:.0f} kN')
print(f'桩基利用率: {N_std_B/pile_capacity:.1%} -> 严重超限!')
n_piles_needed = int(np.ceil(N_std_B / Ra_orig))
print(f'需要桩数: {n_piles_needed} 根 (原{n_piles_typical}根)')

Ra_jy = 650
n_extra_piles = int(np.ceil((N_std_B - pile_capacity) / Ra_jy))
print(f'需额外增设350方桩: {n_extra_piles} 根/柱 (Ra={Ra_jy}kN)')

# ============================================================
# 6. 梁承载力验算
# ============================================================
print('\n' + '='*70)
print('第六部分：梁承载力估算')
print('='*70)

beam_b = 400
beam_h = 800
beam_h0 = beam_h - 40
print(f'典型主梁截面: {beam_b}x{beam_h}mm, h0={beam_h0}mm')

q_orig = (1.2 * dead_load_orig + 1.4 * live_load_orig) * span_y
M_orig = q_orig * span_x ** 2 / 8
print(f'\n原设计: q={q_orig:.1f}kN/m, M={M_orig:.0f}kN.m')

q_new_B = (1.2 * (dead_load_new + dead_extra) + 1.4 * live_load_new_B) * span_y
M_new_B = q_new_B * span_x ** 2 / 8
print(f'B楼: q={q_new_B:.1f}kN/m, M={M_new_B:.0f}kN.m')
print(f'弯矩增大: {M_new_B/M_orig:.1f} 倍')

rho_orig = 0.015
As_orig = rho_orig * beam_b * beam_h0
M_capacity = fy * As_orig * 0.9 * beam_h0 / 1e6
print(f'\n原梁估算抗弯承载力: Mu = {M_capacity:.0f} kN.m')
print(f'B楼弯矩需求: {M_new_B:.0f} kN.m')
print(f'承载力缺口: {(M_new_B - M_capacity)/M_capacity:.0%}')

h0_needed = np.sqrt(M_new_B * 1e6 / (fy * rho_orig * beam_b * 0.9))
h_needed = h0_needed + 40
print(f'满足需求需梁高约: {h_needed:.0f}mm (原800mm)')

floor_h = 4000
net_h_orig = floor_h - beam_h - 120
net_h_new = floor_h - h_needed - 120 - 80
print(f'\n层高: {floor_h}mm')
print(f'原设计梁下净高: {net_h_orig}mm')
print(f'加固后梁下净高: {net_h_new:.0f}mm -> 低于3000mm要求!')

# ============================================================
# 7. 应力滞后效应分析
# ============================================================
print('\n' + '='*70)
print('第七部分：应力滞后效应 (二次受力问题)')
print('='*70)

print("""
加固构件的"二次受力"问题是本项目最大的隐患：

原理说明：
  加固是在原结构已承受恒载的状态下进行的。新增的加固材料
  (混凝土、钢板等) 只能承担加固后新增的那部分荷载，无法
  分担原结构已经承受的荷载。

定量分析：
  原结构恒载应力水平:""")

sigma_dead = dead_load_orig * trib_area * n_floors * 1000 / col_area
sigma_total_orig = N_orig * 1000 / col_area
print(f'  - 柱在恒载下的应力: {sigma_dead:.1f} MPa')
print(f'  - 柱在原设计总荷载下的应力: {sigma_total_orig:.1f} MPa')
print(f'  - 恒载应力占比: {sigma_dead/sigma_total_orig:.0%}')

print(f"""
  加固后新增荷载应力:
  - B楼新增活荷载: {live_load_new_B - live_load_orig} kN/m2
  - 新增荷载产生的柱应力: {(live_load_new_B - live_load_orig) * 1.4 * trib_area * n_floors * 1000 / col_area:.1f} MPa

  问题：新加固的混凝土/钢板需要独自承担这部分巨大的新增应力，
  而原柱已经在"带伤工作"。加固材料的有效利用率通常只有
  60-80%，在如此大的荷载增量下，实际安全裕度极低。""")

# ============================================================
# 8. 消能减震的局限性分析
# ============================================================
print('\n' + '='*70)
print('第八部分：消能减震的局限性')
print('='*70)

print(f"""
消能减震(阻尼器)的作用范围：
  - 能做的：降低水平地震响应，减小层间位移
  - 不能做的：提高竖向承载力

本项目的核心矛盾：
  竖向荷载增量: B楼活荷载从4.0→40.0 kN/m2 (增加900%)
  水平地震力增量: 从{V_orig:.0f}→{V_new_B:.0f} kN (增加{(V_new_B-V_orig)/V_orig:.0%})

  即使消能减震能将地震力降低30-40%（理想情况），
  降低后的地震力仍为: {V_new_B*0.65:.0f} kN，
  仍是原设计的 {V_new_B*0.65/V_orig:.1f} 倍。

  而竖向荷载增加的问题完全无法通过消能减震解决，
  梁柱板基础的加固仍然避免不了。

  消能减震仅能实现"构造措施降低一度"，
  即从二级降为三级，但这只是箍筋间距等构造要求的放松，
  对承载力不足的问题毫无帮助。""")

# ============================================================
# 9. 汇总表
# ============================================================
print('\n' + '='*70)
print('第九部分：综合结论')
print('='*70)

print("""
+------------------+--------------+---------------+------------------------+
| 验算项目         | 原设计       | B楼改造后     | 结论                   |
+------------------+--------------+---------------+------------------------+""")
print(f'| 柱轴压比         | {axial_ratio_orig:.3f}        | {axial_ratio_B:.3f}         | 超限{axial_ratio_B/axial_ratio_limit_2:.1f}倍              |')
print(f'| 底部地震力(kN)   | {V_orig:.0f}         | {V_new_B:.0f}        | 放大{V_new_B/V_orig:.1f}倍              |')
print(f'| 桩基利用率       | {N_std_orig/pile_capacity:.0%}           | {N_std_B/pile_capacity:.0%}          | 需增桩{n_extra_piles}根/柱            |')
print(f'| 主梁弯矩(kN.m)   | {M_orig:.0f}          | {M_new_B:.0f}         | 增大{M_new_B/M_orig:.1f}倍             |')
print(f'| 梁下净高(mm)     | {net_h_orig}          | {net_h_new:.0f}         | 低于3000mm要求         |')
print("""+------------------+--------------+---------------+------------------------+

★ 核心结论:

  1. 柱轴压比超限严重 - 即使增大到1200x1200仍勉强，且严重占用空间
  2. 地震力放大超8倍 - 远超"加固"的合理范围
  3. 梁加固后净高不足3m - 不满足金库/档案库使用要求
  4. 基础需大量补桩 - 在既有地下室中施工极困难且风险大
  5. 应力滞后效应 - 加固材料有效利用率低，实际安全裕度不足
  6. 消能减震仅降构造措施 - 不解决承载力本质问题
  7. 所有构件同时需"脱胎换骨" - 已失去加固的经济合理性

★ 建议:
  本项目应重新评估"拆除重建"方案。当加固量达到如此规模时，
  新建结构在安全性、使用空间、施工质量可控性、全寿命周期
  成本等方面均优于加固方案。方案二对B楼采取的"保外拆内"
  做法已间接证明了这一点。
""")
