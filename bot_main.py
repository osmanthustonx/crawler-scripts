#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
import logging
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# 導入自定義模組
from wallet_analysis import wallet_analysis
from telegram_bot import WalletAnalysisBot
from google_sheet_manager import GoogleSheetManager

# 設置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 全局變量
executor = ThreadPoolExecutor(max_workers=2)

async def analyze_wallet_async(wallet_address: str) -> Dict[str, Any]:
    """異步分析錢包
    
    Args:
        wallet_address: 錢包地址
        
    Returns:
        分析結果
    """
    loop = asyncio.get_event_loop()
    
    # 在執行器中運行同步函數
    return await loop.run_in_executor(
        executor,
        partial(wallet_analysis, wallet_address, False, True)
    )

async def save_to_sheet_async(
    sheet_manager: GoogleSheetManager,
    wallet_address: str, 
    wallet_data: Dict[str, Any]
) -> Union[str, bool]:
    """異步保存到 Google Sheet
    
    Args:
        sheet_manager: Google Sheet 管理器
        wallet_address: 錢包地址
        wallet_data: 錢包數據
        
    Returns:
        成功返回電子表格 URL，失敗返回 False
    """
    loop = asyncio.get_event_loop()
    
    # 在執行器中運行同步函數
    return await loop.run_in_executor(
        executor,
        sheet_manager.save_wallet_data,
        wallet_address,
        wallet_data
    )

def check_credentials() -> bool:
    """檢查憑證文件是否存在
    
    Returns:
        如果所有必要的憑證都存在，則返回 True
    """
    # 檢查 Telegram Bot 令牌
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        logger.error("未設置 TELEGRAM_BOT_TOKEN 環境變量")
        return False
    
    # 檢查 Google API 憑證
    credentials_path = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    if not os.path.exists(credentials_path):
        logger.error(f"找不到 Google API 憑證文件: {credentials_path}")
        return False
    
    return True

def main() -> None:
    """主函數"""
    # 加載 .env 文件中的環境變數
    load_dotenv()
    
    # 檢查憑證
    if not check_credentials():
        logger.error("缺少必要的憑證，無法啟動機器人")
        print("請確保以下憑證已設置:")
        print("1. TELEGRAM_BOT_TOKEN 環境變量 (在 .env 文件中設置)")
        print("2. Google API 憑證文件 (credentials.json 或由 GOOGLE_CREDENTIALS_PATH 環境變量指定)")
        sys.exit(1)
    
    # 獲取 Telegram Bot 令牌
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    # 獲取 Google API 憑證路徑
    credentials_path = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    
    # 獲取 Google Sheet 名稱
    spreadsheet_name = os.environ.get('GOOGLE_SHEET_NAME', 'Wallet Analysis Results')
    
    try:
        # 創建 Google Sheet 管理器
        sheet_manager = GoogleSheetManager(credentials_path, spreadsheet_name)
        
        # 驗證 Google Sheet 憑證
        if not sheet_manager.authenticate():
            logger.error("Google Sheet 身份驗證失敗")
            sys.exit(1)
        
        # 創建 Telegram Bot
        bot = WalletAnalysisBot(telegram_token, analyze_wallet_async)
        
        # 註冊保存函數
        save_func = partial(save_to_sheet_async, sheet_manager)
        bot.register_save_function(save_func)
        
        # 運行機器人
        logger.info("啟動 Wallet Analysis Bot")
        bot.run()
        
    except Exception as e:
        logger.error(f"啟動機器人時出錯: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
