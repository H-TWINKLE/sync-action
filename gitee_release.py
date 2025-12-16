#!/usr/bin/env python
# coding:utf-8
"""
Gitee API 客户端模块
提供与 Gitee 平台交互的功能，包括创建 Release 和上传附件等操作
"""

import os
import time
import logging
from functools import wraps

import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

# 从环境变量中获取重试次数，默认为0（不重试）
gitee_upload_retry_times = os.environ.get("gitee_upload_retry_times", "0")
try:
    retry_times = int(gitee_upload_retry_times)
except:
    retry_times = 0


def retry_decorator(max_retries, include_exceptions=None, exclude_exceptions=None, sleep_interval=1):
    """
    重试装饰器工厂函数
    
    Args:
        max_retries (int): 最大重试次数
        include_exceptions (list): 需要捕获并重试的异常类型列表
        exclude_exceptions (list): 即使发生也不重试的异常类型列表
        sleep_interval (int): 重试间隔时间（秒）
    
    Returns:
        function: 装饰器函数
    """
    if include_exceptions is None:
        include_exceptions = [Exception]
    if exclude_exceptions is None:
        exclude_exceptions = [ValueError]

    def retry_decorator_inner(func):
        """
        内部装饰器实现
        """
        def execute_with_retry(retries_left, *args, **kwargs):
            """
            带重试机制的执行函数
            
            Args:
                retries_left (int): 剩余重试次数
                *args: 函数参数
                **kwargs: 函数关键字参数
            
            Returns:
                函数执行结果
            
            Raises:
                Exception: 当超过最大重试次数或遇到排除的异常时抛出
            """
            try:
                return func(*args, **kwargs)
            except Exception as exception:
                # 如果是排除的异常或者不是需要包含的异常，则直接抛出
                if (is_excluded_exception(exception, exclude_exceptions) or
                        not is_included_exception(exception, include_exceptions)):
                    raise exception
                
                # 如果没有剩余重试次数，则抛出异常
                if retries_left == 0:
                    raise exception
                else:
                    logging.warning('捕获到异常: %s', exception)
                    # 等待指定时间后重试
                    if sleep_interval > 0:
                        time.sleep(sleep_interval)
                    return execute_with_retry(retries_left - 1, *args, **kwargs)

        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            装饰器包装函数
            """
            return execute_with_retry(max_retries, *args, **kwargs)

        return wrapper

    return retry_decorator_inner


def is_included_exception(exception, include_exceptions):
    """
    检查异常是否在包含列表中
    
    Args:
        exception (Exception): 异常实例
        include_exceptions (list): 包含的异常类型列表
    
    Returns:
        bool: 如果异常类型在列表中返回True，否则返回False
    """
    for exception_type in include_exceptions:
        if isinstance(exception, exception_type):
            return True
    return False


def is_excluded_exception(exception, exclude_exceptions):
    """
    检查异常是否在排除列表中
    
    Args:
        exception (Exception): 异常实例
        exclude_exceptions (list): 排除的异常类型列表
    
    Returns:
        bool: 如果异常类型在列表中返回True，否则返回False
    """
    for exception_type in exclude_exceptions:
        if isinstance(exception, exception_type):
            return True
    return False


class Gitee:
    """
    Gitee API 客户端类
    提供与 Gitee 平台交互的方法
    """
    
    def __init__(self, owner, token):
        """
        初始化 Gitee 客户端
        
        Args:
            owner (str): 仓库所有者
            token (str): Gitee 访问令牌
        """
        self.owner = owner
        self.token = token

    def create_release(self, repo, tag_name, name, body='-', target_commitish='master'):
        """
        在 Gitee 仓库中创建一个新的 Release
        
        Args:
            repo (str): 仓库名称
            tag_name (str): 标签名称
            name (str): Release 名称
            body (str): Release 描述信息
            target_commitish (str): 目标提交分支或 SHA 值
        
        Returns:
            tuple: (success, result) 
                   - success (bool): 是否成功
                   - result (str): 成功时为 Release ID，失败时为错误信息
        """
        url = f'https://gitee.com/api/v5/repos/{self.owner}/{repo}/releases'
        data = {
            'access_token': self.token,
            'tag_name': tag_name,
            'name': name,
            'body': body,
            'target_commitish': target_commitish,
        }
        response = requests.post(url, data=data)
        response_data = response.json()
        
        # 检查响应状态码是否表示成功（HTTP 2xx）
        if response.status_code < 200 or response.status_code > 300:
            error_message = response_data["message"] if "message" in response_data else f"响应状态码: {response.status_code}"
            return False, error_message

        # 检查响应中是否包含 ID 字段
        if "id" in response_data:
            return True, response_data["id"]
        else:
            return False, "响应中未包含 'id' 字段"

    @retry_decorator(retry_times)
    def upload_asset(self, repo, release_id, files=None, file_name=None, file_path=None):
        """
        向指定的 Release 上传附件
        
        Args:
            repo (str): 仓库名称
            release_id (str): Release ID
            files (list): 文件路径列表
            file_name (str): 单个文件名称
            file_path (str): 单个文件路径
        
        Returns:
            tuple: (success, result)
                   - success (bool): 是否成功
                   - result (str): 成功时为文件下载链接，失败时为错误信息
        """
        # 处理多个文件的情况
        if files:
            fields = [('access_token', self.token)]
            for file_path_item in files:
                file_path_item = file_path_item.strip()
                if not os.path.isfile(file_path_item):
                    raise ValueError('文件不存在: ' + file_path_item)
                file_field = ('file', (os.path.basename(file_path_item),
                                       open(file_path_item, 'rb'), 'application/octet-stream'))
                fields.append(file_field)
        # 处理单个文件的情况
        elif file_name and file_path:
            file_size = os.path.getsize(file_path)
            fields = {
                'access_token': self.token,
                'file': (file_name, open(file_path, 'rb'), 'application/octet-stream'),
            }
        # 参数校验失败
        else:
            raise ValueError('必须提供 files 或同时提供 file_name 和 file_path 参数')
            
        multipart_encoder = MultipartEncoder(fields=fields)
        url = f"https://gitee.com/api/v5/repos/{self.owner}/{repo}/releases/{release_id}/attach_files"
        
        # 创建带进度条的上传包装器
        with logging_redirect_tqdm():
            with tqdm(total=multipart_encoder.len, unit='B', unit_scale=True, desc=f"上传 {file_name}") as pbar:
                class ProgressAdapter:
                    def __init__(self, encoder, progress_bar):
                        self.encoder = encoder
                        self.progress_bar = progress_bar
                        self.monitor = MultipartEncoderMonitor(encoder, self.update_progress)
                    
                    def update_progress(self, monitor):
                        progress = monitor.bytes_read
                        self.progress_bar.update(progress - self.progress_bar.n)
                    
                    def __getattr__(self, item):
                        return getattr(self.monitor, item)
                
                progress_monitor = ProgressAdapter(multipart_encoder, pbar)
                response = requests.post(url, data=progress_monitor,
                                         headers={'Content-Type': multipart_encoder.content_type})
        response_data = response.json()
        
        # 检查响应状态码是否表示成功（HTTP 2xx）
        if response.status_code < 200 or response.status_code > 300:
            error_message = response_data["message"] if "message" in response_data else f"响应状态码: {response.status_code}"
            return False, error_message

        # 检查响应中是否包含下载链接
        if "browser_download_url" in response_data:
            return True, response_data["browser_download_url"]
        else:
            return False, "响应中未包含 'browser_download_url' 字段"


def get_environment_variable(key, default_value=None):
    """
    从环境变量中获取值
    
    Args:
        key (str): 环境变量键名
        default_value (any): 默认值
    
    Returns:
        any: 环境变量值或默认值
    
    Raises:
        ValueError: 当环境变量不存在且无默认值时抛出
    """
    value = os.environ.get(key)
    if not value:
        if default_value is not None:
            return default_value
        raise ValueError(f'环境变量 {key} 未设置')
    return value


def set_action_output(name, result):
    """
    设置 GitHub Actions 的输出结果
    
    Args:
        name (str): 输出变量名称
        result (any): 输出结果值
    """
    logging.info("result: %s=%s", name, result)
    github_output_path = os.environ.get("GITHUB_OUTPUT")
    if github_output_path:
        with open(github_output_path, 'a', encoding='utf-8') as output_file:
            if '\n' not in str(result):
                output_file.write(f"{name}={result}\n")
                logging.info("%s=%s\n", name, result)
            else:
                delimiter = 'EOF'
                output_file.write(f"{name}<<{delimiter}\n{result}\n{delimiter}\n")
                logging.info("%s<<%s\n%s\n%s\n", name, delimiter, result, delimiter)