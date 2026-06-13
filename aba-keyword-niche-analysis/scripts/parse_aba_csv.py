#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_aba_csv.py
================
解析 Amazon Brand Analytics (ABA) Top Search Terms 导出的 CSV 文件，
提取热搜词、点击/转化份额、品牌、ASIN、类目，并做基础的修饰词挖掘，
输出结构化 JSON 供 Agent 后续语义聚类 / MCP 验证 / 打分使用，
同时在控制台打印人类可读的摘要。

用法：
    python parse_aba_csv.py <aba_top_search_terms.csv> [--out result.json] [--top 30]

设计目标：
    - 兼容多种 ABA 导出格式（官方多列 #1/#2/#3 格式 + 第三方工具简化单品牌格式）
    - 对脏数据、缺列、编码异常做容错，不轻易崩溃
    - 所有数值字段安全转换，无法解析的记为 None 而非抛错
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

# Windows 控制台默认 GBK，强制 UTF-8 输出避免中文乱码 / UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# 0. 常量：停用词 & 基础产品词（用于修饰词提取时剔除）
# ---------------------------------------------------------------------------

# 英文停用词（北美市场，搜索词多为英文）
STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "with", "of", "to", "in", "on", "at",
    "by", "from", "as", "is", "are", "be", "this", "that", "these", "those",
    "your", "you", "my", "our", "it", "its", "&", "+", "-", "x", "vs",
    "pack", "set", "pcs", "pc", "pieces", "count", "ct", "size", "new",
}

# 通用基础产品词：这些词描述“品类本身”，挖掘修饰词时通常需要单独看待
# （注意：不能全删，否则会丢失语义；这里只作为一个可选过滤集合，默认保留品类词，
#  仅在 modifier 提取时降权——见 extract_modifiers）
BASE_PRODUCT_WORDS = {
    "case", "cover", "holder", "stand", "charger", "cable", "ring", "necklace",
    "bracelet", "earrings", "watch", "band", "light", "lamp", "bottle", "cup",
    "bag", "box", "organizer", "mount", "set", "kit", "phone", "screen",
}

# 单位/数字噪声正则
NUM_RE = re.compile(r"^[\d\.\,\$%]+$")
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9\-']+")

# 常见知名品牌种子词（用于品牌词初判，可由 Top Clicked Brand 动态扩充）
SEED_BRANDS = {
    "apple", "samsung", "anker", "sony", "nike", "adidas", "amazon", "amazonbasics",
    "logitech", "bose", "jbl", "dell", "hp", "lenovo", "asus", "lego", "disney",
    "pandora", "swarovski", "fossil", "casio", "google", "microsoft", "xiaomi",
    "huawei", "oneplus", "lululemon", "stanley", "yeti", "hydroflask", "otterbox",
    "spigen", "belkin", "razer", "corsair", "ikea", "philips", "panasonic",
}


# ---------------------------------------------------------------------------
# 1. 安全类型转换
# ---------------------------------------------------------------------------

