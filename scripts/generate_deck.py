import os
import sys
import argparse
import base64
import io
from datetime import datetime
from PIL import Image

# 確保輸出編碼為 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def calculate_projection(savings, rate, duration):
    """計算複利成長明細"""
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

def get_image_base64(images_dir, name, is_full_bleed=False):
    """尋找圖片，縮放壓縮並轉換為 Base64 Data URI"""
    # 支援尋找 .png 或 .jpg
    path = None
    for ext in [".png", ".jpg", ".jpeg"]:
        test_path = os.path.join(images_dir, f"{name}{ext}")
        if os.path.exists(test_path):
            path = test_path
            break
            
    if not path:
        print(f"Warning: Image file for '{name}' not found in {images_dir}. Using placeholders.")
        # 回傳一個極小的透明 GIF base64 做為佔位符
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        
    try:
        img = Image.open(path).convert('RGB')
        w, h = img.size
        target_w = 1280 if is_full_bleed else 900
        if w > target_w:
            img = img.resize((target_w, int(h * target_w / w)), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, 'JPEG', quality=78, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"Error processing image {path}: {e}")
        return "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

def main():
    parser = argparse.ArgumentParser(description="全球資產配置與退休理財規劃互動簡報編譯工具")
    parser.add_argument("--client", default="測試客戶", help="客戶姓名")
    parser.add_argument("--savings", type=float, default=300000.0, help="每年固定儲蓄金額")
    parser.add_argument("--rate", type=float, default=6.0, help="預期年化報酬率(%%)")
    parser.add_argument("--duration", type=int, default=20, help="規劃期程(年)")
    parser.add_argument("--images_dir", required=True, help="含有簡報插圖的目錄路徑")
    parser.add_argument("--out", required=True, help="輸出簡報 HTML 檔案路徑")
    
    args = parser.parse_args()
    
    # 1. 執行精確複利計算
    final_balance, records = calculate_projection(args.savings, args.rate, args.duration)
    annual_drawdown = final_balance * 0.04
    monthly_drawdown = annual_drawdown / 12.0
    
    # 2. 轉換圖片為 Base64
    image_names = [
        "cover_bg", "pain_point", "compound_effect", "summary_metrics",
        "cashflow_safe", "portfolio_pie", "action_steps", "cta_action"
    ]
    images_b64 = {}
    for name in image_names:
        is_full = (name in ["cover_bg", "cta_action"])
        images_b64[name] = get_image_base64(args.images_dir, name, is_full_bleed=is_full)
        
    # 3. 動態渲染複利表 HTML
    table_rows = ""
    for r in records:
        table_rows += f"""
                            <tr>
                                <td class="text-center highlight">第 {r['year']} 年</td>
                                <td class="text-right">NT$ {r['savings']:,.0f}</td>
                                <td class="text-right">NT$ {r['interest']:,.0f}</td>
                                <td class="text-right highlight">NT$ {r['balance']:,.0f}</td>
                            </tr>"""

    # 4. 組合最終簡報 HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>全球資產配置與退休理財規劃建議書 - {args.client}</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&family=Noto+Sans+TC:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0a0e27;
            --bg-2: #11163a;
            --ink: #eef3ff;
            --ink-2: #b8c5e0;
            --ink-3: #7a8bb8;
            --ink-4: #4a5680;
            --accent: #00d4ff;     /* 霓虹青 */
            --accent-2: #ff006e;   /* 亮粉色 */
            --t1: 52px;
            --t2: 32px;
            --t3: 20px;
            --t4: 13px;
            --s1: 80px;
            --s2: 48px;
            --s3: 24px;
            --s4: 12px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg);
            color: var(--ink);
            font-family: 'Noto Sans TC', sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }}

        /* 頂部進度條 */
        #progress {{
            position: absolute;
            top: 0;
            left: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent) 0%, var(--accent-2) 100%);
            width: 0%;
            transition: width 0.3s ease;
            z-index: 100;
        }}

        /* 左上 SOIL 章節標籤 */
        #section-tag {{
            position: absolute;
            top: 24px;
            left: 32px;
            font-family: 'JetBrains Mono', 'Noto Sans TC', sans-serif;
            font-size: var(--t4);
            color: var(--ink-3);
            letter-spacing: 2px;
            z-index: 100;
            background: rgba(10, 14, 39, 0.6);
            padding: 6px 12px;
            border-radius: 20px;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(238, 243, 255, 0.1);
        }}

        /* 右下頁碼 */
        #pageInfo {{
            position: absolute;
            bottom: 24px;
            right: 32px;
            font-family: 'JetBrains Mono', sans-serif;
            font-size: var(--t4);
            color: var(--ink-3);
            z-index: 100;
            background: rgba(10, 14, 39, 0.6);
            padding: 6px 12px;
            border-radius: 20px;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(238, 243, 255, 0.1);
        }}

        /* 左下快捷鍵提示 */
        #hint {{
            position: absolute;
            bottom: 24px;
            left: 32px;
            font-size: 11px;
            color: var(--ink-4);
            z-index: 100;
            pointer-events: none;
        }}

        /* 簡報頁容器 */
        .slide {{
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 80px 100px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.55s ease, transform 0.55s ease;
            transform: translateY(16px);
            overflow: hidden;
            background-color: var(--bg);
        }}

        .slide.active {{
            opacity: 1;
            pointer-events: auto;
            transform: translateY(0);
        }}

        .slide-inner {{
            width: 100%;
            max-width: 1200px;
            position: relative;
            z-index: 2;
        }}

        /* 滿版背景圖 */
        .full-bleed-bg {{
            position: absolute;
            inset: 0;
            background-size: cover;
            background-position: center;
            z-index: 1;
            filter: brightness(0.35);
        }}

        .full-bleed-overlay {{
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at center, rgba(10, 14, 39, 0.2) 0%, rgba(10, 14, 39, 0.9) 80%);
            z-index: 1;
        }}

        /* 玻璃擬態卡片 */
        .glass-card {{
            background: rgba(17, 22, 58, 0.6);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(238, 243, 255, 0.12);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
        }}

        /* 排版與標題 */
        .kicker {{
            font-family: 'JetBrains Mono', 'Noto Sans TC', sans-serif;
            font-size: var(--t4);
            color: var(--accent-2);
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 12px;
            font-weight: 700;
        }}

        h2.title {{
            font-size: var(--t2);
            font-weight: 900;
            color: #fff;
            margin-bottom: 24px;
            letter-spacing: 1px;
            line-height: 1.2;
        }}

        h2.title span {{
            color: var(--accent);
        }}

        .desc {{
            font-size: var(--t3);
            color: var(--ink-2);
            font-weight: 300;
            line-height: 1.6;
            margin-bottom: 30px;
        }}

        /* 二欄與三欄佈局 */
        .grid-2 {{
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 40px;
            align-items: center;
        }}

        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
        }}

        /* 卡片設計 */
        .feature-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(238, 243, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s ease;
        }}

        .feature-card:hover {{
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--accent);
            transform: translateY(-4px);
        }}

        .feature-card h3 {{
            font-size: var(--t3);
            color: #fff;
            margin-bottom: 12px;
            font-weight: 700;
        }}

        .feature-card p {{
            font-size: var(--t4);
            color: var(--ink-2);
            line-height: 1.6;
        }}

        /* 圖片容器 */
        .slide-img-container {{
            width: 100%;
            height: 380px;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(238, 243, 255, 0.1);
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }}

        .slide-img {{
            width: 100%;
            height: 100%;
            background-size: cover;
            background-position: center;
        }}

        /* 強調大數字 */
        .big-number-box {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin: 20px 0;
        }}

        .big-number {{
            font-size: 64px;
            font-weight: 900;
            color: var(--accent);
            line-height: 1;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            font-family: 'JetBrains Mono', sans-serif;
        }}

        .sub-number {{
            font-size: var(--t2);
            font-weight: 700;
            color: var(--accent-2);
        }}

        /* 表格排版 */
        .table-container {{
            max-height: 340px;
            overflow-y: auto;
            border: 1px solid rgba(238, 243, 255, 0.1);
            border-radius: 12px;
            background: rgba(10, 14, 39, 0.4);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th {{
            background-color: var(--bg-2);
            color: var(--accent);
            font-weight: 600;
            text-align: left;
            padding: 10px 14px;
            border-bottom: 2px solid var(--accent);
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        td {{
            padding: 10px 14px;
            border-bottom: 1px solid rgba(238, 243, 255, 0.08);
            color: var(--ink-2);
        }}

        tr:hover td {{
            color: #fff;
            background-color: rgba(238, 243, 255, 0.03);
        }}

        .text-right {{ text-align: right; }}
        .text-center {{ text-align: center; }}
        .highlight {{ color: #fff; font-weight: 700; }}

        /* 按鈕 */
        .btn {{
            display: inline-block;
            background: linear-gradient(135deg, var(--accent) 0%, #0088cc 100%);
            color: #fff;
            padding: 14px 28px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: 700;
            font-size: 16px;
            letter-spacing: 1px;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
            transition: all 0.3s ease;
            margin-top: 15px;
        }}

        .btn:hover {{
            box-shadow: 0 6px 20px rgba(0, 212, 255, 0.5);
            transform: translateY(-2px);
        }}

        /* 導覽按鈕與點擊切頁熱區 */
        .click-left, .click-right {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 80px;
            z-index: 80;
            cursor: pointer;
        }}
        .click-left {{ left: 0; }}
        .click-right {{ right: 0; }}
    </style>
</head>
<body>
    <div id="progress"></div>
    <div id="section-tag">— 引起動機 —</div>
    <div id="pageInfo">1 / 9</div>
    <div id="hint">← / → 或空白鍵切換 | F 全螢幕</div>

    <!-- 點擊熱區 -->
    <div class="click-left" onclick="prevSlide()"></div>
    <div class="click-right" onclick="nextSlide()"></div>

    <!-- 頁 1: 封面 -->
    <section class="slide active" data-slide="1" data-section="引起動機">
        <div class="full-bleed-bg" style="background-image: url('{images_b64["cover_bg"]}')"></div>
        <div class="full-bleed-overlay"></div>
        <div class="slide-inner" style="text-align: center;">
            <div class="kicker">Financial Advisor Planning</div>
            <h2 class="title" style="font-size: var(--t1); margin-bottom: var(--s2);">退休理財規劃<br><span>全球資產配置建議書</span></h2>
            <div class="desc" style="font-size: var(--t3); color: var(--ink-2); max-width: 800px; margin: 0 auto;">
                客戶：{args.client} 先生/女士 &nbsp;&nbsp;|&nbsp;&nbsp; 規劃日期：{datetime.now().strftime('%Y/%m/%d')}
            </div>
            <button class="btn" onclick="nextSlide()">啟動規劃書簡報</button>
        </div>
    </section>

    <!-- 頁 2: 痛點提問 -->
    <section class="slide" data-slide="2" data-section="引起動機">
        <div class="slide-inner">
            <div class="grid-2">
                <div class="glass-card">
                    <div class="kicker">The Pain Point</div>
                    <h2 class="title">存不夠退不起？<br><span>您的退休缺口有多大</span></h2>
                    <p class="desc">許多人忽略了通膨侵蝕與長壽風險。如果僅依賴現金定存或傳統保單，您的資產實質購買力將每年萎縮。我們需要建立能抗通膨且具備生產力的全球資產組合。</p>
                </div>
                <div class="slide-img-container">
                    <div class="slide-img" style="background-image: url('{images_b64["pain_point"]}')"></div>
                </div>
            </div>
        </div>
    </section>

    <!-- 頁 3: 核心命題 -->
    <section class="slide" data-slide="3" data-section="引起動機">
        <div class="slide-inner">
            <div class="grid-2">
                <div class="slide-img-container">
                    <div class="slide-img" style="background-image: url('{images_b64["compound_effect"]}')"></div>
                </div>
                <div class="glass-card">
                    <div class="kicker">Core Value</div>
                    <h2 class="title">複利雪球效應<br><span>用時間換取資產空間</span></h2>
                    <p class="desc">規劃的精髓在於「早期投入」與「穩定滾存」。每年投入固定儲蓄，以 {args.rate:.1f}% 預期年化報酬率前進，透過 {args.duration} 年的複利飛輪，將能建立足以支撐永續提領的巨大資產池。</p>
                </div>
            </div>
        </div>
    </section>

    <!-- 頁 4: 規劃摘要 -->
    <section class="slide" data-slide="4" data-section="維持注意">
        <div class="slide-inner">
            <div class="grid-2">
                <div class="glass-card">
                    <div class="kicker">Accumulated Wealth</div>
                    <h2 class="title">期末資產總額<br><span>NT$ {final_balance:,.0f} 元</span></h2>
                    <div class="big-number-box">
                        <div class="big-number">{final_balance:,.0f} 元</div>
                        <div class="desc">這是在 {args.duration} 年期間，每年定期儲蓄 NT$ {args.savings:,.0f} 元（總投入 NT$ {args.savings * args.duration:,.0f} 元），以 {args.rate:.1f}% 年複合成長率所滾存出來的最終金額。複利效應創造了顯著的財富增值！</div>
                    </div>
                </div>
                <div class="slide-img-container">
                    <div class="slide-img" style="background-image: url('{images_b64["summary_metrics"]}')"></div>
                </div>
            </div>
        </div>
    </section>

    <!-- 頁 5: 金流試算 -->
    <section class="slide" data-slide="5" data-section="維持注意">
        <div class="slide-inner">
            <div class="grid-2">
                <div class="slide-img-container">
                    <div class="slide-img" style="background-image: url('{images_b64["cashflow_safe"]}')"></div>
                </div>
                <div class="glass-card">
                    <div class="kicker">4% Drawdown Rule</div>
                    <h2 class="title">退休永續金流<br><span>年領 {annual_drawdown:,.0f} 元</span></h2>
                    <div class="big-number-box">
                        <div class="big-number" style="color: var(--accent-2);">NT$ {annual_drawdown:,.0f} / 年</div>
                        <div class="sub-number">相當於每月 NT$ {monthly_drawdown:,.0f} 元</div>
                        <p class="desc" style="font-size: var(--t4); margin-top: 10px;">依據全球經典「4% 提領法則」試算，在此資產水位下，您每年可以安全提領該金額做為生活費，且高機率能實現資產永續不枯竭，提供穩健的下行防禦墊。</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 頁 6: 複利增長表 -->
    <section class="slide" data-slide="6" data-section="維持注意">
        <div class="slide-inner">
            <div class="glass-card">
                <div class="kicker">Historical Projection</div>
                <h2 class="title">資產成長軌跡<span>（{args.duration}年複利明細表）</span></h2>
                <div class="table-container">
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
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </section>

    <!-- 頁 7: 配置建議 -->
    <section class="slide" data-slide="7" data-section="維持注意">
        <div class="slide-inner">
            <div class="grid-2">
                <div class="glass-card">
                    <div class="kicker">Asset Allocation</div>
                    <h2 class="title">全球資產配置建議</h2>
                    <div class="grid-3" style="grid-template-columns: 1fr; gap: 16px;">
                        <div class="feature-card">
                            <h3>1. 核心被動股票 (50% - 60%)</h3>
                            <p>以低成本全球股市 ETF（如 VT, VTI, VXUS）搭配台股市值型 ETF 為基石，完整獲取全球與台灣的實體經濟成長利潤。</p>
                        </div>
                        <div class="feature-card">
                            <h3>2. AI 與硬資產衛星 (20% - 30%)</h3>
                            <p>佈局具備壟斷與強定價權的半導體上游大廠（如台積電 2330），與產業超額利潤 ETF，捕捉未來十年的科技核心 Alpha。</p>
                        </div>
                        <div class="feature-card">
                            <h3>3. 防禦型債息儲備 (10% - 20%)</h3>
                            <p>包含優質高評級債券 ETF（如 00937B）以建立穩定配息金流，並預留無時滯的台幣安全墊，保障極端市場下的流動性。</p>
                        </div>
                    </div>
                </div>
                <div class="slide-img-container" style="height: 480px;">
                    <div class="slide-img" style="background-image: url('{images_b64["portfolio_pie"]}')"></div>
                </div>
            </div>
        </div>
    </section>

    <!-- 頁 8: 執行流程 -->
    <section class="slide" data-slide="8" data-section="喚起行動">
        <div class="slide-inner">
            <div class="glass-card" style="text-align: center;">
                <div class="kicker">Implementation Flow</div>
                <h2 class="title">理財三步出發<span>（落實理財方案）</span></h2>
                <div class="grid-3" style="margin-top: 30px;">
                    <div class="feature-card">
                        <div class="kicker" style="color: var(--accent);">Step 01</div>
                        <h3>設定自動儲蓄</h3>
                        <p>將每月或每年存 NT$ {args.savings:,.0f} 元的儲蓄目標，轉為自動轉帳或定期定額申購，消除人性弱點，落實紀律投資。</p>
                    </div>
                    <div class="feature-card">
                        <div class="kicker" style="color: var(--accent);">Step 02</div>
                        <h3>定期再平衡</h3>
                        <p>每季或每半年檢視資產偏差比例，將漲多的部位獲利了結、補入跌深的資產，讓曝險回歸設定範圍。</p>
                    </div>
                    <div class="feature-card">
                        <div class="kicker" style="color: var(--accent);">Step 03</div>
                        <h3>建立防禦墊</h3>
                        <p>保留 6-12 個月的生活費在定存或高流動性資產中，確保在市場黑天鵝降臨時，不需要被迫變賣投資標的。</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 頁 9: 行動結語 -->
    <section class="slide" data-slide="9" data-section="喚起行動">
        <div class="full-bleed-bg" style="background-image: url('{images_b64["cta_action"]}')"></div>
        <div class="full-bleed-overlay"></div>
        <div class="slide-inner" style="text-align: center;">
            <div class="kicker">Call To Action</div>
            <h2 class="title" style="font-size: var(--t1); margin-bottom: var(--s2);">現在立即啟動<br><span>讓時間與複利為您工作</span></h2>
            <div class="desc" style="max-width: 800px; margin: 0 auto 30px auto;">
                理財規劃最重要的不是預測市場，而是「何時開始」。越早讓資金進入複利飛輪，您的退休金流就越穩固。
            </div>
            <a href="mailto:advisor@fundhot.com" class="btn">聯絡理財顧問諮詢</a>
        </div>
    </section>

    <script>
        let currentSlide = 1;
        const totalSlides = 9;

        function updateSlide() {{
            // 更新 slide 顯示
            document.querySelectorAll('.slide').forEach(s => {{
                s.classList.remove('active');
            }});
            const activeSlide = document.querySelector(`.slide[data-slide="${{currentSlide}}"]`);
            if (activeSlide) {{
                activeSlide.classList.add('active');
                // 更新左上角標籤
                const section = activeSlide.getAttribute('data-section');
                document.getElementById('section-tag').innerText = `— ${{section}} —`;
            }}

            // 更新頁碼
            document.getElementById('pageInfo').innerText = `${{currentSlide}} / ${{totalSlides}}`;

            // 更新進度條
            const percent = ((currentSlide - 1) / (totalSlides - 1)) * 100;
            document.getElementById('progress').style.width = `${{percent}}%`;
        }}

        function nextSlide() {{
            if (currentSlide < totalSlides) {{
                currentSlide++;
                updateSlide();
            }}
        }}

        function prevSlide() {{
            if (currentSlide > 1) {{
                currentSlide--;
                updateSlide();
            }}
        }}

        // 鍵盤控制
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'Enter') {{
                e.preventDefault();
                nextSlide();
            }} else if (e.key === 'ArrowLeft') {{
                e.preventDefault();
                prevSlide();
            }} else if (e.key.toLowerCase() === 'f') {{
                // 全螢幕切換
                if (!document.fullscreenElement) {{
                    document.documentElement.requestFullscreen().catch(err => {{
                        console.log(err);
                    }});
                }} else {{
                    document.exitFullscreen();
                }}
            }}
        }});

        // 初始化
        updateSlide();
    </script>
</body>
</html>
"""

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Success: interactive presentation HTML compiled successfully to: {args.out}")

if __name__ == "__main__":
    main()
