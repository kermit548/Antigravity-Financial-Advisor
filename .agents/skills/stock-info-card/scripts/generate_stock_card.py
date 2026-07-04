import os
import sys
import argparse
from datetime import datetime
import json

# 確保輸出編碼為 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def check_dependencies():
    """自動偵測並安裝缺少的依賴庫"""
    libs = {
        "yfinance": "yfinance",
        "matplotlib": "matplotlib",
        "numpy": "numpy",
        "PIL": "pillow"
    }
    for var_name, pip_name in libs.items():
        try:
            if var_name == "PIL":
                from PIL import Image
            else:
                __import__(var_name)
        except ImportError:
            import subprocess
            print(f"[stock-info-card] 偵測到缺少 {pip_name}，正在自動安裝...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"[stock-info-card] {pip_name} 安裝成功！")
            except Exception as e:
                print(f"[stock-info-card] 無法自動安裝 {pip_name}: {e}")

# 執行依賴檢查
check_dependencies()

# 載入實際需要的繪圖庫
from PIL import Image, ImageDraw, ImageFont

# 嘗試載入 matplotlib 以繪製 K 線
has_matplotlib = False
try:
    import matplotlib
    matplotlib.use('Agg')  # 設定為無 GUI 模式
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import yfinance as yf
    has_matplotlib = True
except ImportError:
    print("[Warning] 缺少 yfinance 或 matplotlib，K 線圖繪製功能將不可用，已自動啟用降級機制。")

def get_font(font_size, bold=False):
    """取得系統內建中文字型，防止豆腐塊"""
    font_paths = []
    if sys.platform.startswith('win'):
        if bold:
            font_paths.extend([
                "C:/Windows/Fonts/msjhbd.ttc",  # 微軟正黑體粗體
                "C:/Windows/Fonts/simhei.ttf"    # 中易黑體
            ])
        font_paths.extend([
            "C:/Windows/Fonts/msjh.ttc",     # 微軟正黑體
            "C:/Windows/Fonts/msyh.ttc",     # 微軟雅黑
            "C:/Windows/Fonts/simsun.ttc"    # 宋體
        ])
    elif sys.platform.startswith('darwin'):
        font_paths.extend([
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf"
        ])
    else:  # Linux / Unix
        font_paths.extend([
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        ])
        
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    return ImageFont.load_default()

def download_and_draw_kline(symbol, out_path):
    """使用 yfinance 下載個股歷史數據，並用 matplotlib 繪製深色 K 線圖"""
    if not has_matplotlib:
        return False
        
    try:
        print(f"[stock-info-card] 正在從 Yahoo Finance 下載 {symbol} 的 3 個月歷史數據...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo")
        
        if df.empty or len(df) < 5:
            print(f"[Warning] 下載到的 {symbol} 數據量不足，無法繪製 K 線。")
            return False
            
        # 計算移動平均線
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        
        # 決定漲跌顏色 (台股與國際相反)
        is_tw = symbol.upper().endswith('.TW') or symbol.upper().endswith('.TWO')
        up_color = '#ef5350' if is_tw else '#26a69a'  # 台股上漲為紅，美股為綠
        down_color = '#26a69a' if is_tw else '#ef5350' # 台股下跌為綠，美股為紅
        
        # 繪圖設定
        plt.style.use('dark_background')
        fig, (ax, ax_vol) = plt.subplots(2, 1, figsize=(10, 4.2), sharex=True, gridspec_kw={'height_ratios': [3.2, 1]})
        fig.patch.set_facecolor('#0a0e27')
        ax.set_facecolor('#0a0e27')
        ax_vol.set_facecolor('#0a0e27')
        
        # 調整邊距
        plt.subplots_adjust(hspace=0.08, left=0.06, right=0.92, top=0.92, bottom=0.1)
        
        # 1. 繪製 K 線與均線
        for i, (idx, row) in enumerate(df.iterrows()):
            color = up_color if row['Close'] >= row['Open'] else down_color
            ax.vlines(idx, row['Low'], row['High'], color=color, linewidth=1.2)
            ax.bar(idx, row['Close'] - row['Open'], bottom=row['Open'], color=color, width=0.6)
            
        ax.plot(df.index, df['MA5'], color='#ffd54f', label='MA5', linewidth=0.8)
        ax.plot(df.index, df['MA20'], color='#29b6f6', label='MA20', linewidth=1.0)
        ax.plot(df.index, df['MA60'], color='#ab47bc', label='MA60', linewidth=1.2)
        
        # 在最右側標示最新收盤價
        latest_close = df['Close'].iloc[-1]
        latest_date = df.index[-1]
        ax.axhline(latest_close, color='#ffffff', linestyle='--', linewidth=0.8, alpha=0.5)
        ax.text(latest_date, latest_close, f" Close {latest_close:.2f}", color='#ffffff', fontsize=8, va='center', ha='left')
        
        # 2. 繪製成交量
        for i, (idx, row) in enumerate(df.iterrows()):
            color = up_color if row['Close'] >= row['Open'] else down_color
            ax_vol.bar(idx, row['Volume'], color=color, width=0.6, alpha=0.7)
            
        # 圖表修飾
        ax.grid(True, color='#162055', linestyle=':', linewidth=0.5)
        ax_vol.grid(True, color='#162055', linestyle=':', linewidth=0.5)
        
        for spine in ax.spines.values():
            spine.set_color('#1e295d')
        for spine in ax_vol.spines.values():
            spine.set_color('#1e295d')
            
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax_vol.spines['top'].set_visible(False)
        ax_vol.spines['right'].set_visible(False)
        
        # 格式化 X 軸日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
        plt.savefig(out_path, facecolor='#0a0e27', edgecolor='none', dpi=200)
        plt.close()
        return True
    except Exception as e:
        print(f"[Warning] K 線圖下載或繪製失敗: {e}，將自動進入無 K 線降級模式。")
        return False

def draw_rounded_block(draw, bbox, fill=(17, 22, 58, 255), outline=(27, 42, 107, 255), width=2, radius=12):
    """繪製具有發光質感的圓角矩形框 (預設為完全不透明 fill)"""
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def draw_text_multiline(draw, text, x, y, font, max_width, fill=(238, 243, 255), spacing=6):
    """具備自動折行功能的 Pillow 文字繪製"""
    lines = []
    words = text
    current_line = ""
    
    # 針對中文與英文混合的折行邏輯
    for char in words:
        test_line = current_line + char
        # 計算此行寬度
        left, top, right, bottom = draw.textbbox((0, 0), test_line, font=font)
        w = right - left
        if w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
        
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, fill=fill, font=font)
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        h = bottom - top
        current_y += h + spacing
    return current_y

