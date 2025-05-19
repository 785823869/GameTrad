import os
import smtplib
import logging
import json
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from pathlib import Path
from queue import Queue

class QQEmailSender:
    """QQ邮箱推送工具类"""
    
    CONFIG_FILE = os.path.join("data", "config", "email_config.json")
    
    def __init__(self):
        """初始化邮件发送器"""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        
        # 邮件发送队列和线程
        self.email_queue = Queue()
        self.sending_thread = None
        self.stop_flag = False
        
        # 启动邮件发送线程
        self._start_sending_thread()
    
    def _load_config(self):
        """加载邮件配置"""
        default_config = {
            "enabled": False,
            "smtp_server": "smtp.qq.com",
            "smtp_port": 587,
            "username": "",
            "password": "",  # QQ邮箱授权码
            "sender": "GameTrad系统",
            "recipients": [],
            "retry_count": 3,
            "retry_delay": 5,
        }
        
        try:
            config_path = Path(self.CONFIG_FILE)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置，确保所有字段存在
                    config = {**default_config, **loaded_config}
                    self.logger.info("邮件配置已加载")
                    return config
            else:
                # 创建默认配置
                os.makedirs(config_path.parent, exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                    self.logger.info("已创建默认邮件配置文件")
                return default_config
        except Exception as e:
            self.logger.error(f"加载邮件配置失败: {e}", exc_info=True)
            return default_config
    
    def save_config(self, new_config):
        """保存邮件配置"""
        try:
            # 确保配置目录存在
            config_path = Path(self.CONFIG_FILE)
            os.makedirs(config_path.parent, exist_ok=True)
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            
            self.config = new_config
            self.logger.info("邮件配置已保存")
            return True
        except Exception as e:
            self.logger.error(f"保存邮件配置失败: {e}", exc_info=True)
            return False
    
    def test_connection(self):
        """测试邮件服务器连接"""
        if not self.config["enabled"]:
            return False, "邮件功能未启用"
        
        try:
            server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
            server.ehlo()
            server.starttls()
            server.login(self.config["username"], self.config["password"])
            server.quit()
            return True, "连接测试成功"
        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _start_sending_thread(self):
        """启动邮件发送线程"""
        if self.sending_thread is None or not self.sending_thread.is_alive():
            self.stop_flag = False
            self.sending_thread = threading.Thread(target=self._process_email_queue, daemon=True)
            self.sending_thread.start()
            self.logger.info("邮件发送线程已启动")
    
    def _process_email_queue(self):
        """处理邮件发送队列"""
        while not self.stop_flag:
            try:
                # 从队列获取邮件任务
                if not self.email_queue.empty():
                    email_task = self.email_queue.get()
                    self._send_email_task(email_task)
                    self.email_queue.task_done()
                else:
                    time.sleep(1)  # 避免CPU空转
            except Exception as e:
                self.logger.error(f"处理邮件队列异常: {e}", exc_info=True)
    
    def _send_email_task(self, task):
        """发送单个邮件任务"""
        subject = task["subject"]
        content = task["content"]
        recipients = task.get("recipients", self.config["recipients"])
        html = task.get("html", False)
        
        if not self.config["enabled"]:
            self.logger.warning(f"邮件功能未启用，跳过发送: {subject}")
            return False
        
        if not recipients:
            self.logger.warning("没有收件人，跳过发送")
            return False
        
        retry_count = self.config["retry_count"]
        retry_delay = self.config["retry_delay"]
        
        for attempt in range(retry_count):
            try:
                # 创建邮件
                msg = MIMEMultipart()
                msg['From'] = f"{self.config['sender']} <{self.config['username']}>"
                msg['To'] = "; ".join(recipients)
                msg['Subject'] = Header(subject, 'utf-8')
                
                # 设置邮件内容
                if html:
                    msg.attach(MIMEText(content, 'html', 'utf-8'))
                else:
                    msg.attach(MIMEText(content, 'plain', 'utf-8'))
                
                # 连接服务器发送
                server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
                server.ehlo()
                server.starttls()
                server.login(self.config["username"], self.config["password"])
                server.sendmail(self.config["username"], recipients, msg.as_string())
                server.quit()
                
                self.logger.info(f"邮件发送成功: {subject}")
                return True
                
            except Exception as e:
                self.logger.error(f"邮件发送失败 (尝试 {attempt+1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
        
        self.logger.error(f"邮件发送最终失败: {subject}")
        return False
    
    def send_email(self, subject, content, recipients=None, html=False, immediate=False):
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            content: 邮件内容
            recipients: 收件人列表，为None则使用配置中的默认收件人
            html: 是否为HTML内容
            immediate: 是否立即发送(同步)，否则加入队列(异步)
            
        Returns:
            bool: 是否成功添加到队列或发送成功
        """
        try:
            # 准备邮件任务
            task = {
                "subject": subject,
                "content": content,
                "recipients": recipients,
                "html": html
            }
            
            if immediate:
                # 立即发送
                return self._send_email_task(task)
            else:
                # 加入队列
                self.email_queue.put(task)
                return True
                
        except Exception as e:
            self.logger.error(f"准备邮件任务失败: {e}", exc_info=True)
            return False
    
    def send_template_email(self, template_name, context, recipients=None, immediate=False):
        """
        使用模板发送邮件
        
        Args:
            template_name: 模板名称
            context: 模板上下文数据
            recipients: 收件人列表
            immediate: 是否立即发送
            
        Returns:
            bool: 是否成功
        """
        try:
            # 根据模板名称获取对应的模板
            template_func = self._get_template(template_name)
            if not template_func:
                self.logger.error(f"邮件模板不存在: {template_name}")
                return False
                
            # 生成邮件主题和内容
            subject, content, is_html = template_func(context)
            
            # 发送邮件
            return self.send_email(subject, content, recipients, is_html, immediate)
            
        except Exception as e:
            self.logger.error(f"发送模板邮件失败: {e}", exc_info=True)
            return False
    
    def _get_template(self, template_name):
        """获取邮件模板"""
        templates = {
            "trade_update": self._template_trade_update,
            "system_alert": self._template_system_alert,
            "daily_report": self._template_daily_report,
            "backup_success": self._template_backup_success,
        }
        return templates.get(template_name)
    
    def _template_trade_update(self, context):
        """交易更新通知模板"""
        subject = f"GameTrad交易更新通知 - {context['item_name']}"
        
        # HTML内容
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #4b7bec;">交易物品更新通知</h2>
            <p>您关注的物品已更新：</p>
            <div style="background-color: #f1f2f6; padding: 15px; border-radius: 5px;">
                <p><strong>物品名称:</strong> {context['item_name']}</p>
                <p><strong>价格变化:</strong> {context['old_price']} → <span style="color: {'#2ecc71' if context['price_change'] < 0 else '#e74c3c'}">{context['new_price']}</span></p>
                <p><strong>数量:</strong> {context['quantity']}</p>
                <p><strong>更新时间:</strong> {context['time']}</p>
            </div>
            <p>请登录GameTrad查看详情。</p>
            <p style="color: #7f8c8d; font-size: 12px;">此邮件由GameTrad系统自动发送，请勿回复。</p>
        </body>
        </html>
        """
        
        return subject, content, True  # 返回主题、内容、是否HTML
    
    def _template_system_alert(self, context):
        """系统警报模板"""
        subject = f"GameTrad系统警报 - {context['alert_type']}"
        
        # HTML内容
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #e74c3c;">系统警报</h2>
            <p>GameTrad系统检测到以下问题：</p>
            <div style="background-color: #f1f2f6; padding: 15px; border-radius: 5px;">
                <p><strong>警报类型:</strong> {context['alert_type']}</p>
                <p><strong>严重程度:</strong> {context['severity']}</p>
                <p><strong>详情:</strong> {context['details']}</p>
                <p><strong>时间:</strong> {context['time']}</p>
            </div>
            <p>请及时处理以上问题。</p>
            <p style="color: #7f8c8d; font-size: 12px;">此邮件由GameTrad系统自动发送，请勿回复。</p>
        </body>
        </html>
        """
        
        return subject, content, True
    
    def _template_daily_report(self, context):
        """日报模板"""
        subject = f"GameTrad日报 - {context['date']}"
        
        # 构建表格内容
        rows = ""
        for item in context['items']:
            rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{item['name']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{item['price']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{item['quantity']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{item['profit']}</td>
            </tr>
            """
        
        # HTML内容
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #2980b9;">GameTrad日报</h2>
            <p>日期: {context['date']}</p>
            
            <h3>今日交易摘要</h3>
            <p>总交易量: {context['total_trades']}</p>
            <p>总利润: {context['total_profit']}</p>
            
            <h3>热门物品</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 8px; border: 1px solid #ddd;">物品名称</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">价格</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">数量</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">利润</th>
                </tr>
                {rows}
            </table>
            
            <p style="color: #7f8c8d; font-size: 12px;">此邮件由GameTrad系统自动发送，请勿回复。</p>
        </body>
        </html>
        """
        
        return subject, content, True
    
    def _template_backup_success(self, context):
        """备份成功通知模板"""
        subject = "GameTrad数据备份成功通知"
        
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #27ae60;">数据备份成功</h2>
            <p>GameTrad系统已完成数据备份：</p>
            <div style="background-color: #f1f2f6; padding: 15px; border-radius: 5px;">
                <p><strong>备份时间:</strong> {context['time']}</p>
                <p><strong>备份文件:</strong> {context['filename']}</p>
                <p><strong>文件大小:</strong> {context['size']}</p>
                <p><strong>备份路径:</strong> {context['path']}</p>
            </div>
            <p style="color: #7f8c8d; font-size: 12px;">此邮件由GameTrad系统自动发送，请勿回复。</p>
        </body>
        </html>
        """
        
        return subject, content, True
    
    def stop(self):
        """停止邮件发送线程"""
        self.stop_flag = True
        if self.sending_thread and self.sending_thread.is_alive():
            self.sending_thread.join(timeout=2)
        self.logger.info("邮件发送线程已停止") 