def to_float(val):
    """把 '12.34%' / '$1,234.5' / ' 0.12 ' 这类字符串安全转 float；失败返回 None。"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in ("n/a", "na", "-", "--", "none", "null"):
        return None
    s = s.replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def to_int(val):
    f = to_float(val)
    return int(round(f)) if f is not None else None


def pct_to_ratio(val):
    """把份额值统一成 0-100 的百分数。
    导出里可能是 '12.3%'（=12.3）也可能是 0.123（=12.3%）。"""
    f = to_float(val)
    if f is None:
        return None
    # 启发式：原始字符串带 % 或数值 > 1 视为已是百分数；<=1 视为比例
    s = str(val)
    if "%" in s:
        return f
    if f <= 1.0:
        return f * 100.0
    return f


# ---------------------------------------------------------------------------
# 2. 列名归一化与映射
# ---------------------------------------------------------------------------

def norm_header(h):
    """归一化表头：小写、去多余符号，便于模糊匹配。"""
    if h is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(h).lower())


# 字段别名表：把各种导出表头映射到统一 key
HEADER_ALIASES = {
    "search_frequency_rank": [
        "searchfrequencyrank", "sfr", "rank", "searchrank", "frequencyrank"
    ],
    "search_term": [
        "searchterm", "keyword", "term", "searchterms", "kw"
    ],
    # 简化（单品牌）格式
    "top_clicked_brand": [
        "topclickedbrand", "clickedbrand", "brand", "topbrand", "1clickedbrand"
    ],
    "top_clicked_category": [
        "topclickedcategory", "clickedcategory", "category", "topcategory",
        "1clickedcategory", "categorypath"
    ],
}

# 多列 #1/#2/#3 ABA 官方格式：按 rank 提取
RANKED_ALIASES = {
    "asin": ["clickedasin", "clickeditemasin", "asin", "productasin"],
    "title": ["producttitle", "title", "clickeditemname", "productname"],
    "click_share": ["clickshare", "clickconcentration"],
    "conversion_share": ["conversionshare", "cartaddshare", "convshare"],
}


def build_column_index(headers):
    """返回归一化表头列表 + 单值字段索引映射。"""
    norm = [norm_header(h) for h in headers]
    return norm


def find_col(norm_headers, aliases):
    """在归一化表头里找到第一个匹配 alias 的列索引，找不到返回 None。"""
    for i, h in enumerate(norm_headers):
        for a in aliases:
            if h == a or (a in h and len(a) >= 4):
                return i
    return None


def find_ranked_cols(norm_headers):
    """识别官方多列格式中 #1/#2/#3 的列位置。
    官方表头形如：'#1 Clicked ASIN', 'Product Title', '#1 Click Share', '#1 Conversion Share' ...
    归一化后含 '1' / '2' / '3' 前缀数字。返回 {rank: {field: idx}}。"""
    ranked = defaultdict(dict)
    for i, h in enumerate(norm_headers):
        m = re.match(r"^[#]?([123])(.*)$", h)
        rank = None
        rest = h
        if m:
            rank = int(m.group(1))
            rest = m.group(2)
        # 即使没有数字前缀，也尝试根据上下文（title 紧跟 asin）兜底，这里只处理有前缀的
        if rank is None:
            continue
        for field, aliases in RANKED_ALIASES.items():
            if any(a in rest for a in aliases):
                if field not in ranked[rank]:
                    ranked[rank][field] = i
    return dict(ranked)


# ---------------------------------------------------------------------------
# 3. 读取 CSV（含元数据首行探测）
# ---------------------------------------------------------------------------

def read_rows(path):
    """读取 CSV 全部行（list of list），自动尝试多种编码。"""
    encodings = ["utf-8-sig", "utf-8", "latin-1", "gbk"]
    last_err = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                # 嗅探分隔符
                sample = f.read(8192)
                f.seek(0)
                delim = ","
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                    delim = dialect.delimiter
                except Exception:
                    delim = ","
                reader = csv.reader(f, delimiter=delim)
                rows = [r for r in reader]
            return rows, enc, delim
        except (UnicodeDecodeError, UnicodeError) as e:
            last_err = e
            continue
    raise RuntimeError(f"无法以任何已知编码读取 CSV: {last_err}")


def detect_header_and_meta(rows):
    """
    探测元数据首行与真正的表头行。
    ABA 导出通常第 0 行是元数据（如 'Department=...,Reporting Range=Weekly,Select week=...'），
    第 1 行才是列标题。也兼容没有元数据行的情况。
    返回 (meta_dict, header_idx, headers)。
    """
    meta = {}
    header_idx = 0

    def looks_like_header(cells):
        joined = " ".join(norm_header(c) for c in cells)
        return ("searchterm" in joined) or ("searchfrequencyrank" in joined) or ("keyword" in joined and "rank" in joined)

    # 扫描前 5 行找表头
    for i, row in enumerate(rows[:5]):
        if looks_like_header(row):
            header_idx = i
            break
    else:
        header_idx = 0

    # header 之前的行视为元数据
    for i in range(header_idx):
        for cell in rows[i]:
            if not cell:
                continue
            # 形如 key=value 或 key: value
            m = re.match(r"\s*([^=:]+)\s*[=:]\s*(.+)\s*", str(cell))
            if m:
                meta[m.group(1).strip()] = m.group(2).strip()
            else:
                meta.setdefault("_raw", []).append(str(cell).strip())

    headers = rows[header_idx] if header_idx < len(rows) else []
    return meta, header_idx, headers


# ---------------------------------------------------------------------------
# 4. 行解析 -> 统一记录
# ---------------------------------------------------------------------------

def parse_records(rows, header_idx, headers):
    norm_headers = build_column_index(headers)

    col_rank = find_col(norm_headers, HEADER_ALIASES["search_frequency_rank"])
    col_term = find_col(norm_headers, HEADER_ALIASES["search_term"])
    col_brand = find_col(norm_headers, HEADER_ALIASES["top_clicked_brand"])
    col_cat = find_col(norm_headers, HEADER_ALIASES["top_clicked_category"])
    ranked = find_ranked_cols(norm_headers)

    # 简化格式的单值 asin/title/clickshare/convshare
    col_asin = find_col(norm_headers, RANKED_ALIASES["asin"])
    col_title = find_col(norm_headers, RANKED_ALIASES["title"])
    col_click = find_col(norm_headers, RANKED_ALIASES["click_share"])
    col_conv = find_col(norm_headers, RANKED_ALIASES["conversion_share"])

    if col_term is None:
        raise ValueError(
            "未能在表头中找到 Search Term 列。请确认这是 ABA Top Search Terms 导出文件。\n"
            f"检测到的表头：{headers}"
        )

    records = []
    for row in rows[header_idx + 1:]:
        if not row or all((c is None or str(c).strip() == "") for c in row):
            continue
        # 行长度不足则补齐
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))

        term = str(row[col_term]).strip() if col_term is not None and col_term < len(row) else ""
        if not term:
            continue

        rec = {
            "search_term": term,
            "search_frequency_rank": to_int(row[col_rank]) if col_rank is not None and col_rank < len(row) else None,
            "top_clicked_brand": (str(row[col_brand]).strip() if col_brand is not None and col_brand < len(row) and row[col_brand] else None),
            "top_clicked_category": (str(row[col_cat]).strip() if col_cat is not None and col_cat < len(row) and row[col_cat] else None),
            "ranked": [],  # 列表，每个元素含 rank/asin/title/click_share/conversion_share
        }

        if ranked:
            for r in sorted(ranked.keys()):
                cols = ranked[r]
                rec["ranked"].append({
                    "rank": r,
                    "asin": (str(row[cols["asin"]]).strip() if "asin" in cols and cols["asin"] < len(row) and row[cols["asin"]] else None),
                    "title": (str(row[cols["title"]]).strip() if "title" in cols and cols["title"] < len(row) and row[cols["title"]] else None),
                    "click_share": pct_to_ratio(row[cols["click_share"]]) if "click_share" in cols and cols["click_share"] < len(row) else None,
                    "conversion_share": pct_to_ratio(row[cols["conversion_share"]]) if "conversion_share" in cols and cols["conversion_share"] < len(row) else None,
                })
        else:
            # 简化单品牌格式：只有一组 asin/title/clickshare/convshare
            rec["ranked"].append({
                "rank": 1,
                "asin": (str(row[col_asin]).strip() if col_asin is not None and col_asin < len(row) and row[col_asin] else None),
                "title": (str(row[col_title]).strip() if col_title is not None and col_title < len(row) and row[col_title] else None),
                "click_share": pct_to_ratio(row[col_click]) if col_click is not None and col_click < len(row) else None,
                "conversion_share": pct_to_ratio(row[col_conv]) if col_conv is not None and col_conv < len(row) else None,
            })

        records.append(rec)

    return records


# ---------------------------------------------------------------------------
# 5. 派生指标
# ---------------------------------------------------------------------------

def compute_metrics(rec):
    """为单条记录计算 Top1/Top3 点击份额、转化份额、Top3 转化率。"""
    ranked = rec.get("ranked", [])
    by_rank = {r["rank"]: r for r in ranked}

    top1_click = by_rank.get(1, {}).get("click_share")
    top1_conv = by_rank.get(1, {}).get("conversion_share")

    clicks = [r.get("click_share") for r in ranked if r.get("click_share") is not None]
    convs = [r.get("conversion_share") for r in ranked if r.get("conversion_share") is not None]

    top3_click = round(sum(clicks), 2) if clicks else None
    top3_conv = round(sum(convs), 2) if convs else None

    # Top3 转化率 ~ Top3 转化份额 / Top3 点击份额（代理指标，反映点击转化效率）
    top3_conv_rate = None
    if top3_click and top3_click > 0 and top3_conv is not None:
        top3_conv_rate = round(top3_conv / top3_click * 100.0, 2)

    rec["metrics"] = {
        "top1_click_share": top1_click,
        "top3_click_share": top3_click,
        "top1_conversion_share": top1_conv,
        "top3_conversion_share": top3_conv,
        "top3_conversion_rate": top3_conv_rate,
        "click_concentration": top1_click,  # Top1 点击份额即点击集中度近似
    }
    return rec


# ---------------------------------------------------------------------------
# 6. 品牌词判定 & 修饰词挖掘
# ---------------------------------------------------------------------------

def build_brand_vocab(records):
    """从 Top Clicked Brand 收集品牌词表（归一化 token），叠加种子品牌。"""
    vocab = set(SEED_BRANDS)
    for rec in records:
        b = rec.get("top_clicked_brand")
        if b:
            for tok in TOKEN_RE.findall(b.lower()):
                if len(tok) >= 2:
                    vocab.add(tok)
    return vocab


def is_brand_keyword(term, brand_vocab):
    """搜索词是否包含已知品牌 token。"""
    toks = set(TOKEN_RE.findall(term.lower()))
    return bool(toks & brand_vocab)


def tokenize(term):
    return [t.lower() for t in TOKEN_RE.findall(term)]


def extract_modifiers(records, top_n=40):
    """
    高频修饰词提取：
      - 对所有（非品牌）搜索词分词
      - 剔除停用词、纯数字、品牌 token
      - 基础品类词单独标记（不直接删除，给 weight 降权信息）
    返回 [(word, count), ...]。
    """
    counter = Counter()
    for rec in records:
        if rec.get("is_brand"):
            continue
        for tok in tokenize(rec["search_term"]):
            if tok in STOPWORDS:
                continue
            if NUM_RE.match(tok):
                continue
            if len(tok) < 3:
                continue
            counter[tok] += 1
    # 基础品类词降权（不直接删，标注出来）
    most = counter.most_common(top_n * 2)
    modifiers = []
    base = []
    for w, c in most:
        if w in BASE_PRODUCT_WORDS:
            base.append({"word": w, "count": c, "is_base_product": True})
        else:
            modifiers.append({"word": w, "count": c, "is_base_product": False})
    return modifiers[:top_n], base[:20]


# ---------------------------------------------------------------------------
# 7. 汇总
# ---------------------------------------------------------------------------

def summarize(records, meta, brand_vocab):
    # 标记品牌词
    for rec in records:
        rec["is_brand"] = is_brand_keyword(rec["search_term"], brand_vocab)
        compute_metrics(rec)

    brand_kws = [r for r in records if r["is_brand"]]
    non_brand_kws = [r for r in records if not r["is_brand"]]

    # Top Brands 统计（出现频次）
    brand_counter = Counter()
    for r in records:
        if r.get("top_clicked_brand"):
            brand_counter[r["top_clicked_brand"]] += 1

    # Top ASINs 统计（Top1 ASIN 出现频次 + 标题）
    asin_counter = Counter()
    asin_title = {}
    for r in records:
        for rk in r["ranked"]:
            a = rk.get("asin")
            if a:
                asin_counter[a] += 1
                if rk.get("title") and a not in asin_title:
                    asin_title[a] = rk["title"]

    modifiers, base_words = extract_modifiers(records)

    # 平均点击份额 / 平均转化率
    click_vals = [r["metrics"]["top1_click_share"] for r in records if r["metrics"]["top1_click_share"] is not None]
    conv_rate_vals = [r["metrics"]["top3_conversion_rate"] for r in records if r["metrics"]["top3_conversion_rate"] is not None]
    avg_click = round(sum(click_vals) / len(click_vals), 2) if click_vals else None
    avg_conv_rate = round(sum(conv_rate_vals) / len(conv_rate_vals), 2) if conv_rate_vals else None

    summary = {
        "meta": meta,
        "total_keywords": len(records),
        "brand_keyword_count": len(brand_kws),
        "non_brand_keyword_count": len(non_brand_kws),
        "avg_top1_click_share": avg_click,
        "avg_top3_conversion_rate": avg_conv_rate,
        "modifier_words": modifiers,
        "base_product_words": base_words,
        "top_brands": [{"brand": b, "count": c} for b, c in brand_counter.most_common(20)],
        "top_asins": [{"asin": a, "count": c, "title": asin_title.get(a)} for a, c in asin_counter.most_common(20)],
        "non_brand_keywords": [
            {
                "search_term": r["search_term"],
                "rank": r["search_frequency_rank"],
                "category": r.get("top_clicked_category"),
                "top1_click_share": r["metrics"]["top1_click_share"],
                "top3_click_share": r["metrics"]["top3_click_share"],
                "top3_conversion_rate": r["metrics"]["top3_conversion_rate"],
            }
            for r in sorted(non_brand_kws, key=lambda x: (x["search_frequency_rank"] is None, x["search_frequency_rank"] or 1e12))
        ],
        "brand_keywords": [
            {"search_term": r["search_term"], "rank": r["search_frequency_rank"], "brand": r.get("top_clicked_brand")}
            for r in sorted(brand_kws, key=lambda x: (x["search_frequency_rank"] is None, x["search_frequency_rank"] or 1e12))
        ],
        "records": records,  # 完整明细，供 Agent 聚类/打分
    }
    return summary


# ---------------------------------------------------------------------------
# 8. 控制台摘要打印
# ---------------------------------------------------------------------------

def print_console_summary(s, top=30):
    def line(c="-"):
        print(c * 64)

    line("=")
    print("ABA Top Search Terms 解析摘要")
    line("=")
    if s.get("meta"):
        for k, v in s["meta"].items():
            if k == "_raw":
                continue
            print(f"  {k}: {v}")
        line()
    print(f"总关键词数        : {s['total_keywords']}")
    print(f"品牌词数          : {s['brand_keyword_count']}")
    print(f"非品牌词数        : {s['non_brand_keyword_count']}")
    print(f"平均 Top1 点击份额: {s['avg_top1_click_share']}%")
    print(f"平均 Top3 转化率  : {s['avg_top3_conversion_rate']}%")
    line()

    print("高频修饰词 (Top 20):")
    for m in s["modifier_words"][:20]:
        print(f"   {m['word']:<20} x{m['count']}")
    line()

    print("Top 品牌 (按出现频次):")
    for b in s["top_brands"][:10]:
        print(f"   {b['brand']:<28} x{b['count']}")
    line()

    print("Top ASIN (按出现频次):")
    for a in s["top_asins"][:10]:
        t = (a["title"] or "")[:40]
        print(f"   {a['asin']:<12} x{a['count']}  {t}")
    line()

    print(f"Top 非品牌搜索词 (按搜索排名, 前 {top}):")
    for r in s["non_brand_keywords"][:top]:
        rk = r["rank"] if r["rank"] is not None else "-"
        cs = r["top1_click_share"]
        cs = f"{cs}%" if cs is not None else "-"
        print(f"   #{str(rk):<7} {r['search_term'][:38]:<40} 点击{cs}")
    line("=")


# ---------------------------------------------------------------------------
# 9. main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="解析 ABA Top Search Terms CSV")
    ap.add_argument("csv_path", help="ABA Top Search Terms CSV 文件路径")
    ap.add_argument("--out", default=None, help="输出 JSON 路径 (默认: 同目录 aba_parsed.json)")
    ap.add_argument("--top", type=int, default=30, help="控制台展示的 Top 非品牌词数量")
    args = ap.parse_args()

    if not os.path.isfile(args.csv_path):
        print(f"[错误] 文件不存在: {args.csv_path}", file=sys.stderr)
        sys.exit(2)

    try:
        rows, enc, delim = read_rows(args.csv_path)
    except Exception as e:
        print(f"[错误] 读取 CSV 失败: {e}", file=sys.stderr)
        sys.exit(2)

    if not rows or len(rows) < 2:
        print("[错误] CSV 内容为空或行数不足，无法解析。", file=sys.stderr)
        sys.exit(2)

    try:
        meta, header_idx, headers = detect_header_and_meta(rows)
        records = parse_records(rows, header_idx, headers)
    except ValueError as e:
        print(f"[错误] 格式异常: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"[错误] 解析失败: {e}", file=sys.stderr)
        sys.exit(3)

    if len(records) == 0:
        print("[错误] 未解析到任何有效搜索词数据行。请检查 CSV 是否为 ABA Top Search Terms 导出。", file=sys.stderr)
        sys.exit(3)

    if len(records) < 20:
        print(f"[警告] 仅解析到 {len(records)} 个关键词，样本偏少，聚类与选品结论可信度有限。", file=sys.stderr)

    brand_vocab = build_brand_vocab(records)
    summary = summarize(records, meta, brand_vocab)

    out_path = args.out or os.path.join(os.path.dirname(os.path.abspath(args.csv_path)), "aba_parsed.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[错误] 写入 JSON 失败: {e}", file=sys.stderr)
        sys.exit(4)

    print_console_summary(summary, top=args.top)
    print(f"\n[完成] 已解析 (编码={enc}, 分隔符='{delim}')，JSON 已写入: {out_path}")
    print(f"[提示] Agent 下一步：读取该 JSON 的 non_brand_keywords / modifier_words 做语义聚类。")


if __name__ == "__main__":
    main()