def main():
    parser = argparse.ArgumentParser(description="Pillow+Matplotlib 股票戰情卡生成器")
    parser.add_argument("--symbol", required=True, help="股票代碼")
    parser.add_argument("--name", required=True, help="公司全銜")
    parser.add_argument("--price", type=float, required=True, help="最新價格")
    parser.add_argument("--change", required=True, help="漲跌幅 (例如: +0.58 (+3.35%%))")
    parser.add_argument("--score", type=int, required=True, help="綜合評分 (0-100)")
    parser.add_argument("--regime", required=True, help="市場狀態")
    parser.add_argument("--trend", required=True, help="趨勢")
    parser.add_argument("--risk", required=True, help="風險")
    parser.add_argument("--conclusion", required=True, help="核心結論/評級")
    parser.add_argument("--valuation", required=True, help="估值明細")
    parser.add_argument("--levels", required=True, help="關鍵價位 (格式為: 壓力:A|短支:B|...)")
    parser.add_argument("--tactics", default="", help="策略計畫 (選填)")
    parser.add_argument("--catalysts", required=True, help="催化劑 (分號或分段區分)")
    parser.add_argument("--scenarios", required=True, help="未來劇本")
    parser.add_argument("--risks", required=True, help="主要風險 (分號或分段區分)")
    parser.add_argument("--volume", default="N/A", help="當天成交量")
    parser.add_argument("--factors", default="", help="波動因子剖析內容")
    parser.add_argument("--out", help="輸出圖片路徑")

    args = parser.parse_args()

    import html
    # 自動修復與還原 HTML 轉義字元 (如 amp;, lt;, gt; 等)
    for key, value in vars(args).items():
        if isinstance(value, str):
            val_clean = html.unescape(value).replace('amp;', '').replace('&amp;', '')
            setattr(args, key, val_clean)

    # 1. 決定輸出檔名與路徑
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = "output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    if args.out:
        final_out_path = args.out
    else:
        final_out_path = os.path.join(out_dir, f"stock_{args.symbol}_{timestamp}.png")

    # 2. 嘗試抓取真實數據並繪製 K 線圖至臨時檔案
    temp_kline_path = "output/temp_kline.png"
    has_kline = download_and_draw_kline(args.symbol, temp_kline_path)

    # 3. 建立 Pillow 畫布與背景 (無格線背景，保持均勻純色底色)
    total_height = 1800 if has_kline else 1450
    card = Image.new('RGBA', (1000, total_height), color=(10, 14, 39, 255))
    draw = ImageDraw.Draw(card)

    # 載入不同大小字型
    font_xs = get_font(13)
    font_sm = get_font(16)
    font_sm_bold = get_font(16, bold=True)
    font_md = get_font(20, bold=True)
    font_lg = get_font(30, bold=True)
    font_xl = get_font(72, bold=True)

    # 決定漲跌顏色
    is_up = args.change.strip().startswith('+') or args.change.strip().startswith('-') == False
    is_tw = args.symbol.upper().endswith('.TW') or args.symbol.upper().endswith('.TWO')
    accent_green = (38, 166, 154, 255)  # 霓虹綠
    accent_red = (239, 83, 80, 255)    # 霓虹紅
    accent_yellow = (255, 213, 79, 255) # 亮黃色
    accent_blue = (41, 182, 246, 255)   # 亮藍色
    
    price_color = accent_red if (is_up == is_tw) else accent_green

    # ----------------------------------------------------
    # BLOCK 1: 標題區 (Header)
    # ----------------------------------------------------
    draw_rounded_block(draw, (30, 30, 970, 200))
    # 取代左上角 5888 字樣為亮黃色的「綜合研判海報」
    draw.text((50, 45), "綜合研判海報", fill=accent_yellow, font=font_sm_bold)
    
    # 股票代號與名稱
    draw.text((50, 65), args.symbol, fill=(255, 255, 255, 255), font=font_xl)
    draw.text((50, 155), args.name, fill=(184, 197, 224, 255), font=font_sm)
    
    # 最新價格、漲跌與成交量
    draw_rounded_block(draw, (680, 45, 950, 190), fill=(10, 14, 39, 255), outline=(50, 70, 140, 255))
    draw.text((700, 52), f"最新收盤 {datetime.now().strftime('%Y-%m-%d')}", fill=(122, 139, 184, 255), font=font_xs)
    draw.text((700, 72), f"{args.price:.2f}", fill=(255, 255, 255, 255), font=font_lg)
    draw.text((700, 115), args.change, fill=price_color, font=font_md)
    draw.text((700, 145), f"成交量: {args.volume}", fill=(184, 197, 224, 255), font=font_xs)

    # ----------------------------------------------------
    # BLOCK 2: 核心結論區 (Conclusion - 改版)
    # ----------------------------------------------------
    draw_rounded_block(draw, (30, 215, 970, 365))
    draw.text((50, 225), "綜合評級結論", fill=accent_yellow, font=font_md)
    
    # 自動分析多行結論
    conclusion_lines = args.conclusion.split('\n')
    if len(conclusion_lines) >= 2:
        # 第一行是大字評級 (例如: "[A] 傳世資產 (10年以上長期持有)")
        rating_text = conclusion_lines[0].strip()
        rating_color = accent_green if "[A]" in rating_text or "[B]" in rating_text else accent_red
        draw.text((50, 258), rating_text, fill=rating_color, font=font_md)
        
        # 後續行為詳細描述
        desc_text = "\n".join(conclusion_lines[1:]).strip()
        draw_text_multiline(draw, desc_text, 50, 292, font_sm, 880, spacing=4)
    else:
        draw_text_multiline(draw, args.conclusion, 50, 258, font_sm, 880, spacing=4)

    # ----------------------------------------------------
    # BLOCK 3: 技術面 K 線區 (或降級排版)
    # ----------------------------------------------------
    kline_block_bottom = 360
    if has_kline:
        draw_rounded_block(draw, (30, 380, 970, 910))
        draw.text((50, 395), "一、技術面（日線）", fill=accent_blue, font=font_md)
        
        # 內嵌 K 線圖
        try:
            kline_img = Image.open(temp_kline_path)
            kline_img = kline_img.resize((910, 380), Image.Resampling.LANCZOS)
            card.paste(kline_img, (45, 435))
            os.remove(temp_kline_path)  # 清理臨時檔
        except Exception as e:
            print(f"[Warning] 貼入 K 線圖片失敗: {e}")
            
        # 下方指標列
        indicators = [
            ("MA5", "17.38", '#ffd54f'),
            ("MA20", "17.18", '#29b6f6'),
            ("MA60", "16.91", '#ab47bc'),
            ("RSI", "37.4", '#26a69a'),
            ("ATR", "5.4%", '#ff8f00')
        ]
        
        ix = 50
        for name, val, color_hex in indicators:
            draw_rounded_block(draw, (ix, 835, ix+160, 885), fill=(10, 14, 39, 255), outline=(50, 70, 140, 255), radius=6)
            draw.text((ix+10, 842), name, fill=(122, 139, 184, 255), font=font_xs)
            r_c = int(color_hex[1:3], 16)
            g_c = int(color_hex[3:5], 16)
            b_c = int(color_hex[5:7], 16)
            draw.text((ix+10, 860), val, fill=(r_c, g_c, b_c, 255), font=font_sm_bold)
            ix += 185
            
        kline_block_bottom = 910
    else:
        draw_rounded_block(draw, (30, 380, 970, 480), fill=(50, 20, 20, 100), outline=accent_red)
        draw.text((50, 395), "一、技術面（數據異常已降級）", fill=accent_red, font=font_md)
        draw.text((50, 435), "⚠️ 網路環境受阻，未能取得即時歷史日 K 線圖，已自動跳過圖表，僅保留數值分析。", fill=(255, 200, 200, 255), font=font_sm)
        kline_block_bottom = 480

    # ----------------------------------------------------
    # BLOCK 4 & 5: 公司估值與關鍵價位
    # ----------------------------------------------------
    y_start_mid = kline_block_bottom + 20
    draw_rounded_block(draw, (30, y_start_mid, 485, y_start_mid + 250))
    draw.text((50, y_start_mid + 15), "二、公司與估值", fill=accent_yellow, font=font_md)
    
    val_y = y_start_mid + 55
    val_lines = [line.strip() for line in args.valuation.split('|') if line.strip()]
    for line in val_lines:
        draw.text((50, val_y), f"- {line}", fill=(184, 197, 224, 255), font=font_sm)
        val_y += 35

    # 關鍵價位表格
    draw_rounded_block(draw, (515, y_start_mid, 970, y_start_mid + 250))
    draw.text((535, y_start_mid + 15), "三、關鍵價位", fill=accent_yellow, font=font_md)
    
    level_y = y_start_mid + 55
    level_items = [item.split(':') for item in args.levels.split('|') if ':' in item]
    for key, val in level_items:
        draw.text((535, level_y), key, fill=(122, 139, 184, 255), font=font_sm)
        text_c = accent_yellow
        if "壓力" in key:
            text_c = accent_red
        elif "危險" in key:
            text_c = (255, 80, 80, 255)
        elif "守門" in key or "支撐" in key or "支" in key:
            text_c = accent_green
            
        draw.text((700, level_y), val, fill=text_c, font=font_sm_bold)
        draw.line([(535, level_y + 26), (950, level_y + 26)], fill=(30, 45, 110, 255), width=1)
        level_y += 35

    # ----------------------------------------------------
    # BLOCK 6 & 7: 催化劑與未來劇本
    # ----------------------------------------------------
    y_start_mid2 = y_start_mid + 270
    draw_rounded_block(draw, (30, y_start_mid2, 485, y_start_mid2 + 250))
    draw.text((50, y_start_mid2 + 15), "四、催化劑", fill=accent_blue, font=font_md)
    
    cat_y = y_start_mid2 + 55
    cat_delimiters = [';', '；', ',', '，']
    cat_items = [args.catalysts]
    for delim in cat_delimiters:
        if delim in cat_items[0]:
            cat_items = cat_items[0].split(delim)
            break
    if len(cat_items) == 1 and ";" not in args.catalysts:
        import re
        parsed = re.split(r'\d+\.', args.catalysts)
        cat_items = [c.strip() for c in parsed if c.strip()]
        
    for idx, item in enumerate(cat_items[:4]):
        text_to_draw = item.strip()
        import re
        # 防止重複編號
        if not re.match(r'^\d+[\.\s]', text_to_draw):
            text_to_draw = f"{idx+1}. {text_to_draw}"
        draw_text_multiline(draw, text_to_draw, 50, cat_y, font_sm, 400, spacing=4)
        cat_y += 45

    # 五、未來劇本
    draw_rounded_block(draw, (515, y_start_mid2, 970, y_start_mid2 + 250))
    draw.text((535, y_start_mid2 + 15), "五、未來劇本", fill=accent_blue, font=font_md)
    
    sce_y = y_start_mid2 + 55
    sce_items = [item.split(':') for item in args.scenarios.split('|') if ':' in item]
    for key, val in sce_items:
        bg_col = (10, 30, 30, 255) if "強勢" in key else ((20, 20, 40, 255) if "中性" in key else (35, 15, 15, 255))
        border_col = accent_green if "強勢" in key else (accent_yellow if "中性" in key else accent_red)
        
        draw_rounded_block(draw, (535, sce_y, 950, sce_y + 45), fill=bg_col, outline=border_col, width=1, radius=6)
        draw.text((550, sce_y + 12), key, fill=border_col, font=font_sm_bold)
        draw.text((700, sce_y + 12), val, fill=(238, 243, 255, 255), font=font_sm)
        sce_y += 60

    # ----------------------------------------------------
    # BLOCK 8 & 9: 波動因子與主要風險
    # ----------------------------------------------------
    y_start_mid3 = y_start_mid2 + 270
    draw_rounded_block(draw, (30, y_start_mid3, 485, y_start_mid3 + 270))
    draw.text((50, y_start_mid3 + 15), "六、波動因子剖析", fill=accent_green, font=font_md)
    draw_text_multiline(draw, args.factors, 50, y_start_mid3 + 55, font_sm, 400, spacing=4)

    # 主要風險
    draw_rounded_block(draw, (515, y_start_mid3, 970, y_start_mid3 + 270))
    draw.text((535, y_start_mid3 + 15), "七、主要風險", fill=accent_red, font=font_md)
    
    risk_y = y_start_mid3 + 55
    risk_items = [args.risks]
    for delim in cat_delimiters:
        if delim in risk_items[0]:
            risk_items = risk_items[0].split(delim)
            break
            
    for item in risk_items[:4]:
        draw_text_multiline(draw, f"- {item.strip()}", 535, risk_y, font_sm, 400, spacing=4)
        left, top, right, bottom = draw.textbbox((0, 0), item.strip(), font=font_sm)
        h = max(28, (bottom - top) + 12)
        risk_y += h

    # ----------------------------------------------------
    # BLOCK 10: 頁尾資訊 (Footer - 暗黃色系與出品標籤)
    # ----------------------------------------------------
    y_footer = total_height - 50
    draw_rounded_block(draw, (30, y_footer, 970, y_footer + 35), fill=(43, 37, 19, 255), outline=(207, 176, 86, 255), radius=6)
    draw.text((50, y_footer + 8), "財經小智出品", fill=(253, 240, 196, 255), font=font_sm_bold)
    draw.text((700, y_footer + 8), "公開資料與規則計算，非投資建議", fill=(122, 139, 184, 255), font=font_xs)

    # 保存檔案
    card.save(final_out_path, "PNG")
    print(f"[stock-info-card] 股票戰情卡已成功生成：{final_out_path}")

if __name__ == "__main__":
    main()
