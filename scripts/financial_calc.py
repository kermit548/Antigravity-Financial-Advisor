import sys
import argparse
from datetime import datetime
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Ensure output encoding is UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def set_cell_background(cell, fill_hex):
    """Set the background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def calculate_projection(savings, rate, duration):
    """Calculate compound interest projection."""
    r = rate / 100.0
    balance = 0
    records = []
    
    for year in range(1, duration + 1):
        interest = balance * r
        balance = (balance + savings) * (1 + r)
        records.append({
            "year": year,
            "savings": savings,
            "interest": interest,
            "balance": balance
        })
        
    return balance, records

def create_report(client, target, duration, rate, savings, out_path):
    final_balance, records = calculate_projection(savings, rate, duration)
    
    # Calculate 4% drawdown rule
    annual_drawdown = final_balance * 0.04
    monthly_drawdown = annual_drawdown / 12.0
    
    doc = Document()
    
    # Page margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("全球資產配置與退休理財規劃建議書")
    run_title.font.name = "DFKai-SB"
    run_title.font.size = Pt(22)
    run_title.bold = True
    
    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run(f"客戶：{client} 先生/女士  |  規劃日期：{datetime.now().strftime('%Y/%m/%d')}")
    run_sub.font.name = "PMingLiU"
    run_sub.font.size = Pt(12)
    
    doc.add_paragraph()
    
    # Section 1: Target Summary
    h1 = doc.add_paragraph()
    run_h1 = h1.add_run("一、 退休理財規劃摘要")
    run_h1.bold = True
    run_h1.font.size = Pt(16)
    run_h1.font.name = "DFKai-SB"
    
    p_desc = doc.add_paragraph()
    p_desc.add_run(
        f"本規劃書旨在為您進行長期退休金流模擬。根據您的設定，每年固定投入新台幣 {savings:,.0f} 元，"
        f"在預期年化報酬率 {rate:.2f}% 下進行投資，預計規劃期程為 {duration} 年。"
    ).font.name = "PMingLiU"
    
    # Summary Table
    sum_table = doc.add_table(rows=3, cols=2)
    sum_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    headers = [
        ("規劃參數項目", "試算規劃結果"),
        ("期末累積資產總額", f"NT$ {final_balance:,.0f} 元"),
        ("退休金流 (4% 提領率試算)", f"每年可提領 NT$ {annual_drawdown:,.0f} 元 (相當於每月 NT$ {monthly_drawdown:,.0f} 元)")
    ]
    
    for i, (k, v) in enumerate(headers):
        row = sum_table.rows[i]
        row.cells[0].width = Inches(2.5)
        row.cells[1].width = Inches(3.9)
        
        # Key cell
        c0 = row.cells[0]
        p0 = c0.paragraphs[0]
        run0 = p0.add_run(k)
        run0.font.name = "PMingLiU"
        run0.font.size = Pt(11)
        if i == 0:
            set_cell_background(c0, "003366") # Navy
            run0.font.color.rgb = None
            run0.bold = True
            p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            set_cell_background(c0, "F2F2F2")
            
        # Value cell
        c1 = row.cells[1]
        p1 = c1.paragraphs[0]
        run1 = p1.add_run(v)
        run1.font.name = "PMingLiU"
        run1.font.size = Pt(11)
        if i == 0:
            set_cell_background(c1, "003366")
            run1.bold = True
            p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
    # Set borders for table
    for table in [sum_table]:
        tblPr = table._tbl.tblPr
        tblBorders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), 'CCCCCC')
            tblBorders.append(border)
        tblPr.append(tblBorders)

    doc.add_paragraph()
    
    # Section 2: Asset Allocation Recommendation
    h2 = doc.add_paragraph()
    run_h2 = h2.add_run("二、 全球化資產配置建議")
    run_h2.bold = True
    run_h2.font.size = Pt(16)
    run_h2.font.name = "DFKai-SB"
    
    p_alloc = doc.add_paragraph()
    p_alloc.add_run(
        "基於資產配置指南與風險分散原則，建議將您的退休組合規劃為以下三大部分：\n"
        "1. 核心資產 (60%)：全球股票型基金 / 美股 ETF 與全球投資等級債券。\n"
        "2. 另類投資 (20%)：黃金、大宗商品、房地產信託 (REITs)，用於抗通膨與降低資產相關性。\n"
        "3. 固定收益與結構型商品 (20%)：如保本結構型商品 (SN) 或區間累計配息商品 (DRA) 以鎖定基本收益率。"
    ).font.name = "PMingLiU"
    
    # Table of Year-by-Year projection (first 5 and last 5)
    doc.add_paragraph()
    h3 = doc.add_paragraph()
    run_h3 = h3.add_run("三、 複利資產增長增值表")
    run_h3.bold = True
    run_h3.font.size = Pt(16)
    run_h3.font.name = "DFKai-SB"
    
    proj_table = doc.add_table(rows=1, cols=4)
    proj_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    hdr_cells = proj_table.rows[0].cells
    hdr_names = ["年度", "每年投入 (元)", "當期產生的利息 (元)", "累積資產餘額 (元)"]
    for i, name in enumerate(hdr_names):
        set_cell_background(hdr_cells[i], "003366")
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(name)
        run.bold = True
        run.font.size = Pt(11)
        run.font.name = "PMingLiU"
        
    for r in records:
        # Show all years if duration <= 20, else show first 5 and last 5
        if duration > 20 and (5 < r['year'] < duration - 4):
            if r['year'] == 6:
                row_cells = proj_table.add_row().cells
                for cell in row_cells:
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run("...").font.size = Pt(11)
            continue
            
        row_cells = proj_table.add_row().cells
        data = [
            f"第 {r['year']} 年",
            f"NT$ {r['savings']:,.0f}",
            f"NT$ {r['interest']:,.0f}",
            f"NT$ {r['balance']:,.0f}"
        ]
        for i, val in enumerate(data):
            p = row_cells[i].paragraphs[0]
            if i > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(val)
            run.font.size = Pt(11)
            run.font.name = "PMingLiU"
            
    # Set borders for proj_table
    tblPr = proj_table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), 'CCCCCC')
        tblBorders.append(border)
    tblPr.append(tblBorders)

    # Save
    doc.save(out_path)
    print(f"✓ 成功產出理財規劃建議書：{out_path}")

def main():
    parser = argparse.ArgumentParser(description="財經小智理財建議計算與產檔工具")
    parser.add_argument("--client", required=True, help="客戶姓名")
    parser.add_argument("--target", type=float, default=10000000, help="退休目標資產金額")
    parser.add_argument("--duration", type=int, default=20, help="規劃期程(年)")
    parser.add_argument("--rate", type=float, default=6.0, help="預期年化報酬率(%%)")
    parser.add_argument("--savings", type=float, default=300000, help="每年固定儲蓄金額")
    parser.add_argument("--out", required=True, help="輸出檔案路徑")
    
    args = parser.parse_args()
    
    create_report(
        client=args.client,
        target=args.target,
        duration=args.duration,
        rate=args.rate,
        savings=args.savings,
        out_path=args.out
    )

if __name__ == "__main__":
    main()
