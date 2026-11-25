"""
高德地图 WebService API 客户端 —— 私有模块，不映射为公开路由。

（改写自腾讯版本：对外三个函数 geocode / place_search / distance_matrix 的
  签名与返回结构保持不变，底层切换为高德，上层 _tools.py 无需改动。）

合规说明：
  - 国内地图服务使用合规服务商高德地图（GCJ-02 坐标系）。
  - 绝不内嵌任何真实 Key。Key 只能来自环境变量 AMAP_API_KEY
    （兼容旧变量名 TENCENT_MAP_KEY，方便直接把高德 Key 填进去）。
  - 若 Key 缺失或仍是占位符，所有调用返回明确错误，不会发起外部请求。

文档参考：
  - 地理编码   https://lbs.amap.com/api/webservice/guide/api/georegeo
  - 关键词搜索 https://lbs.amap.com/api/webservice/guide/api/search
  - 周边搜索   https://lbs.amap.com/api/webservice/guide/api/search#placearound
  - 距离矩阵   https://lbs.amap.com/api/webservice/guide/api/direction#distance
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_BASE = "https://restapi.amap.com/v3"
KEY_ENV = "AMAP_API_KEY"
KEY_FALLBACK_ENV = "TENCENT_MAP_KEY"
KEY_PLACEHOLDER = "请到高德开放平台申请自己的 Key（服务平台选 Web服务）并替换此占位符"
_VALID_MODES = {"driving", "walking", "bicycling", "ebicycling", "straight"}
_TIMEOUT = 15


def key_placeholder_text() -> str:
    return KEY_PLACEHOLDER


def get_key() -> str:
    """返回已配置的 Key；缺失或占位符时返回空串。优先 AMAP_API_KEY，兼容旧 TENCENT_MAP_KEY。"""
    for env in (KEY_ENV, KEY_FALLBACK_ENV):
        value = (os.getenv(env) or "").strip()
        if not value or value == KEY_PLACEHOLDER or value.startswith("<") or "请到" in value:
            continue
        return value
    return ""


def is_key_configured() -> bool:
    return bool(get_key())


def error_json(message: str, hint: str | None = None) -> str:
    payload: dict[str, Any] = {"ok": False, "error": message}
    if hint:
        payload["hint"] = hint
    return json.dumps(payload, ensure_ascii=False)


def _request(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """发起 GET 请求并校验高德 API 的 status（字符串 '1' 为成功）。"""
    key = get_key()
    if not key:
        return {
            "status": -1,
            "message": f"未配置地图 Key：请在环境变量中设置 {KEY_ENV}（{KEY_PLACEHOLDER}）",
        }

    query = dict(params)
    query["key"] = key
    query.setdefault("output", "json")
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(query)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EdgeOne-Agent-Geo/1.0"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except urllib.error.HTTPError as exc:
        return {"status": -1, "message": f"地图服务 HTTP 错误 {exc.code}"}
    except urllib.error.URLError as exc:
        return {"status": -1, "message": f"无法连接地图服务：{exc.reason}"}
    except (ValueError, json.JSONDecodeError):
        return {"status": -1, "message": "地图服务返回内容无法解析为 JSON"}
    except Exception as exc:  # noqa: BLE001 - 网络调用兜底
        return {"status": -1, "message": f"地图服务调用异常：{type(exc).__name__}: {exc}"}

    if not isinstance(data, dict):
        return {"status": -1, "message": "地图服务返回格式异常"}
    if str(data.get("status")) != "1":
        return {
            "status": -1,
            "message": str(data.get("info") or data.get("message") or "地图服务返回错误"),
        }
    data["status"] = 0  # 归一化为上层约定的成功码
    return data


def _s(value: Any) -> str:
    """高德部分字段会返回 [] 或 list，统一转成字符串。"""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(str(x) for x in value)
    return "" if value is None else str(value)


def _parse_lnglat(value: Any) -> tuple[float | None, float | None]:
    """高德 location 为 '经度,纬度' 字符串，转成 (lat, lng)。"""
    if not value or not isinstance(value, str):
        return None, None
    parts = value.split(",")
    if len(parts) < 2:
        return None, None
    try:
        lng, lat = float(parts[0]), float(parts[1])
        return lat, lng
    except (TypeError, ValueError):
        return None, None


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """直线距离（米），用于 straight 模式。"""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def geocode(address: str, policy: int = 1) -> dict[str, Any]:
    """文字地址 -> 经纬度（GCJ-02）。高德 geocode/geo。"""
    data = _request("geocode/geo", {"address": address})
    if data.get("status") != 0:
        return data

    geocodes = data.get("geocodes") or []
    if not geocodes:
        return {"status": -1, "message": "地址解析无结果，请带上城市名重试"}

    item = geocodes[0] or {}
    lat, lng = _parse_lnglat(item.get("location"))
    if lat is None or lng is None:
        return {"status": -1, "message": "地址解析成功但未返回坐标，请换用更具体的位置描述"}

    return {
        "status": 0,
        "result": {
            "title": _s(item.get("formatted_address")) or address,
            "location": {"lat": lat, "lng": lng},
            "address_components": {
                "city": _s(item.get("city")),
                "district": _s(item.get("district")),
                "street": _s(item.get("street")),
            },
            "reliability": None,
            "level": item.get("level"),
        },
    }


def place_search(
    keyword: str,
    boundary: str,
    page_size: int = 20,
    orderby: str | None = None,
    added_fields: str | None = None,
    filters: str | None = None,
    get_subpois: int = 0,
) -> dict[str, Any]:
    """
    地点关键词搜索，返回腾讯风格 data 列表。

    boundary 兼容：
      nearby(lat,lng,radius[,auto_extend])   周边搜索
      region(city[,...])                      城市搜索
      region(poi:ID)                          高德无对应接口，返回错误让上层降级为周边搜索
      rectangle(...)                          退化为城市搜索
    """
    page_size = max(1, min(20, int(page_size)))
    params: dict[str, Any] = {
        "keywords": keyword,
        "offset": page_size,
        "page": 1,
        "extensions": "all",
    }
    path = "place/text"

    boundary = boundary or ""
    match = re.match(r"nearby\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*(\d+)", boundary)
    if match:
        lat, lng, radius = float(match.group(1)), float(match.group(2)), int(match.group(3))
        params["location"] = f"{lng},{lat}"  # 高德坐标顺序：经度,纬度
        params["radius"] = max(100, min(radius, 50000))
        path = "place/around"
    elif boundary.startswith("region(poi:"):
        return {"status": -1, "message": "高德不支持按 POI ID 搜索，改用周边搜索"}
    else:
        match = re.match(r"region\(\s*([^,)]+)", boundary)
        if match:
            params["city"] = match.group(1).strip()

    data = _request(path, params)
    if data.get("status") != 0:
        return data

    pois: list[dict[str, Any]] = []
    for item in data.get("pois") or []:
        lat, lng = _parse_lnglat(item.get("location"))
        try:
            distance = int(float(item.get("distance"))) if item.get("distance") else None
        except (TypeError, ValueError):
            distance = None
        pois.append({
            "id": item.get("id"),
            "title": _s(item.get("name")),
            "address": _s(item.get("address")),
            "category": _s(item.get("type")),
            "location": {"lat": lat, "lng": lng},
            "_distance": distance,
            "tel": _s(item.get("tel")),
        })
    return {"status": 0, "data": pois}


def distance_matrix(
    from_lat: float,
    from_lng: float,
    to_points: list[dict[str, Any]],
    mode: str = "walking",
) -> dict[str, Any]:
    """一对多距离矩阵，返回统一 results 结构。高德 distance。"""
    mode = mode if mode in _VALID_MODES else "walking"
    points = [
        p for p in to_points
        if isinstance(p, dict) and p.get("lat") is not None and p.get("lng") is not None
    ][:20]
    if not points:
        return {"status": -1, "message": "距离矩阵缺少有效终点坐标"}

    def _straight_results() -> list[dict[str, Any]]:
        """直线距离降级结果（高德距离接口不可用时使用）。"""
        out = []
        for point in points:
            distance = _haversine(
                float(from_lat), float(from_lng), float(point["lat"]), float(point["lng"])
            )
            out.append({
                "id": point.get("id"),
                "name": point.get("name"),
                "lat": float(point["lat"]),
                "lng": float(point["lng"]),
                "distance_m": round(distance),
                "distance_km": round(distance / 1000, 2),
                "duration_s": None,
                "duration_min": None,
                "snap_failed": True,
            })
        return out

    if mode == "straight":
        return {"status": 0, "mode": mode, "results": _straight_results()}

    type_map = {"driving": "0", "walking": "1", "bicycling": "2", "ebicycling": "2"}
    origins = f"{float(from_lng)},{float(from_lat)}"
    destinations = ";".join(f"{float(p['lng'])},{float(p['lat'])}" for p in points)
    data = _request("distance", {
        "origins": origins,
        "destination": destinations,
        "type": type_map.get(mode, "1"),
    })
    if data.get("status") != 0:
        # 距离服务不可用（如 Key 未开通 direction/distance）时优雅降级为直线距离，
        # 保证出行推荐流程不中断；用 snap_failed=true 标记非真实路面距离。
        return {"status": 0, "mode": mode, "results": _straight_results(), "degraded": True}

    items = data.get("results") or []
    parsed: list[dict[str, Any]] = []
    for idx, point in enumerate(points):
        element = items[idx] if idx < len(items) else {}
        try:
            distance = int(float(element.get("distance"))) if element.get("distance") else None
        except (TypeError, ValueError):
            distance = None
        try:
            duration = int(float(element.get("duration"))) if element.get("duration") else None
        except (TypeError, ValueError):
            duration = None
        parsed.append({
            "id": point.get("id"),
            "name": point.get("name"),
            "lat": float(point["lat"]),
            "lng": float(point["lng"]),
            "distance_m": distance,
            "distance_km": round(distance / 1000, 2) if distance is not None else None,
            "duration_s": duration,
            "duration_min": round(duration / 60, 1) if duration is not None else None,
            "snap_failed": distance is None,
        })
    return {"status": 0, "mode": mode, "results": parsed}
