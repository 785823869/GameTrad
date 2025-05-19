import os
import smtplib
import logging
import json
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from pathlib import Path
from queue import Queue
from datetime import datetime, timedelta
import re

class QQEmailSender:
    """QQ邮箱推送工具类"""
    
    CONFIG_FILE = os.path.join("data", "config", "email_config.json")
    CUSTOM_TEMPLATES_FILE = os.path.join("data", "config", "email_templates.json")
    LOG_DIR = os.path.join("data", "logs", "email")
    
    def __init__(self):
        """初始化邮件发送器"""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.custom_templates = self._load_custom_templates()
        
        # 确保日志目录存在
        os.makedirs(self.LOG_DIR, exist_ok=True)
        
        # 邮件发送队列和线程
        self.email_queue = Queue()
        self.sending_thread = None
        self.stop_flag = False
        
        # 启动邮件发送线程
        self._start_sending_thread()
        
        # 设置日志处理器
        self._setup_logger()
        
        # 清理过期日志
        self._clean_old_logs()
    
    def _setup_logger(self):
        """设置专用日志处理器"""
        # 创建文件处理器
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.LOG_DIR, f"email_{today}.log")
        
        # 检查是否已经有此文件处理器
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == os.path.abspath(log_file):
                return
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        
    def _clean_old_logs(self):
        """清理过期日志"""
        try:
            # 获取日志保留天数
            log_days = self.config.get("log_days", 30)
            
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=log_days)
            
            # 遍历日志目录
            for file_name in os.listdir(self.LOG_DIR):
                if file_name.startswith("email_") and file_name.endswith(".log"):
                    try:
                        # 从文件名提取日期
                        date_str = file_name[6:-4]  # 去掉 "email_" 和 ".log"
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        # 检查是否过期
                        if file_date < cutoff_date:
                            file_path = os.path.join(self.LOG_DIR, file_name)
                            os.remove(file_path)
                            self.logger.info(f"已删除过期日志: {file_name}")
                    except Exception as e:
                        self.logger.warning(f"无法处理日志文件 {file_name}: {e}")
        except Exception as e:
            self.logger.error(f"清理过期日志失败: {e}")
    
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
            "enable_log": True,
            "log_days": 30,
            "enable_daily_report": False,
            "daily_report_time": "20:00"
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
    
    def _load_custom_templates(self):
        """加载自定义模板"""
        default_templates = {
            # 存储自定义模板
            # 格式: "template_name": {"subject": "Subject template", "content": "Content template", "html": true/false}
        }
        
        try:
            templates_path = Path(self.CUSTOM_TEMPLATES_FILE)
            if templates_path.exists():
                with open(templates_path, 'r', encoding='utf-8') as f:
                    loaded_templates = json.load(f)
                    self.logger.info("自定义邮件模板已加载")
                    return loaded_templates
            else:
                # 创建默认模板文件
                os.makedirs(templates_path.parent, exist_ok=True)
                with open(templates_path, 'w', encoding='utf-8') as f:
                    json.dump(default_templates, f, ensure_ascii=False, indent=2)
                    self.logger.info("已创建默认邮件模板文件")
                return default_templates
        except Exception as e:
            self.logger.error(f"加载邮件模板失败: {e}", exc_info=True)
            return default_templates
    
    def save_custom_template(self, template_name, subject, content, is_html=True):
        """保存自定义模板"""
        try:
            # 添加或更新模板
            self.custom_templates[template_name] = {
                "subject": subject,
                "content": content,
                "html": is_html
            }
            
            # 保存到文件
            templates_path = Path(self.CUSTOM_TEMPLATES_FILE)
            os.makedirs(templates_path.parent, exist_ok=True)
            
            with open(templates_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_templates, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"自定义模板已保存: {template_name}")
            return True
        except Exception as e:
            self.logger.error(f"保存自定义模板失败: {e}", exc_info=True)
            return False
    
    def delete_custom_template(self, template_name):
        """删除自定义模板"""
        try:
            if template_name in self.custom_templates:
                del self.custom_templates[template_name]
                
                # 保存更改
                templates_path = Path(self.CUSTOM_TEMPLATES_FILE)
                with open(templates_path, 'w', encoding='utf-8') as f:
                    json.dump(self.custom_templates, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"自定义模板已删除: {template_name}")
                return True
            else:
                self.logger.warning(f"尝试删除不存在的模板: {template_name}")
                return False
        except Exception as e:
            self.logger.error(f"删除自定义模板失败: {e}", exc_info=True)
            return False
    
    def list_custom_templates(self):
        """列出所有自定义模板"""
        return list(self.custom_templates.keys())
    
    def get_custom_template(self, template_name):
        """获取自定义模板"""
        return self.custom_templates.get(template_name)
        
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
            
            # 更新日志设置
            self._setup_logger()
            self._clean_old_logs()
            
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
            self.logger.info("邮件服务器连接测试成功")
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
                
                # 设置发件人，确保格式正确
                sender_name = self.config['sender']
                sender_email = self.config['username']
                
                # 使用email.utils.formataddr函数确保地址格式完全符合RFC标准
                from_addr = formataddr((sender_name, sender_email))
                msg['From'] = from_addr
                
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
                server.sendmail(sender_email, recipients, msg.as_string())
                server.quit()
                
                # 记录成功
                self.logger.info(f"邮件发送成功: {subject}")
                
                # 记录详细日志
                if self.config.get("enable_log", True):
                    self._log_email_sent(subject, recipients, True)
                
                return True
                
            except Exception as e:
                self.logger.error(f"邮件发送失败 (尝试 {attempt+1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
        
        # 记录最终失败
        if self.config.get("enable_log", True):
            self._log_email_sent(subject, recipients, False, "达到最大重试次数")
        
        self.logger.error(f"邮件发送最终失败: {subject}")
        return False
    
    def _log_email_sent(self, subject, recipients, success, error=None):
        """记录邮件发送日志"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(self.LOG_DIR, f"email_{today}.log")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "成功" if success else "失败"
            recipients_str = ", ".join(recipients)
            
            log_entry = f"{timestamp} | {status} | 收件人: {recipients_str} | 主题: {subject}"
            if error:
                log_entry += f" | 错误: {error}"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            self.logger.error(f"记录邮件日志失败: {e}")
    
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
    
    def render_template(self, template, context):
        """
        渲染模板文本，替换变量
        
        Args:
            template: 模板文本
            context: 变量上下文
            
        Returns:
            str: 渲染后的文本
        """
        rendered = template
        
        # 替换所有 {{variable}} 格式的变量
        for key, value in context.items():
            pattern = r'\{\{\s*' + key + r'\s*\}\}'
            rendered = re.sub(pattern, str(value), rendered)
        
        return rendered
    
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
            # 首先检查是否是自定义模板
            if template_name in self.custom_templates:
                template_data = self.custom_templates[template_name]
                
                # 渲染模板
                subject = self.render_template(template_data["subject"], context)
                content = self.render_template(template_data["content"], context)
                is_html = template_data.get("html", True)
                
                # 发送邮件
                return self.send_email(subject, content, recipients, is_html, immediate)
            
            # 否则使用内置模板
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
        
        content = f'''
        <html>
        <head>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4a86e8; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .item {{ margin-bottom: 10px; }}
                .item .label {{ font-weight: bold; display: inline-block; width: 80px; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>交易更新通知</h2>
                </div>
                <div class="content">
                    <p>系统检测到以下交易信息更新：</p>
                    
                    <div class="item">
                        <span class="label">物品名称:</span> {context['item_name']}
                    </div>
                    <div class="item">
                        <span class="label">价格:</span> {context['price']}
                    </div>
                    <div class="item">
                        <span class="label">数量:</span> {context['quantity']}
                    </div>
                    <div class="item">
                        <span class="label">服务器:</span> {context['server']}
                    </div>
                    <div class="item">
                        <span class="label">时间:</span> {context['time']}
                    </div>
                    
                    <p>请登录GameTrad系统查看详细信息。</p>
                </div>
                <div class="footer">
                    此邮件由GameTrad系统自动发送，请勿回复
                </div>
            </div>
        </body>
        </html>
        '''
        
        return subject, content, True
    
    def _template_system_alert(self, context):
        """系统警报模板"""
        subject = f"GameTrad系统警报 - {context.get('status', '警告')}"
        
        content = f'''
        <html>
        <head>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #e06666; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .message {{ padding: 10px; background-color: #fff; border-left: 4px solid #e06666; margin-top: 10px; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>系统警报</h2>
                </div>
                <div class="content">
                    <p><strong>状态:</strong> {context.get('status', '警告')}</p>
                    <p><strong>时间:</strong> {context.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
                    
                    <div class="message">
                        {context.get('message', '系统检测到异常情况，请尽快处理！')}
                    </div>
                    
                    <p>请尽快登录系统检查详情。</p>
                </div>
                <div class="footer">
                    此邮件由GameTrad系统自动发送，请勿回复
                </div>
            </div>
        </body>
        </html>
        '''
        
        return subject, content, True
    
    def _template_daily_report(self, context):
        """每日报告模板"""
        subject = f"GameTrad每日报告 - {context.get('date', datetime.now().strftime('%Y-%m-%d'))}"
        
        # 使用表格格式展示数据
        report_rows = ""
        if 'items' in context and isinstance(context['items'], list):
            for item in context['items']:
                row = f'''
                <tr>
                    <td>{item.get('name', '-')}</td>
                    <td>{item.get('quantity', '0')}</td>
                    <td>{item.get('price', '0.00')}</td>
                    <td>{item.get('total', '0.00')}</td>
                </tr>
                '''
                report_rows += row
        else:
            report_rows = "<tr><td colspan='4'>无数据</td></tr>"
        
        content = f'''
        <html>
        <head>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #6aa84f; color: white; padding: 15px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                table, th, td {{ border: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; padding: 10px; text-align: left; }}
                td {{ padding: 8px; }}
                .summary {{ margin-top: 20px; font-weight: bold; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #777; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>GameTrad每日报告</h2>
                </div>
                <div class="content">
                    <p><strong>报告日期:</strong> {context.get('date', datetime.now().strftime('%Y-%m-%d'))}</p>
                    <p><strong>报告周期:</strong> {context.get('period', '过去24小时')}</p>
                    
                    <h3>交易概览</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>物品名称</th>
                                <th>交易数量</th>
                                <th>价格</th>
                                <th>总金额</th>
                            </tr>
                        </thead>
                        <tbody>
                            {report_rows}
                        </tbody>
                    </table>
                    
                    <div class="summary">
                        <p>交易总数: {context.get('total_trades', 0)}</p>
                        <p>交易总额: {context.get('total_amount', '0.00')}</p>
                    </div>
                    
                    <p>请登录系统查看完整报告。</p>
                </div>
                <div class="footer">
                    此报告由GameTrad系统自动生成，请勿回复此邮件
                </div>
            </div>
        </body>
        </html>
        '''
        
        return subject, content, True
    
    def _template_backup_success(self, context):
        """备份成功通知模板"""
        subject = "GameTrad数据库备份成功通知"
        
        content = f'''
        <html>
        <head>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #45818e; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .info-item {{ margin-bottom: 10px; }}
                .info-item .label {{ font-weight: bold; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>数据库备份成功</h2>
                </div>
                <div class="content">
                    <p>系统已成功完成数据库备份操作。</p>
                    
                    <div class="info-item">
                        <span class="label">备份文件:</span> {context.get('filename', '未知')}
                    </div>
                    <div class="info-item">
                        <span class="label">备份路径:</span> {context.get('path', '未知')}
                    </div>
                    <div class="info-item">
                        <span class="label">文件大小:</span> {context.get('size', '未知')}
                    </div>
                    <div class="info-item">
                        <span class="label">备份时间:</span> {context.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
                    </div>
                    
                    <p>您可以在系统中查看和管理所有备份文件。</p>
                </div>
                <div class="footer">
                    此邮件由GameTrad系统自动发送，请勿回复
                </div>
            </div>
        </body>
        </html>
        '''
        
        return subject, content, True
    
    def stop(self):
        """停止邮件发送线程"""
        self.stop_flag = True
        if self.sending_thread and self.sending_thread.is_alive():
            self.sending_thread.join(timeout=1.0)
            self.logger.info("邮件发送线程已停止") 