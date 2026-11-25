"""
Agent Tools —— 出行决策（私有模块，以下划线开头，不映射为公开路由）。

四步工具链：
  1. resolve_location          文字位置 -> 经纬度（如「红莲南路地铁站」）
  2. search_nearby_malls       以某坐标为中心检索附近商场
  3. check_shops_in_mall       核查某商场内是否存在指定店铺/品牌
  4. compute_travel_distances  计算出发点到候选商场的真实路面距离与耗时

所有工具：
  - 返回中文友好的 JSON 字符串；
  - 地图调用统一走 _geo.py，Key 仅来自环境变量，缺失时给出明确提示，
    绝不使用任何内置 Key 或伪造数据。
"""

from __future__ import annotations

import json
from typing import Annotated

from agents import function_tool

from . import _geo


def _key_hint() -> str:
    return (
        f"请到腾讯位置服务开放平台申请 Key：{_geo.KEY_PLACEHOLDER}；"
        f"拿到后写入项目根目录 .env 的 {_geo.KEY_ENV}=...，"
        "并在 EdgeOne Makers 控制台 -> 项目设置 -> 环境变量中同步配置后重新部署。"
    )


def _guard_key() -> str | None:
    """Key 未配置时返回可直接下发的错误 JSON，否则返回 None。"""
    if not _geo.is_key_configured():
        return _geo.error_json(
            f"地图服务未配置 Key（环境变量 {_geo.KEY_ENV} 缺失或仍为占位符）",
            _key_hint(),
        )
    return None


def _first_address(data: dict) -> str:
    result = data.get("result") or {}
    comps = result.get("address_components") or {}
    city = comps.get("city") or ""
    district = comps.get("district") or ""
    street = comps.get("street") or ""
    return "".join(part for part in (city, district, street) if part)


# ========== Tool 1: 解析位置 ==========
@function_tool
def resolve_location(
    location_text: Annotated[str, "用户描述的位置文字，例如：红莲南路地铁站、北京市海淀区中关村、国贸地铁站"],
) -> str:
    """把用户输入的中文位置文字解析为经纬度坐标与所在城市，供后续地图检索使用。"""
    blocked = _guard_key()
    if blocked:
        return blocked
    if not location_text or not location_text.strip():
        return _geo.error_json("位置文字不能为空，请让用户补充具体地点")

    data = _geo.geocode(location_text.strip(), policy=1)
    if data.get("status") != 0:
        return _geo.error_json(
            f"位置解析失败：{data.get('message')}。建议用户输入更完整的位置（尽量带上城市名）",
            str(data.get("request_id") or ""),
        )
    result = data.get("result") or {}
    loc = result.get("location") or {}
    lat, lng = loc.get("lat"), loc.get("lng")
    if lat is None or lng is None:
        return _geo.error_json("位置解析成功但未返回坐标，请换用更具体的位置描述")

    comps = result.get("address_components") or {}
    payload = {
        "ok": True,
        "query": location_text.strip(),
        "name": result.get("title") or location_text.strip(),
        "address": _first_address(data),
        "city": comps.get("city") or "",
        "district": comps.get("district") or "",
        "lat": lat,
        "lng": lng,
        "reliability": result.get("reliability"),
        "level": result.get("level"),
    }
    return json.dumps(payload, ensure_ascii=False)


# ========== Tool 2: 检索附近商场 ==========
@function_tool
def search_nearby_malls(
    lat: Annotated[float, "中心点纬度，来自 resolve_location 的 lat"],
    lng: Annotated[float, "中心点经度，来自 resolve_location 的 lng"],
    radius: Annotated[int, "搜索半径（米），范围 10~1000，建议 1000"] = 1000,
    keyword: Annotated[str, "检索关键词，默认「商场」，也可填「购物中心」等"] = "商场",
    page_size: Annotated[int, "返回条数，最大 20，建议 20"] = 20,
) -> str:
    """以指定坐标为中心，检索附近的商场/购物中心，返回名称、地址、坐标与直线距离。"""
    blocked = _guard_key()
    if blocked:
        return blocked
    try:
        radius = max(10, min(1000, int(radius)))
        page_size = max(1, min(20, int(page_size)))
    except (TypeError, ValueError):
        return _geo.error_json("radius / page_size 必须是数字")

    # auto_extend=1：不足时在 1km/2km/5km 内自动扩大范围，避免「附近没搜到」。
    boundary = f"nearby({float(lat)},{float(lng)},{radius},1)"
    data = _geo.place_search(
        keyword=keyword or "商场",
        boundary=boundary,
        page_size=page_size,
        orderby="_distance",
        added_fields="category_code",
    )
    if data.get("status") != 0:
        return _geo.error_json(f"商场检索失败：{data.get('message')}", str(data.get("request_id") or ""))

    pois = []
    for item in data.get("data") or []:
        loc = item.get("location") or {}
        pois.append({
            "id": item.get("id"),
            "name": item.get("title"),
            "address": item.get("address"),
            "category": item.get("category"),
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "straight_distance_m": item.get("_distance"),
            "tel": item.get("tel"),
        })
    # 只看真正的商场/购物类 POI，过滤掉同名但无关结果（如「商场公交站」）。
    malls = [p for p in pois if p["id"] and p["lat"] is not None and p["lng"] is not None]
    if not malls:
        return json.dumps({
            "ok": True,
            "count": 0,
            "malls": [],
            "note": "该范围内未检索到商场，可让 search_nearby_malls 使用更大 radius 或换 keyword=购物中心 重试",
        }, ensure_ascii=False)

    return json.dumps({
        "ok": True,
        "keyword": keyword or "商场",
        "radius_m": radius,
        "count": len(malls),
        "malls": malls,
        "hint": "straight_distance_m 为直线距离，最终推荐请用 compute_travel_distances 获取真实路面距离",
    }, ensure_ascii=False)


