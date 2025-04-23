#!/usr/bin/env python3
import os
import json
from typing import Dict, List, Any, Union
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class GoogleSheetManager:
    """管理 Google Sheet 的類別，用於存儲爬蟲數據"""
    
    def __init__(self, credentials_file: str, spreadsheet_name: str):
        """初始化 Google Sheet 管理器
        
        Args:
            credentials_file: Google API 憑證 JSON 文件路徑
            spreadsheet_name: Google Sheet 的名稱
        """
        self.credentials_file = credentials_file
        self.spreadsheet_name = spreadsheet_name
        self.client = None
        self.sheet = None
        
    def authenticate(self) -> bool:
        """使用憑證進行身份驗證
        
        Returns:
            成功返回 True，失敗返回 False
        """
        try:
            # 定義 API 範圍
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 驗證憑證
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, scope
            )
            
            # 創建 gspread 客戶端
            self.client = gspread.authorize(credentials)
            
            # 嘗試打開電子表格，如果不存在則創建
            try:
                self.sheet = self.client.open(self.spreadsheet_name)
            except gspread.exceptions.SpreadsheetNotFound:
                self.sheet = self.client.create(self.spreadsheet_name)
                # 共享給所有人可查看
                self.sheet.share(None, perm_type='anyone', role='reader')
                
            return True
        except Exception as e:
            print(f"Google Sheet 身份驗證錯誤: {e}")
            return False
    
    def get_or_create_worksheet(self, worksheet_name: str) -> gspread.Worksheet:
        """獲取或創建工作表
        
        Args:
            worksheet_name: 工作表名稱
            
        Returns:
            工作表對象
        """
        try:
            # 嘗試獲取工作表，如果不存在則創建
            try:
                worksheet = self.sheet.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.sheet.add_worksheet(
                    title=worksheet_name, 
                    rows=1000, 
                    cols=26
                )
                
                # 設置標題行
                headers = [
                    "錢包地址", 
                    "爬取時間", 
                    "餘額 (SOL)", 
                    "總價值 ($)", 
                    "買入 ($)", 
                    "賣出 ($)", 
                    "盈虧 ($)", 
                    "已實現利潤 ($)", 
                    "未實現利潤 ($)", 
                    "總利潤 ($)", 
                    "勝率 (%)", 
                    "代幣數量", 
                    "歷史買入成本 ($)", 
                    "代幣平均成本 ($)", 
                    "代幣售出平均利潤 ($)", 
                    "最後活躍時間", 
                    "持有代幣"
                ]
                worksheet.append_row(headers)
                
            return worksheet
        except Exception as e:
            print(f"獲取或創建工作表錯誤: {e}")
            raise
    
    def save_wallet_data(self, wallet_address: str, wallet_data: Dict[str, Any]) -> bool:
        """保存錢包數據到 Google Sheet
        
        Args:
            wallet_address: 錢包地址
            wallet_data: 錢包數據
            
        Returns:
            成功返回 True，失敗返回 False
        """
        try:
            # 獲取當前日期作為工作表名稱
            current_date = datetime.now().strftime("%Y-%m-%d")
            worksheet = self.get_or_create_worksheet(current_date)
            
            # 提取摘要數據
            summary = wallet_data.get("wallet_summary", {})
            holdings = wallet_data.get("wallet_holdings", [])
            
            # 格式化持有代幣
            holdings_text = ""
            if holdings:
                tokens = []
                for token in holdings[:5]:  # 只取前5個代幣
                    token_name = token.get("symbol", "未知")
                    token_amount = token.get("amount", 0)
                    token_value = token.get("value", 0)
                    tokens.append(f"{token_name}: {token_amount} (${token_value})")
                holdings_text = ", ".join(tokens)
                if len(holdings) > 5:
                    holdings_text += f" 和其他 {len(holdings) - 5} 個代幣"
            
            # 準備數據行
            row_data = [
                wallet_address,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                summary.get("balance", 0),
                summary.get("total_value", 0),
                summary.get("buy", 0),
                summary.get("sell", 0),
                summary.get("pnl", 0),
                summary.get("realized_profit", 0),
                summary.get("unrealized_profit", 0),
                summary.get("total_profit", 0),
                summary.get("winrate", 0),
                summary.get("token_num", 0),
                summary.get("history_bought_cost", 0),
                summary.get("token_avg_cost", 0),
                summary.get("token_sold_avg_profit", 0),
                datetime.fromtimestamp(summary.get("last_active_timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S") if summary.get("last_active_timestamp", 0) > 0 else "無數據",
                holdings_text
            ]
            
            # 添加數據行
            worksheet.append_row(row_data)
            
            # 獲取電子表格的 URL
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{self.sheet.id}"
            
            return spreadsheet_url
        except Exception as e:
            print(f"保存錢包數據錯誤: {e}")
            return False
