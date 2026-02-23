#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气数据爬虫 - 基于 wttr.in API

功能：
    - 获取指定城市的实时天气数据（温度、天气、湿度、风速、降水）
    - 解析 JSON 响应并提取关键信息
    - 保存结果到 weather_data.json（含时间戳）
    - 支持命令行参数指定城市名称

用法：
    python weather_crawler.py Beijing
    python weather_crawler.py --city Shanghai
    python weather_crawler.py  # 默认查询 Beijing
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import requests

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
API_URL_TEMPLATE = "https://wttr.in/{city}?format=j1"
DEFAULT_CITY = "Beijing"
REQUEST_TIMEOUT = 15          # 秒
MAX_RETRIES = 3               # 最大重试次数
OUTPUT_FILE = "weather_data.json"

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def safe_int(value: Any, default: int = 0) -> int:
    """安全地将值转换为 int，失败时返回默认值。"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全地将值转换为 float，失败时返回默认值。"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------
def fetch_weather_json(city: str) -> Dict[str, Any]:
    """
    向 wttr.in 发送请求，返回原始 JSON 字典。

    Args:
        city: 城市名称（英文或中文均可，英文更稳定）

    Returns:
        API 返回的完整 JSON 字典

    Raises:
        requests.exceptions.RequestException: 网络层错误
        json.JSONDecodeError: 响应不是合法 JSON
    """
    url = API_URL_TEMPLATE.format(city=city)
    logger.info("正在请求: %s", url)

    # 带重试的请求
    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            logger.info("请求成功 (第 %d 次尝试)", attempt)
            return data
        except requests.exceptions.Timeout as exc:
            last_error = exc
            logger.warning("请求超时 (第 %d/%d 次)", attempt, MAX_RETRIES)
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
            logger.warning("网络连接失败 (第 %d/%d 次)", attempt, MAX_RETRIES)
        except requests.exceptions.HTTPError as exc:
            # HTTP 4xx/5xx —— 不重试客户端错误
            if exc.response is not None and exc.response.status_code < 500:
                logger.error("HTTP 错误 %s，不再重试", exc.response.status_code)
                raise
            last_error = exc
            logger.warning("服务器错误 (第 %d/%d 次)", attempt, MAX_RETRIES)

    # 所有重试均失败
    raise last_error  # type: ignore[misc]


def parse_weather(data: Dict[str, Any], city: str) -> Dict[str, Any]:
    """
    从 API 原始 JSON 中提取关键天气信息。

    Args:
        data: wttr.in 返回的完整 JSON
        city: 查询的城市名称

    Returns:
        结构化的天气信息字典
    """
    # 校验数据结构
    if "current_condition" not in data or not data["current_condition"]:
        raise ValueError("API 返回数据缺少 current_condition 字段")

    current = data["current_condition"][0]

    # ---- 基础天气信息 ----
    weather_info: Dict[str, Any] = {
        "query_city": city,
        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observation_time": current.get("localObsDateTime", "N/A"),
        "temperature": {
            "current_c": safe_int(current.get("temp_C")),
            "current_f": safe_int(current.get("temp_F")),
            "feels_like_c": safe_int(current.get("FeelsLikeC")),
            "feels_like_f": safe_int(current.get("FeelsLikeF")),
        },
        "weather": {
            "description": current.get("weatherDesc", [{}])[0].get("value", "N/A"),
            "code": current.get("weatherCode", "N/A"),
            "cloud_cover_pct": safe_int(current.get("cloudcover")),
        },
        "humidity_pct": safe_int(current.get("humidity")),
        "wind": {
            "speed_kmph": safe_int(current.get("windspeedKmph")),
            "speed_mph": safe_int(current.get("windspeedMiles")),
            "direction": current.get("winddir16Point", "N/A"),
            "degree": safe_int(current.get("winddirDegree")),
        },
        "precipitation": {
            "current_mm": safe_float(current.get("precipMM")),
            "current_inches": safe_float(current.get("precipInches")),
        },
        "extras": {
            "visibility_km": safe_int(current.get("visibility")),
            "pressure_mb": safe_int(current.get("pressure")),
            "uv_index": safe_int(current.get("uvIndex")),
        },
    }

    # ---- 降水概率（来自今日小时级预报） ----
    weather_list = data.get("weather", [])
    if weather_list and weather_list[0].get("hourly"):
        hourly = weather_list[0]["hourly"][0]
        weather_info["precipitation"]["chance_of_rain_pct"] = safe_int(
            hourly.get("chanceofrain")
        )
        weather_info["precipitation"]["chance_of_snow_pct"] = safe_int(
            hourly.get("chanceofsnow")
        )

    # ---- 位置信息 ----
    nearest = data.get("nearest_area", [{}])[0]
    weather_info["location"] = {
        "area": nearest.get("areaName", [{}])[0].get("value", "N/A"),
        "country": nearest.get("country", [{}])[0].get("value", "N/A"),
        "latitude": nearest.get("latitude", "N/A"),
        "longitude": nearest.get("longitude", "N/A"),
    }

    logger.info(
        "解析完成: %s, %s°C, %s",
        weather_info["weather"]["description"],
        weather_info["temperature"]["current_c"],
        weather_info["location"]["area"],
    )
    return weather_info


def save_to_json(weather_info: Dict[str, Any], filepath: str) -> None:
    """
    将天气数据追加保存到 JSON 文件。

    文件结构为一个列表，每次运行追加一条记录。
    如果文件不存在或格式损坏，则新建。

    Args:
        weather_info: 要保存的天气数据字典
        filepath: 输出文件路径
    """
    records: list = []

    # 尝试读取已有数据
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                logger.warning("已有文件格式不是列表，将重新创建")
                records = []
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("读取已有文件失败 (%s)，将重新创建", exc)
            records = []

    records.append(weather_info)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    logger.info("数据已保存到 %s（共 %d 条记录）", filepath, len(records))


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def run(city: str) -> None:
    """
    执行完整的天气数据采集流程：请求 → 解析 → 保存。

    Args:
        city: 目标城市名称
    """
    logger.info("===== 开始采集天气数据: %s =====", city)

    try:
        raw_data = fetch_weather_json(city)
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "未知"
        logger.error("HTTP 错误 (%s)，可能是城市名称无效: %s", status, city)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        logger.error("网络连接失败，请检查网络后重试")
        sys.exit(1)
    except requests.exceptions.Timeout:
        logger.error("请求超时（已重试 %d 次）", MAX_RETRIES)
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error("API 返回的数据不是合法 JSON")
        sys.exit(1)
    except requests.exceptions.RequestException as exc:
        logger.error("请求异常: %s", exc)
        sys.exit(1)

    try:
        weather_info = parse_weather(raw_data, city)
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.error("数据解析失败: %s", exc)
        sys.exit(1)

    # 输出到控制台（方便查看）
    print("\n" + "=" * 50)
    print(f"  城市: {weather_info['location']['area']}, "
          f"{weather_info['location']['country']}")
    print(f"  温度: {weather_info['temperature']['current_c']}°C "
          f"(体感 {weather_info['temperature']['feels_like_c']}°C)")
    print(f"  天气: {weather_info['weather']['description']}")
    print(f"  湿度: {weather_info['humidity_pct']}%")
    print(f"  风速: {weather_info['wind']['speed_kmph']} km/h "
          f"({weather_info['wind']['direction']})")
    precip = weather_info["precipitation"]
    print(f"  降水: {precip['current_mm']} mm", end="")
    if "chance_of_rain_pct" in precip:
        print(f"  (降雨概率 {precip['chance_of_rain_pct']}%)", end="")
    print()
    print(f"  观测时间: {weather_info['observation_time']}")
    print("=" * 50 + "\n")

    # 保存到文件
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    save_to_json(weather_info, output_path)

    logger.info("===== 采集完成 =====")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="天气数据爬虫 - 基于 wttr.in API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python weather_crawler.py Beijing\n"
               "  python weather_crawler.py --city Shanghai\n"
               "  python weather_crawler.py 东京",
    )
    parser.add_argument(
        "city_pos",
        nargs="?",
        default=None,
        metavar="CITY",
        help="城市名称（位置参数）",
    )
    parser.add_argument(
        "--city", "-c",
        default=None,
        help=f"城市名称（命名参数，默认: {DEFAULT_CITY}）",
    )
    return parser.parse_args()


def main() -> None:
    """入口：解析参数并启动采集。"""
    args = parse_args()
    # 优先使用 --city，其次位置参数，最后默认值
    city = args.city or args.city_pos or DEFAULT_CITY
    run(city)


if __name__ == "__main__":
    main()
