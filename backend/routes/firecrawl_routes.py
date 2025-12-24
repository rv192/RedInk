"""
Firecrawl 相关 API 路由

包含功能：
- 获取 Firecrawl 配置状态
- 抓取网页内容
"""

import logging
from pathlib import Path
import yaml
import requests
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent.parent
FIRECRAWL_CONFIG_PATH = CONFIG_DIR / 'firecrawl_config.yaml'


def create_firecrawl_blueprint():
    """创建 Firecrawl 路由蓝图"""
    firecrawl_bp = Blueprint('firecrawl', __name__)

    @firecrawl_bp.route('/firecrawl/status', methods=['GET'])
    def get_firecrawl_status():
        """
        获取 Firecrawl 配置状态

        返回：
        - success: 是否成功
        - enabled: 是否启用
        - configured: 是否已配置（有 base_url 或 api_key）
        """
        try:
            config = _read_firecrawl_config()
            
            enabled = config.get('enabled', False)
            has_base_url = bool(config.get('base_url', ''))
            has_api_key = bool(config.get('api_key', ''))
            configured = has_base_url or has_api_key
            
            return jsonify({
                "success": True,
                "enabled": enabled,
                "configured": configured
            })
        except Exception as e:
            logger.error(f"获取 Firecrawl 状态失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @firecrawl_bp.route('/firecrawl/scrape', methods=['POST'])
    def scrape_url():
        """
        抓取网页内容

        请求体：
        - url: 要抓取的网页 URL

        返回：
        - success: 是否成功
        - data: 抓取结果
          - title: 网页标题
          - content: Markdown 格式的正文内容
          - word_count: 字数
          - url: 原始 URL
        """
        try:
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({
                    "success": False,
                    "error": "缺少 url 参数"
                }), 400

            # 读取配置
            config = _read_firecrawl_config()
            
            if not config.get('enabled', False):
                return jsonify({
                    "success": False,
                    "error": "Firecrawl 未启用，请先在设置中启用"
                }), 400

            # 调用 Firecrawl API
            result = _scrape_with_firecrawl(url, config)
            
            return jsonify(result)

        except Exception as e:
            logger.error(f"抓取网页失败: {e}")
            return jsonify({
                "success": False,
                "error": f"抓取失败: {str(e)}"
            }), 500

    return firecrawl_bp


def _read_firecrawl_config() -> dict:
    """读取 Firecrawl 配置"""
    if FIRECRAWL_CONFIG_PATH.exists():
        with open(FIRECRAWL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {
        'enabled': False,
        'api_key': '',
        'base_url': ''
    }


def _scrape_with_firecrawl(url: str, config: dict) -> dict:
    """
    使用 Firecrawl 抓取网页

    Args:
        url: 要抓取的 URL
        config: Firecrawl 配置

    Returns:
        抓取结果
    """
    base_url = config.get('base_url', '').rstrip('/') or 'https://api.firecrawl.dev'
    api_key = config.get('api_key', '')
    
    # 构建请求
    scrape_url = f"{base_url}/v1/scrape"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    payload = {
        'url': url,
        'formats': ['markdown']
    }
    
    logger.info(f"🌐 开始抓取网页: {url}")
    
    try:
        response = requests.post(
            scrape_url,
            headers=headers,
            json=payload,
            timeout=60  # 抓取可能需要较长时间
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 解析 Firecrawl 响应
            if result.get('success') or result.get('data'):
                data = result.get('data', {})
                
                # 获取 markdown 内容
                content = data.get('markdown', '')
                
                # 获取元数据
                metadata = data.get('metadata', {})
                title = metadata.get('title', '') or metadata.get('ogTitle', '') or '未知标题'
                
                # 计算字数（中文按字符计算）
                word_count = len(content)
                
                logger.info(f"✅ 网页抓取成功: {title[:50]}... ({word_count} 字)")
                
                return {
                    "success": True,
                    "data": {
                        "title": title,
                        "content": content,
                        "word_count": word_count,
                        "url": url
                    }
                }
            else:
                error_msg = result.get('error', '未知错误')
                logger.error(f"❌ Firecrawl 返回错误: {error_msg}")
                return {
                    "success": False,
                    "error": f"抓取失败: {error_msg}"
                }
        
        elif response.status_code == 401:
            logger.error("❌ Firecrawl API Key 无效")
            return {
                "success": False,
                "error": "API Key 无效或未提供"
            }
        
        elif response.status_code == 402:
            logger.error("❌ Firecrawl API 配额已用尽")
            return {
                "success": False,
                "error": "API 配额已用尽"
            }
        
        else:
            error_text = response.text[:200]
            logger.error(f"❌ Firecrawl 请求失败: HTTP {response.status_code} - {error_text}")
            return {
                "success": False,
                "error": f"请求失败: HTTP {response.status_code}"
            }
    
    except requests.exceptions.Timeout:
        logger.error(f"❌ 抓取超时: {url}")
        return {
            "success": False,
            "error": "抓取超时，请稍后重试"
        }
    
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ 无法连接 Firecrawl 服务: {base_url}")
        return {
            "success": False,
            "error": f"无法连接到 Firecrawl 服务: {base_url}"
        }
