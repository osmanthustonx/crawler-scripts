# crawler-scripts

## GMGN 錢包分析工具

這是一個自動化爬蟲腳本，可以訪問 GMGN.ai 網站並獲取 Solana 錢包的勝率統計和交易記錄。現在還支援透過 Telegram Bot 介面輸入錢包地址，並將爬取的數據保存到 Google Sheet 中。

### Demo

https://github.com/user-attachments/assets/7959a28c-e215-45ad-9c8d-15b4cba798db

### 功能特點

- 自動訪問 GMGN.ai 上指定錢包地址的頁面
- 自動處理網頁操作（關閉彈窗、點擊按鈕等）
- 抓取錢包的統計數據和持倉資訊
- 支持批量分析多個錢包地址
- 可選擇保持瀏覽器開啟以便調試
- 透過 Telegram Bot 提供使用者介面
- 將爬取的數據保存到 Google Sheet 中

### 安裝要求

在使用前，需要安裝以下依賴：

```bash
uv venv
source .venv/bin/activate && echo "虛擬環境已激活"

pip install -r requirements.txt
```

或使用 uv 安裝：

```bash
uv venv
source .venv/bin/activate && echo "虛擬環境已激活"

uv pip install -r requirements.txt
```

主要依賴：

- 爬蟲相關：undetected-chromedriver、selenium
- Telegram Bot 相關：python-telegram-bot
- Google Sheet 相關：gspread、oauth2client、google-auth 等
- 環境變數相關：python-dotenv

### 使用方法

#### 直接使用爬蟲腳本

基本用法：

```bash
python wallet_analysis.py <錢包地址>
```

分析多個錢包：

```bash
python wallet_analysis.py <錢包地址1> <錢包地址2> <錢包地址3> ...
```

#### 使用 Telegram Bot

啟動 Bot：

```bash
python bot_main.py
or
source .venv/bin/activate && python bot_main.py
```

然後可以透過 Telegram 與 Bot 互動，發送錢包地址進行分析。

### 命令行參數

- `<錢包地址>`: 一個或多個要分析的 Solana 錢包地址
- `keep_open`: 分析完成後保持瀏覽器開啟（用於調試）
- `clean`: 只輸出乾淨的 JSON 數據，不輸出調試信息

### 使用示例

分析單個錢包地址：

```bash
python wallet_analysis.py 8zab1batbJZZz5MnawzLz3MqkWJBP9LF4AdZCE3y2JJF
```

分析多個錢包地址並保持瀏覽器開啟：

```bash
python wallet_analysis.py 8zab1batbJZZz5MnawzLz3MqkWJBP9LF4AdZCE3y2JJF 4Xky4NEi6rPsLzQxNhZ3JvKnasocUL4cT3x4fso76qxN keep_open
```

只輸出乾淨的 JSON 數據（適合後續處理）：

```bash
python wallet_analysis.py 8zab1batbJZZz5MnawzLz3MqkWJBP9LF4AdZCE3y2JJF clean
```

### 輸出數據

腳本將輸出 JSON 格式的數據，包含每個錢包的：

- wallet_summary: 錢包的統計摘要，包括勝率等信息
- wallet_holdings: 錢包交易過的的代幣信息

如果發生錯誤，將返回錯誤信息。

## Telegram Bot 與 Google Sheet 整合

### 設置步驟

#### 1. 創建 Telegram Bot

1. 在 Telegram 中搜索 [@BotFather](https://t.me/BotFather)
2. 發送 `/newbot` 命令
3. 按照提示設置 Bot 名稱和使用者名稱
4. 獲取 Bot API 令牌
5. 將令牌填入 `.env` 文件的 `TELEGRAM_BOT_TOKEN` 欄位

#### 2. 設置 Google API 憑證

1. 訪問 [Google Cloud Console](https://console.cloud.google.com/)
2. 創建新項目
   - 點擊頂部導航欄中的項目下拉選單
   - 點擊「新建項目」按鈕
   - 輸入項目名稱（例如「Wallet-Analysis-Bot」）
   - 點擊「創建」按鈕

3. 啟用 Google Sheets API
   - 在左側導航欄中，點擊「API 和服務」
   - 點擊「啟用 API 和服務」
   - 搜索「Google Sheets API」並點擊
   - 點擊「啟用」按鈕

4. 啟用 Google Drive API
   - 返回「API 和服務」頁面
   - 點擊「啟用 API 和服務」
   - 搜索「Google Drive API」並點擊
   - 點擊「啟用」按鈕

5. 創建服務帳號
   - 在左側導航欄中，點擊「API 和服務」，然後選擇「憑證」
   - 點擊「創建憑證」按鈕，選擇「服務帳號」
   - 輸入服務帳號名稱和 ID
   - 點擊「創建並繼續」
   - 在「授予此服務帳號對項目的訪問權限」頁面，選擇「基本」→「編輯者」角色
   - 點擊「完成」

6. 創建服務帳號金鑰
   - 在「憑證」頁面，找到剛創建的服務帳號
   - 點擊該服務帳號右側的「操作」按鈕（三個點）
   - 選擇「管理金鑰」
   - 點擊「添加金鑰」→「創建新金鑰」
   - 選擇「JSON」格式
   - 點擊「創建」按鈕，下載 JSON 憑證文件

7. 設置 Google Sheet 權限
   - 創建一個新的 Google Sheet 或使用現有的
   - 點擊右上角的「共享」按鈕
   - 輸入服務帳號的電子郵件地址（在 JSON 文件中的 `client_email` 欄位）
   - 設置權限為「編輯者」
   - 點擊「共享」按鈕

#### 3. 配置環境變數

1. 將下載的 JSON 憑證文件重命名為 `credentials.json` 並移動到項目目錄
2. 編輯 `.env` 文件：

```
# Telegram Bot 令牌
TELEGRAM_BOT_TOKEN="您的Telegram Bot令牌"

# Google API 憑證設置
GOOGLE_CREDENTIALS_PATH="credentials.json"
GOOGLE_SHEET_NAME="Wallet Analysis Results"
```

### 使用 Telegram Bot

啟動 Bot：

```bash
python bot_main.py
```

與 Bot 互動：

1. 在 Telegram 中搜索您創建的 Bot
2. 發送 `/start` 命令開始使用
3. 發送 `/help` 查看幫助信息
4. 發送 `/analyze <錢包地址>` 或直接發送錢包地址進行分析
5. 分析完成後，點擊「保存到 Google Sheet」按鈕將結果保存到 Google Sheet

### Google Sheet 數據格式

數據將按日期保存在不同的工作表中，每個工作表包含以下列：

- 錢包地址
- 爬取時間
- 餘額
- 總價值
- 買入
- 賣出
- 盈虧
- 已實現利潤
- 未實現利潤
- 代幣數量
- 持有代幣

### 故障排除

如果遇到問題，請檢查：

1. Telegram Bot 令牌是否正確
2. Google API 憑證文件是否有效
3. 服務帳號是否有權限訪問 Google Sheet
4. 依賴項是否正確安裝
