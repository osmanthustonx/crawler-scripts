#!/usr/bin/env python3
import os
import logging
from typing import Dict, List, Any, Callable, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# 設置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class WalletAnalysisBot:
    """Telegram Bot 類別，用於處理錢包分析請求"""
    
    def __init__(self, token: str, wallet_analyzer_func: Callable):
        """初始化 Telegram Bot
        
        Args:
            token: Telegram Bot API 令牌
            wallet_analyzer_func: 錢包分析函數
        """
        self.token = token
        self.wallet_analyzer_func = wallet_analyzer_func
        self.application = Application.builder().token(token).build()
        
        # 註冊命令處理器
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        
        # 註冊消息處理器
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # 註冊回調查詢處理器
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # 註冊錯誤處理器
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """處理 /start 命令
        
        Args:
            update: 更新對象
            context: 上下文對象
        """
        user = update.effective_user
        await update.message.reply_text(
            f"您好 {user.first_name}！\n\n"
            f"我是錢包分析機器人，可以幫您分析 Solana 錢包地址。\n\n"
            f"使用 /analyze 加上錢包地址來分析一個錢包\n"
            f"或者直接發送錢包地址給我。\n\n"
            f"使用 /help 獲取更多幫助。"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """處理 /help 命令
        
        Args:
            update: 更新對象
            context: 上下文對象
        """
        help_text = (
            "📊 *錢包分析機器人使用說明* 📊\n\n"
            "*命令列表:*\n"
            "/start - 開始使用機器人\n"
            "/help - 顯示此幫助信息\n"
            "/analyze <錢包地址> - 分析指定的錢包地址\n\n"
            "*直接使用:*\n"
            "您也可以直接發送 Solana 錢包地址，我會自動為您分析。\n\n"
            "*支持的格式:*\n"
            "- 單個 Solana 錢包地址\n"
            "- 多個地址（每行一個）\n\n"
            "*注意:*\n"
            "分析過程可能需要一些時間，請耐心等待。"
        )
        await update.message.reply_markdown(help_text)
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """處理 /analyze 命令
        
        Args:
            update: 更新對象
            context: 上下文對象
        """
        # 檢查是否提供了錢包地址
        if not context.args:
            await update.message.reply_text("請提供要分析的錢包地址。\n例如: /analyze 5YEdmMQcEt6MEKikYRZdrUwPwL5xhH5fqR2VZ4XXTL7c")
            return
        
        # 獲取錢包地址
        wallet_address = context.args[0]
        
        # 發送處理中消息
        processing_message = await update.message.reply_text(
            f"正在分析錢包地址: `{wallet_address}`\n這可能需要一些時間，請耐心等待...",
            parse_mode='Markdown'
        )
        
        # 調用錢包分析函數
        await self._process_wallet_analysis(update, context, wallet_address, processing_message.message_id)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """處理文本消息
        
        Args:
            update: 更新對象
            context: 上下文對象
        """
        # 獲取消息文本
        text = update.message.text
        
        # 檢查是否是錢包地址（簡單檢查）
        if len(text) >= 32 and not text.startswith('/'):
            # 發送處理中消息
            processing_message = await update.message.reply_text(
                f"正在分析錢包地址: `{text}`\n這可能需要一些時間，請耐心等待...",
                parse_mode='Markdown'
            )
            
            # 調用錢包分析函數
            await self._process_wallet_analysis(update, context, text, processing_message.message_id)
        else:
            # 發送幫助信息
            await update.message.reply_text(
                "請發送有效的 Solana 錢包地址進行分析。\n"
                "或使用 /help 獲取更多幫助。"
            )
    
    async def _process_wallet_analysis(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        wallet_address: str,
        message_id: int
    ) -> None:
        """處理錢包分析
        
        Args:
            update: 更新對象
            context: 上下文對象
            wallet_address: 錢包地址
            message_id: 處理中消息的 ID
        """
        try:
            # 調用錢包分析函數
            result = await context.application.create_task(
                self.wallet_analyzer_func(wallet_address)
            )
            
            # 檢查結果
            if not result or "error" in result.get(wallet_address, {}):
                error_msg = result.get(wallet_address, {}).get("error", "未知錯誤")
                await update.message.reply_text(f"分析錯誤: {error_msg}")
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=message_id,
                    text=f"❌ 分析錢包地址 `{wallet_address}` 失敗: {error_msg}",
                    parse_mode='Markdown'
                )
                return
            
            # 獲取錢包數據
            wallet_data = result.get(wallet_address, {})
            
            # 創建鍵盤標記
            keyboard = [
                [
                    InlineKeyboardButton("保存到 Google Sheet", callback_data=f"save_{wallet_address}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # 格式化摘要數據
            summary = wallet_data.get("wallet_summary", {})
            
            # 創建結果消息
            # 將時間戳轉換為可讀格式
            last_active_time = "無數據"
            if summary.get("last_active_timestamp", 0) > 0:
                from datetime import datetime
                last_active_time = datetime.fromtimestamp(summary.get("last_active_timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            result_message = (
                f"✅ *錢包分析結果*\n\n"
                f"*錢包地址:* `{wallet_address}`\n\n"
                f"*基本信息:*\n"
                f"\u2022 餘額: {summary.get('balance', 0)} SOL\n"
                f"\u2022 總價值: ${summary.get('total_value', 0)}\n"
                f"\u2022 代幣數量: {summary.get('token_num', 0)}\n"
                f"\u2022 最後活躍時間: {last_active_time}\n\n"
                
                f"*交易統計:*\n"
                f"\u2022 買入: ${summary.get('buy', 0)}\n"
                f"\u2022 賣出: ${summary.get('sell', 0)}\n"
                f"\u2022 盈虧: ${summary.get('pnl', 0)}\n\n"
                
                f"*利潤分析:*\n"
                f"\u2022 已實現利潤: ${summary.get('realized_profit', 0)}\n"
                f"\u2022 未實現利潤: ${summary.get('unrealized_profit', 0)}\n"
                f"\u2022 總利潤: ${summary.get('total_profit', 0)}\n"
                f"\u2022 勝率: {summary.get('winrate', 0)}%\n\n"
                
                f"*成本分析:*\n"
                f"\u2022 歷史買入成本: ${summary.get('history_bought_cost', 0)}\n"
                f"\u2022 代幣平均成本: ${summary.get('token_avg_cost', 0)}\n"
                f"\u2022 代幣售出平均利潤: ${summary.get('token_sold_avg_profit', 0)}"
            )
            
            # 更新處理中消息
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                text=result_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # 將錢包數據存儲在上下文中，以便回調時使用
            if 'wallet_data' not in context.bot_data:
                context.bot_data['wallet_data'] = {}
            
            context.bot_data['wallet_data'][wallet_address] = wallet_data
            logger.info(f"已將錢包 {wallet_address} 的數據存儲在上下文中")
            
        except Exception as e:
            logger.error(f"分析錢包時出錯: {e}")
            await update.message.reply_text(f"分析過程中發生錯誤: {str(e)}")
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                text=f"❌ 分析錢包地址 `{wallet_address}` 時發生錯誤",
                parse_mode='Markdown'
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """處理回調查詢
        
        Args:
            update: 更新對象
            context: 上下文對象
        """
        query = update.callback_query
        await query.answer()
        
        # 獲取回調數據
        callback_data = query.data
        
        # 處理保存到 Google Sheet 的回調
        if callback_data.startswith("save_"):
            wallet_address = callback_data[5:]  # 移除 "save_" 前綴
            
            # 檢查錢包數據是否存在
            logger.info(f"檢查錢包 {wallet_address} 的數據")
            logger.info(f"context.bot_data 包含的鍵: {list(context.bot_data.keys())}")
            if 'wallet_data' not in context.bot_data or wallet_address not in context.bot_data['wallet_data']:
                await query.edit_message_text(
                    text=f"無法保存數據: 找不到錢包 `{wallet_address}` 的數據",
                    parse_mode='Markdown'
                )
                return
            
            # 獲取錢包數據
            wallet_data = context.bot_data['wallet_data'][wallet_address]
            
            # 發送保存中消息
            await query.edit_message_text(
                text=query.message.text + "\n\n*正在保存到 Google Sheet...*",
                parse_mode='Markdown'
            )
            
            # 調用保存函數（這應該由主程序提供）
            logger.info(f"context.bot_data 包含的鍵: {list(context.bot_data.keys())}")
            if 'save_to_sheet_func' in context.bot_data:
                try:
                    result = await context.application.create_task(
                        context.bot_data['save_to_sheet_func'](wallet_address, wallet_data)
                    )
                    
                    if result:
                        await query.edit_message_text(
                            text=query.message.text + f"\n\n✅ *已保存到 Google Sheet*\n[點擊查看]({result})",
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                    else:
                        await query.edit_message_text(
                            text=query.message.text + "\n\n❌ *保存到 Google Sheet 失敗*",
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"保存到 Google Sheet 時出錯: {e}")
                    await query.edit_message_text(
                        text=query.message.text + f"\n\n❌ *保存到 Google Sheet 時出錯: {str(e)}*",
                        parse_mode='Markdown'
                    )
            else:
                await query.edit_message_text(
                    text=query.message.text + "\n\n❌ *保存功能未配置*",
                    parse_mode='Markdown'
                )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """處理錯誤
        
        Args:
            update: 更新對象
            context: 上下文對象
        """
        logger.error(f"更新 {update} 導致錯誤 {context.error}")
        
        # 發送錯誤消息
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "抱歉，處理您的請求時發生錯誤。請稍後再試。"
            )
    
    def register_save_function(self, save_func: Callable) -> None:
        """註冊保存函數
        
        Args:
            save_func: 保存函數
        """
        self.application.bot_data['save_to_sheet_func'] = save_func
        logger.info("已註冊保存函數")
    
    def run(self) -> None:
        """運行機器人"""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