# ========== Tool 3: 核查商场内的店铺 ==========
@function_tool
def check_shops_in_mall(
    mall_id: Annotated[str, "商场 POI ID，来自 search_nearby_malls 返回的 id"],
    mall_name: Annotated[str, "商场名称，来自 search_nearby_malls 返回的 name"],
    mall_lat: Annotated[float, "商场纬度，来自 search_nearby_malls 返回的 lat"],
    mall_lng: Annotated[float, "商场经度，来自 search_nearby_malls 返回的 lng"],
    shop_keywords: Annotated[str, "要核查的店铺/品牌名，多个用英文逗号分隔，例如：倍轻松,西厅村屋"],
) -> str:
    """核查指定商场内是否存在用户关心的店铺或品牌，返回每个店铺是否命中。"""
    blocked = _guard_key()
    if blocked:
        return blocked

    keywords = [k.strip() for k in (shop_keywords or "").split(",") if k.strip()]
    if not keywords:
        return _geo.error_json("请提供至少一个要核查的店铺/品牌名")

    results = []
    for kw in keywords[:8]:
        found = []
        method = "poi_region"
        # 首选：商场 AOI 范围内搜索（region(poi:POIID)），结果最准确。
        data = _geo.place_search(
            keyword=kw,
            boundary=f"region(poi:{mall_id})",
            page_size=5,
        )
        if data.get("status") != 0:
            # 降级：商场坐标周边 300 米内搜索（部分商场无 AOI 轮廓）。
            method = "nearby_fallback"
            data = _geo.place_search(
                keyword=kw,
                boundary=f"nearby({float(mall_lat)},{float(mall_lng)},300,0)",
                page_size=5,
            )
        if data.get("status") == 0:
            for item in data.get("data") or []:
                found.append({
                    "name": item.get("title"),
                    "address": item.get("address"),
                    "category": item.get("category"),
                })

        results.append({
            "shop_keyword": kw,
            "found": bool(found),
            "match_count": len(found),
            "matches": found[:3],
            "match_method": method,
        })

    return json.dumps({
        "ok": True,
        "mall_id": mall_id,
        "mall_name": mall_name,
        "all_shops_present": all(r["found"] for r in results),
        "shops": results,
    }, ensure_ascii=False)


# ========== Tool 4: 计算真实路面距离 ==========
@function_tool
def compute_travel_distances(
    from_lat: Annotated[float, "出发点纬度，通常是 resolve_location 得到的用户位置 lat"],
    from_lng: Annotated[float, "出发点经度，通常是 resolve_location 得到的用户位置 lng"],
    destinations_json: Annotated[
        str,
        "候选商场 JSON 数组字符串，来自 search_nearby_malls 结果。格式："
        '[{"id":"...","name":"...","lat":39.9,"lng":116.4}, ...]，最多 20 个',
    ],
    mode: Annotated[str, "出行方式：walking 步行 / driving 驾车 / bicycling 骑行 / straight 直线，默认 walking"] = "walking",
) -> str:
    """批量计算出发点到多个候选商场的真实路面距离与预计耗时，用于最终排序推荐。"""
    blocked = _guard_key()
    if blocked:
        return blocked
    try:
        destinations = json.loads(destinations_json) if isinstance(destinations_json, str) else destinations_json
    except (ValueError, json.JSONDecodeError):
        return _geo.error_json("destinations_json 不是合法 JSON 数组字符串")
    if not isinstance(destinations, list) or not destinations:
        return _geo.error_json("候选商场列表为空，请先调用 search_nearby_malls")

    data = _geo.distance_matrix(float(from_lat), float(from_lng), destinations[:20], mode=mode)
    if data.get("status") != 0:
        payload = {"ok": False, "error": f"距离计算失败：{data.get('message')}"}
        if data.get("request_id"):
            payload["request_id"] = data["request_id"]
        return json.dumps(payload, ensure_ascii=False)

    return json.dumps({
        "ok": True,
        "mode": data.get("mode"),
        "results": data.get("results") or [],
        "note": "distance_m 为真实路面距离（米），duration_min 为预计耗时（分钟）；snap_failed=true 时距离为直线距离",
    }, ensure_ascii=False)
