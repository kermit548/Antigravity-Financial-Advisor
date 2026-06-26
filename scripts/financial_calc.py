import sys
import argparse
from datetime import datetime

# Ensure output encoding is UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
    
    # Generate premium HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>全球資產配置與退休理財規劃建議書 - {client}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Noto+Sans+TC:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0a0e27;
            --bg-card: rgba(17, 22, 58, 0.7);
            --ink: #eef3ff;
            --ink-secondary: #b8c5e0;
            --accent: #00d4ff;
            --accent-pink: #ff006e;
            --border: rgba(238, 243, 255, 0.15);
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            background-color: var(--bg);
            color: var(--ink);
            font-family: 'Inter', 'Noto Sans TC', sans-serif;
            line-height: 1.6;
            padding: 40px 20px;
            background-image: radial-gradient(circle at 10% 20%, rgba(0, 212, 255, 0.1) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(255, 0, 110, 0.08) 0%, transparent 40%);
            background-attachment: fixed;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 50px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 30px;
        }}
        
        h1 {{
            font-size: 32px;
            font-weight: 900;
            letter-spacing: 2px;
            color: #fff;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #fff 0%, var(--ink-secondary) 50%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .meta-info {{
            font-size: 14px;
            color: var(--ink-secondary);
            font-weight: 300;
        }}
        
        .meta-info span {{
            margin: 0 15px;
            color: var(--accent);
        }}
        
        section {{
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 35px;
            margin-bottom: 40px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }}
        
        h2 {{
            font-size: 21px;
            font-weight: 700;
            margin-bottom: 25px;
            color: var(--accent);
            border-left: 4px solid var(--accent-pink);
            padding-left: 12px;
        }}
        
        p {{
            font-size: 16px;
            color: var(--ink-secondary);
            margin-bottom: 20px;
            font-weight: 300;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 15px;
        }}
        
        th {{
            background-color: rgba(0, 212, 255, 0.1);
            color: var(--accent);
            font-weight: 600;
            text-align: left;
            padding: 14px 18px;
            border-bottom: 2px solid var(--accent);
        }}
        
        td {{
            padding: 14px 18px;
            border-bottom: 1px solid var(--border);
            color: var(--ink-secondary);
            font-weight: 300;
        }}
        
        tr:hover td {{
            color: #fff;
            background-color: rgba(238, 243, 255, 0.02);
        }}
        
        .text-right {{
            text-align: right;
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .highlight {{
            color: #fff;
            font-weight: 600;
        }}
        
        .summary-card {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        
        .card-item {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}
        
        .card-label {{
            font-size: 14px;
            color: var(--ink-secondary);
            margin-bottom: 5px;
        }}
        
        .card-value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--accent);
        }}
        
        .card-desc {{
            font-size: 13px;
            color: var(--ink-secondary);
            margin-top: 5px;
            font-style: italic;
        }}
        
        ul {{
            list-style-type: none;
            margin-left: 10px;
        }}
        
        li {{
            margin-bottom: 12px;
            color: var(--ink-secondary);
            font-weight: 300;
            position: relative;
            padding-left: 20px;
        }}
        
        li::before {{
            content: "▪";
            color: var(--accent-pink);
            position: absolute;
            left: 0;
            top: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>全球資產配置與退休理財規劃建議書</h1>
            <div class="meta-info">
                客戶：<strong>{client} 先生/女士</strong>
                <span>|</span>
                規劃日期：<strong>{datetime.now().strftime('%Y/%m/%d')}</strong>
            </div>
        </header>

        <section>
            <h2>一、 退休理財規劃摘要</h2>
            <p>本建議書旨在為您模擬長期資產複利增值與金流狀況。根據設定，在規劃期間內每年定期定額投入新台幣 {savings:,.0f} 元，以預期年化報酬率 {rate:.2f}% 進行滾存，試算期程為 {duration} 年。</p>
            
            <div class="summary-card">
                <div class="card-item">
                    <div class="card-label">期末累積資產總額</div>
                    <div class="card-value">NT$ {final_balance:,.0f} 元</div>
                </div>
                <div class="card-item">
                    <div class="card-label">退休年領金流 (4% 提領率試算)</div>
                    <div class="card-value">NT$ {annual_drawdown:,.0f} 元</div>
                    <div class="card-desc">相當於每月可彈性支配 NT$ {monthly_drawdown:,.0f} 元</div>
                </div>
            </div>
        </section>

        <section>
            <h2>二、 全球化資產配置建議</h2>
            <p>基於長線資產配置與風險分散考量，建議將您的退休組合重組為以下三大核心區塊：</p>
            <ul>
                <li><strong>核心被動股票資產 (50% - 60%)</strong>：以全球全市場低成本股市 ETF（如 VT 或 VTI 搭配 VXUS）為主，搭配台股市值型 ETF，以極低管理費完整參與全球與台灣經濟實質成長。</li>
                <li><strong>AI 與硬資產進攻衛星 (20% - 30%)</strong>：集中於具備物理產能壟斷與強大定價權的半導體上游龍頭（如台積電 2330、DRAM 板塊），搭配主動式捷豹 ETF（如 00991A）以賺取超級週期的超額 Alpha。</li>
                <li><strong>防禦型與現金流儲備 (10% - 20%)</strong>：包含穩定債息來源（如 00937B 現金流奶牛）、本人名下無時滯之台幣安全墊，以及外部美元安全網，提供斷頭補倉防禦與穩定息收。</li>
            </ul>
        </section>

        <section>
            <h2>三、 複利資產增長增值表</h2>
            <table>
                <thead>
                    <tr>
                        <th class="text-center">年度</th>
                        <th class="text-right">每年投入 (元)</th>
                        <th class="text-right">當期利息收益 (元)</th>
                        <th class="text-right">累積資產餘額 (元)</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for r in records:
        # Show all if duration <= 20, else show first 5 and last 5
        if duration > 20 and (5 < r['year'] < duration - 4):
            if r['year'] == 6:
                html_content += """
                    <tr>
                        <td class="text-center highlight">...</td>
                        <td class="text-right">...</td>
                        <td class="text-right">...</td>
                        <td class="text-right">...</td>
                    </tr>
"""
            continue
            
        html_content += f"""
                    <tr>
                        <td class="text-center highlight">第 {r['year']} 年</td>
                        <td class="text-right">NT$ {r['savings']:,.0f}</td>
                        <td class="text-right">NT$ {r['interest']:,.0f}</td>
                        <td class="text-right highlight">NT$ {r['balance']:,.0f}</td>
                    </tr>
"""
        
    html_content += """
                </tbody>
            </table>
        </section>
    </div>
</body>
</html>
"""
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ 成功產出 HTML 理財建議書：{out_path}")

def main():
    parser = argparse.ArgumentParser(description="財經小智理財建議計算與產檔工具 (HTML版)")
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
