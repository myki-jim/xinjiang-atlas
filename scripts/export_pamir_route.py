#!/usr/bin/env python3
"""Export the selected 7-day Shache road trip as one large, self-contained PNG.

Run with --fetch-routes once to refresh the OSRM road geometry. Normal runs are
offline and use the reviewed road geometry snapshot in public/data/routes.
The travel plan and stop expansion mirror src/routes.js and src/main.js as of
the snapshot date; this is a shareable editorial itinerary, not navigation.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DATA = ROOT / "public/data/routes/pamir-7-slow-full-osrm.json"
OUTPUT = ROOT / "public/exports/pamir-shache-7-day-road-trip.png"
W, H = 10000, 7000
FONT = next((str(path) for path in [
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("C:/Windows/Fonts/msyh.ttc"),
] if path.exists()), None)
COLORS = ["#BD7C39", "#D46A4B", "#338E94", "#A373BD", "#78956A", "#587DB2", "#C06466"]
BG, INK, MUTED, SEA = "#F5F2EA", "#173C39", "#6C7D76", "#214846"

# Snapshot of the actual full-pace stops in the selected route. The five OSM
# nodes/ways are copied from src/osmPlaces.json / src/landmarkPlaces.json.
PLACES = {
    "kashgar": ("喀什古城", 75.99197, 39.47233),
    "gaotai": ("高台民居", 76.00002, 39.47021),
    "oytakh": ("奥依塔克红山峡谷", 75.49382, 38.94759),
    "baisha": ("白沙湖 · 布伦口", 74.97811, 38.69106),
    "osm-n12421270105": ("白沙湖二号观景台", 74.968675, 38.688316),
    "karakul": ("喀拉库勒湖", 75.056133, 38.443394),
    "stone-city": ("石头城遗址", 75.232631, 37.7823),
    "panlong": ("盘龙古道", 75.600375, 37.639883),
    "osm-n13129567998": ("班迪尔蓝湖北岸观景台", 75.42806, 37.838754),
    "osm-n13129567995": ("班迪尔蓝湖南岸观景台", 75.441558, 37.821215),
    "osm-n4808866521": ("塔合曼湿地公园观景台", 75.185192, 37.923306),
    "shache": ("莎车老城", 77.25477, 38.41517),
    "osm-w958776273": ("叶尔羌汗国王陵", 77.256071, 38.416231),
}

DAYS = [
    {"title": "喀什慢起步", "stay": "喀什", "stops": ["kashgar", "gaotai"],
     "line": ["喀什古城", "高台民居"]},
    {"title": "白沙山与湖岸", "stay": "布伦口附近", "stops": ["kashgar", "oytakh", "baisha", "osm-n12421270105"],
     "line": ["喀什", "奥依塔克红山", "白沙湖", "二号观景台"]},
    {"title": "雪峰、喀拉库勒湖", "stay": "塔什库尔干", "stops": ["baisha", "karakul", "stone-city"],
     "line": ["白沙湖", "喀拉库勒湖", "石头城"]},
    {"title": "盘龙与班迪尔蓝湖", "stay": "塔什库尔干", "stops": ["stone-city", "panlong", "osm-n13129567998", "osm-n13129567995", "stone-city"],
     "line": ["石头城", "盘龙古道", "班迪尔北岸", "班迪尔南岸", "石头城"]},
    {"title": "塔合曼湿地、返回喀什", "stay": "喀什", "stops": ["stone-city", "osm-n4808866521", "kashgar"],
     "line": ["石头城", "塔合曼湿地", "喀什"]},
    {"title": "叶尔羌古城街巷", "stay": "莎车", "stops": ["kashgar", "shache", "osm-w958776273"],
     "line": ["喀什", "莎车老城", "王陵"]},
    {"title": "莎车晨光、回到喀什", "stay": "喀什 / 返程", "stops": ["shache", "kashgar"],
     "line": ["莎车", "喀什"]},
]


def font(size: int) -> ImageFont.FreeTypeFont:
    if FONT is None:
        raise RuntimeError("Install a CJK font such as Noto Sans CJK, then rerun the exporter")
    return ImageFont.truetype(FONT, size)


def px(lon: float, lat: float) -> tuple[float, float]:
    # Local equirectangular projection. Different x/y scales account roughly
    # for longitude convergence near 39° N, without pretending survey accuracy.
    return (1110 + (lon - 74.4) * 1450, 1370 + (39.83 - lat) * 1870)


def fetch_routes() -> dict:
    """Fetch seven modest, independent routes; keep responses for offline use."""
    output = {"provider": "OSRM public demo service, OpenStreetMap contributors", "days": []}
    for number, day in enumerate(DAYS, 1):
        coords = ";".join(f"{PLACES[stop][1]},{PLACES[stop][2]}" for stop in day["stops"])
        url = ("https://router.project-osrm.org/route/v1/driving/" + coords +
               "?overview=full&geometries=geojson&steps=false")
        request = urllib.request.Request(url, headers={"User-Agent": "XinjiangAtlas/1.0 route-poster (noncommercial)"})
        with urllib.request.urlopen(request, timeout=40) as response:
            data = json.load(response)
        if data.get("code") != "Ok" or not data.get("routes"):
            raise RuntimeError(f"Day {number}: routing failed: {data.get('code')}")
        route = data["routes"][0]
        snaps = [round(waypoint["distance"]) for waypoint in data["waypoints"]]
        print(f"D{number}: {route['distance']/1000:.1f} km, "
              f"{len(route['geometry']['coordinates'])} geometry points, snaps {snaps} m")
        if max(snaps) > 6500:
            raise RuntimeError(f"Day {number}: waypoint is over 6.5 km from a routable road; review route")
        output["days"].append({"stops": day["stops"], "distance_m": route["distance"],
                               "geometry": route["geometry"]["coordinates"],
                               "snapped": [w["location"] for w in data["waypoints"]],
                               "snap_distance_m": snaps})
        time.sleep(0.45)
    ROUTE_DATA.parent.mkdir(parents=True, exist_ok=True)
    ROUTE_DATA.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return output


def line_width(draw: ImageDraw.ImageDraw, points, color, width, joint="curve"):
    if len(points) > 1:
        draw.line(points, fill=color, width=width, joint=joint)


def draw_arrow(draw: ImageDraw.ImageDraw, points, color, radius=29):
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    if total < 170:
        return
    target = total * 0.61
    done = 0
    for (x0, y0), (x1, y1), segment in zip(points, points[1:], lengths):
        if done + segment >= target and segment:
            part = (target - done) / segment
            x, y = x0 + (x1-x0)*part, y0 + (y1-y0)*part
            theta = math.atan2(y1-y0, x1-x0)
            # White keyline keeps arrow legible over overlapping trip legs.
            poly = [(x + radius*math.cos(theta), y + radius*math.sin(theta)),
                    (x - radius*.68*math.cos(theta) + radius*.70*math.sin(theta),
                     y - radius*.68*math.sin(theta) - radius*.70*math.cos(theta)),
                    (x - radius*.68*math.cos(theta) - radius*.70*math.sin(theta),
                     y - radius*.68*math.sin(theta) + radius*.70*math.cos(theta))]
            draw.polygon(poly, fill=color)
            return
        done += segment


def dotted(draw: ImageDraw.ImageDraw, a, b, color, radius=5, step=25):
    distance = math.dist(a, b)
    if not distance:
        return
    for n in range(0, int(distance), step):
        x = a[0] + (b[0]-a[0])*n/distance
        y = a[1] + (b[1]-a[1])*n/distance
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)


def draw_geometry(draw, data):
    # Adjacent days reuse parts of G314. Small screen-space offsets keep each
    # coloured pass visible. They are graphic offsets, not separate roads.
    offsets = [-13, -8, 2, 0, 14, -17, 17]
    for i, day_route in enumerate(data["days"]):
        coords = day_route["geometry"]
        points = [px(lon, lat) for lon, lat in coords]
        offset = offsets[i]
        points = [(x+offset, y+offset) for x, y in points]
        line_width(draw, points, "#FFFDF8", 41)
        line_width(draw, points, COLORS[i], 23)
        # Draw direction on long successive legs, and only one on tiny ones.
        boundaries = [tuple(px(*loc)) for loc in day_route["snapped"]]
        prev = 0
        for end in boundaries[1:]:
            matched = min(range(prev, len(points)), key=lambda k: math.dist(points[k], (end[0]+offset, end[1]+offset)))
            leg = points[prev:matched+1]
            if len(leg) > 2 and sum(math.dist(a,b) for a,b in zip(leg,leg[1:])) > 200:
                draw_arrow(draw, leg, COLORS[i], radius=42)
            prev = matched
        # The road route snaps to the nearest road, not to the scenic anchor.
        for stop, snapped in zip(DAYS[i]["stops"], day_route["snapped"]):
            anchor = px(PLACES[stop][1], PLACES[stop][2])
            road = px(*snapped)
            if math.dist(anchor, road) > 16:
                dotted(draw, road, anchor, COLORS[i], 5, 28)


def round_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)


def text(draw, xy, string, size, fill=INK, anchor=None, spacing=10):
    draw.multiline_text(xy, string, fill=fill, font=font(size), anchor=anchor, spacing=spacing)


def base_map(im, draw):
    box = (285, 1015, 6420, 6450)
    round_rect(draw, box, 60, "#E8EBDD")
    # The cropped Xinjiang polygon is the atlas's own public/data boundary.
    boundary = json.loads((ROOT / "public/data/xinjiang.geojson").read_text())
    rings = boundary["geometry"]["coordinates"]
    layer = Image.new("RGBA", (box[2]-box[0], box[3]-box[1]), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    for ring in rings:
        projected = [(px(lon, lat)[0]-box[0], px(lon, lat)[1]-box[1]) for lon, lat in ring]
        layer_draw.polygon(projected, fill="#E8EBDD")
        layer_draw.line(projected, fill="#C2CCBE", width=5, joint="curve")
    rounded_mask = Image.new("L", layer.size)
    ImageDraw.Draw(rounded_mask).rounded_rectangle((0, 0, *layer.size), radius=60, fill=255)
    im.paste(layer, box[:2], ImageChops.multiply(layer.getchannel("A"), rounded_mask))
    # Coordinate grid is the positional context; muted decorative stipples do
    # not claim to be elevation contours or mapped tracks.
    for lon in [74.5, 75, 75.5, 76, 76.5, 77, 77.5]:
        x = px(lon, 39)[0]
        draw.line((x, 1240, x, 6240), fill="#D5DED3", width=2)
        text(draw, (x+13, 6270), f"{lon:g}° E", 27, "#9BAAA0")
    for lat in [37.5, 38, 38.5, 39, 39.5]:
        y = px(75, lat)[1]
        draw.line((420, y, 6170, y), fill="#D5DED3", width=2)
        text(draw, (470, y+15), f"{lat:g}° N", 27, "#9BAAA0")
    text(draw, (493, 1168), "地理位置  /  途经地点", 42, "#58716A")
    text(draw, (4800, 1180), "N ↑", 58, SEA)
    text(draw, (465, 6060), "PAMIR PLATEAU / 帕米尔高原", 39, "#9AA99A")
    text(draw, (4760, 5930), "YARKAND / 叶尔羌", 38, "#9AA99A")
    # The boundary above is deliberately pale; it is not a road or route.


def legend(draw):
    text(draw, (430, 5585), "每天的颜色", 34, MUTED)
    for i, color in enumerate(COLORS):
        x = 435 + i*780
        round_rect(draw, (x, 5688, x+42, 5730), 16, color)
        text(draw, (x+57, 5683), f"D{i+1}", 47, INK)
    text(draw, (435, 5845), "→ 行进方向    • 景点锚点    ⋯ 道路与景点的连接", 37, MUTED)


def point_labels(draw):
    # Nearby coordinates are grouped on the map; all 13 distinct stops and
    # every repeat visit are spelled out in the ordered itinerary at right.
    clusters = [
        (["kashgar", "gaotai"], "01–02", "喀什古城 · 高台民居", (3535, 1510), 1205),
        (["oytakh"], "03", "奥依塔克红山", (3060, 2490), 1110),
        (["baisha", "osm-n12421270105"], "04–05", "白沙湖 · 二号观景台", (550, 2980), 1260),
        (["karakul"], "06", "喀拉库勒湖", (535, 3740), 1020),
        (["osm-n4808866521"], "11", "塔合曼湿地", (410, 4360), 1120),
        (["stone-city"], "07", "石头城遗址", (480, 5070), 1060),
        (["osm-n13129567998", "osm-n13129567995"], "09–10", "班迪尔蓝湖 · 南北岸", (3400, 4570), 1290),
        (["panlong"], "08", "盘龙古道", (3660, 5525), 970),
        (["shache", "osm-w958776273"], "12–13", "莎车老城 · 王陵", (4810, 3370), 1250),
    ]
    for ids, number, label, (x, y), width in clusters:
        lon = sum(PLACES[item][1] for item in ids)/len(ids)
        lat = sum(PLACES[item][2] for item in ids)/len(ids)
        ax, ay = px(lon, lat)
        # Connect center of badge to its precise map coordinate.
        target_x = min(max(ax, x), x+width)
        target_y = min(max(ay, y), y+145)
        draw.line((ax, ay, target_x, target_y), fill="#647F74", width=4)
        draw.ellipse((ax-21, ay-21, ax+21, ay+21), fill="#FFFDF8", outline=SEA, width=7)
        round_rect(draw, (x, y, x+width, y+145), 44, "#FFFDF8", "#C6D4CA", 3)
        round_rect(draw, (x+18, y+25, x+185, y+120), 29, SEA)
        text(draw, (x+100, y+72), number, 39 if len(number)>2 else 52, "#FFFFFF", anchor="mm")
        text(draw, (x+210, y+69), label, 48, INK, anchor="lm")


def right_panel(draw, data):
    round_rect(draw, (6590, 1015, 9720, 6450), 60, "#FFFDF8")
    text(draw, (6800, 1130), "DAILY ROADBOOK", 42, "#81958C")
    text(draw, (6800, 1220), "逐日顺序", 84, INK)
    text(draw, (6800, 1360), "由上往下读；重复地点表示折返或夜宿。", 41, MUTED)
    cy = 1520
    for number, day in enumerate(DAYS, 1):
        color = COLORS[number-1]
        y = cy+(number-1)*678
        round_rect(draw, (6770, y, 9545, y+638), 35, "#F4F4EC")
        round_rect(draw, (6820, y+54, 6965, y+191), 37, color)
        text(draw, (6892, y+124), f"D{number}", 51, "#FFFFFF", anchor="mm")
        text(draw, (7030, y+60), day["title"], 63, INK)
        road_km = round(data["days"][number-1]["distance_m"] / 1000)
        text(draw, (7030, y+156), f"夜宿 {day['stay']}  ·  自驾约 {road_km} km", 37, MUTED)
        draw.line((6830, y+245, 9490, y+245), fill="#DAE2D7", width=3)
        # Two rows and explicit arrows fit the densest day with five stops.
        names = day["line"]
        if len(names) == 5:
            rows = [names[:3], names[3:]]
        elif len(names) == 4:
            rows = [names[:2], names[2:]]
        else:
            rows = [names]
        for row_i, row in enumerate(rows):
            ry = y+325+row_i*125
            out = "  →  ".join(row)
            size = 46 if len(out) < 27 else 39
            text(draw, (6835, ry), out, size, INK)
        if len(rows) == 1:
            text(draw, (6835, y+500), "顺序见地图中的同色路线", 36, "#889B8F")
        else:
            text(draw, (6835, y+562), "↳ 接续上方，沿同色线路前进", 34, "#889B8F")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch-routes", action="store_true", help="refresh publicly routed road geometry")
    args = parser.parse_args()
    data = fetch_routes() if args.fetch_routes else json.loads(ROUTE_DATA.read_text())
    assert [item["stops"] for item in data["days"]] == [day["stops"] for day in DAYS], "Route snapshot differs from selected stops"

    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    round_rect(draw, (0, 0, W, 825), 0, SEA)
    text(draw, (350, 127), "经纬  /  XINJIANG ATLAS", 47, "#C4DDD4")
    text(draw, (335, 242), "帕米尔与莎车 · 七日行进图", 140, "#FFFDF8")
    text(draw, (355, 525), "喀什出发，途经红山与高原湖，抵达莎车后返回喀什。", 60, "#D5E4D9")
    round_rect(draw, (7690, 212, 9670, 385), 82, "#D8E7D7")
    text(draw, (8680, 296), "7 天   /   莎车慢行   /   自驾   /   多点摄影", 49, SEA, anchor="mm")
    total_km = round(sum(day["distance_m"] for day in data["days"]) / 1000)
    text(draw, (7720, 550), f"13 个独立地图锚点  ·  道路估算约 {total_km:,} km", 48, "#D8E7D7")

    base_map(im, draw)
    draw_geometry(draw, data)
    point_labels(draw)
    legend(draw)
    right_panel(draw, data)

    text(draw, (340, 6650), "道路线条与里程据 OSRM / OpenStreetMap 估算；景点为位置锚点，色线的细微错位用于区分往返。此图用于行程总览，不是实时导航。", 35, MUTED)
    text(draw, (340, 6740), "景区入口、盘龙古道通行及国庆道路情况，以出发时的官方信息和实地导航为准。地图数据 © OpenStreetMap contributors · ODbL", 33, MUTED)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT} ({W} × {H}; {OUTPUT.stat().st_size/1048576:.1f} MiB)")


if __name__ == "__main__":
    main()
