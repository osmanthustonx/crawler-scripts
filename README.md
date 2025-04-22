# crawler-scripts

## GMGN 錢包分析工具

這是一個自動化爬蟲腳本，可以訪問 GMGN.ai 網站並獲取 Solana 錢包的勝率統計和交易記錄。

### Demo

https://github.com/user-attachments/assets/7959a28c-e215-45ad-9c8d-15b4cba798db

### 功能特點

- 自動訪問 GMGN.ai 上指定錢包地址的頁面
- 自動處理網頁操作（關閉彈窗、點擊按鈕等）
- 抓取錢包的統計數據和持倉資訊
- 支持批量分析多個錢包地址
- 可選擇保持瀏覽器開啟以便調試

### 安裝要求

在使用前，需要安裝以下依賴：

```bash
pip install -r requirements.txt
```

主要依賴：

- undetected-chromedriver >= 3.5.0
- selenium >= 4.10

### 使用方法

基本用法：

```bash
python wallet_analysis.py <錢包地址>
```

分析多個錢包：

```bash
python wallet_analysis.py <錢包地址1> <錢包地址2> <錢包地址3> ...
```

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
