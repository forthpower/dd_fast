#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dd_fast 守护进程
监控主程序运行状态，如果程序停止则自动重启
"""

import os
import sys
import time
import subprocess
import signal
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
log_dir = Path.home() / "Library" / "Logs" / "dd_fast"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "daemon.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DDFastDaemon:
    """dd_fast 守护进程类"""
    
    def __init__(self):
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent
        self.app_script = self.project_root / "app.py"
        self.pid_file = log_dir / "dd_fast.pid"
        self.process = None
        self.running = True
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("=" * 60)
        logger.info("dd_fast 守护进程启动")
        logger.info(f"项目目录: {self.project_root}")
        logger.info(f"应用脚本: {self.app_script}")
        logger.info(f"日志目录: {log_dir}")
        logger.info("=" * 60)
    
    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        logger.info(f"收到信号 {signum}，准备退出...")
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
        sys.exit(0)
    
    def _is_process_running(self, pid):
        """检查进程是否运行"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _get_running_pid(self):
        """获取正在运行的进程PID"""
        try:
            if self.pid_file.exists():
                pid = int(self.pid_file.read_text().strip())
                if self._is_process_running(pid):
                    return pid
        except:
            pass
        return None
    
    def _save_pid(self, pid):
        """保存进程PID"""
        try:
            self.pid_file.write_text(str(pid))
        except Exception as e:
            logger.error(f"保存PID失败: {e}")
    
    def _start_app(self):
        """启动应用"""
        try:
            # 检查脚本是否存在
            if not self.app_script.exists():
                logger.error(f"应用脚本不存在: {self.app_script}")
                return False
            
            # 获取Python解释器路径
            python = sys.executable
            
            # 启动应用
            logger.info(f"启动应用: {python} {self.app_script}")
            # 将输出重定向到日志文件
            stdout_file = log_dir / "app.stdout.log"
            stderr_file = log_dir / "app.stderr.log"
            stdout_f = open(stdout_file, 'a')
            stderr_f = open(stderr_file, 'a')
            self.process = subprocess.Popen(
                [python, str(self.app_script)],
                cwd=str(self.project_root),
                stdout=stdout_f,
                stderr=stderr_f,
                preexec_fn=os.setsid  # 创建新的进程组
            )
            # 注意：文件句柄会随进程一起关闭，不需要手动关闭
            
            # 保存PID
            self._save_pid(self.process.pid)
            logger.info(f"应用已启动，PID: {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"启动应用失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _check_process(self):
        """检查进程状态"""
        if self.process is None:
            return False
        
        # 检查进程是否还在运行
        if self.process.poll() is not None:
            # 进程已退出
            return_code = self.process.returncode
            logger.warning(f"应用进程已退出，返回码: {return_code}")
            logger.info(f"应用输出日志: {log_dir / 'app.stdout.log'}")
            logger.info(f"应用错误日志: {log_dir / 'app.stderr.log'}")
            
            self.process = None
            return False
        
        return True
    
    def run(self):
        """运行守护进程"""
        restart_delay = 5  # 重启延迟（秒）
        check_interval = 10  # 检查间隔（秒）
        consecutive_failures = 0
        max_failures = 5
        
        while self.running:
            try:
                # 检查进程是否运行
                if not self._check_process():
                    # 进程未运行，需要启动
                    if self.process is None:
                        logger.info("应用未运行，准备启动...")
                        if self._start_app():
                            consecutive_failures = 0
                            logger.info("应用启动成功")
                        else:
                            consecutive_failures += 1
                            logger.error(f"应用启动失败 (连续失败 {consecutive_failures} 次)")
                            
                            if consecutive_failures >= max_failures:
                                logger.error(f"连续启动失败 {max_failures} 次，停止尝试")
                                break
                            
                            logger.info(f"{restart_delay}秒后重试...")
                            time.sleep(restart_delay)
                            continue
                
                # 进程运行正常，等待检查间隔
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，退出守护进程")
                break
            except Exception as e:
                logger.error(f"守护进程错误: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(check_interval)
        
        # 清理
        if self.process:
            try:
                logger.info("正在停止应用...")
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
        
        logger.info("守护进程已退出")


def main():
    """主函数"""
    daemon = DDFastDaemon()
    daemon.run()


if __name__ == "__main__":
    main()

