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
W, H = 10000, 6600
MAP_BOX = (260, 760, 6430, 6140)
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
    return (660 + (lon - 74.7) * 1830, 1050 + (39.62 - lat) * 2050)


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
        line_width(draw, points, "#FFFDF8", 45)
        line_width(draw, points, COLORS[i], 27)
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
    box = MAP_BOX
    round_rect(draw, box, 54, "#E7EBDC")
    # The cropped Xinjiang polygon is the atlas's own public/data boundary.
    boundary = json.loads((ROOT / "public/data/xinjiang.geojson").read_text())
    rings = boundary["geometry"]["coordinates"]
    layer = Image.new("RGBA", (box[2]-box[0], box[3]-box[1]), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    for ring in rings:
        projected = [(px(lon, lat)[0]-box[0], px(lon, lat)[1]-box[1]) for lon, lat in ring]
        layer_draw.polygon(projected, fill="#E7EBDC")
        layer_draw.line(projected, fill="#C2CCBE", width=5, joint="curve")
    rounded_mask = Image.new("L", layer.size)
    ImageDraw.Draw(rounded_mask).rounded_rectangle((0, 0, *layer.size), radius=54, fill=255)
    im.paste(layer, box[:2], ImageChops.multiply(layer.getchannel("A"), rounded_mask))
    # Graticule, nearby towns, highway names and a truthful local scale give
    # positional context without presenting decorative relief as elevation.
    for lon in [75, 75.5, 76, 76.5, 77, 77.5]:
        x = px(lon, 39)[0]
        draw.line((x, 870, x, 5995), fill="#CFD9CC", width=2)
        text(draw, (x+14, 6000), f"{lon:g}° E", 30, "#87998D")
    for lat in [37.5, 38, 38.5, 39, 39.5]:
        y = px(75, lat)[1]
        draw.line((380, y, 6270, y), fill="#CFD9CC", width=2)
        text(draw, (395, y+14), f"{lat:g}° N", 28, "#87998D")
    text(draw, (420, 850), "南疆  /  帕米尔—叶尔羌局部", 48, "#56736A")
    text(draw, (4590, 849), "N ↑", 59, SEA)

    for x, y, label in [
        (*px(75.99197, 39.47233), "喀什市"),
        (*px(74.97811, 38.69106), "布伦口"),
        (*px(75.232631, 37.7823), "塔什库尔干"),
        (*px(77.25477, 38.41517), "莎车县"),
    ]:
        draw.ellipse((x-11, y-11, x+11, y+11), fill=SEA)
        # Destination callouts below name the sights; town names in the inset
        # and at the roadside explain where each segment sits.
    round_rect(draw, (3160, 2820, 4210, 2900), 30, "#FFFFFFCB")
    text(draw, (3685, 2860), "G314  中巴公路", 40, "#698078", anchor="mm")
    round_rect(draw, (4300, 2490, 5500, 2570), 30, "#FFFFFFCB")
    text(draw, (4900, 2530), "喀什—莎车通道", 39, "#698078", anchor="mm")
    text(draw, (445, 2220), "克州 · 阿克陶", 42, "#A5B1A0")
    text(draw, (4460, 3000), "喀什地区", 42, "#A5B1A0")

    # A miniature outline of Xinjiang locates this crop in the province.
    inset = (5100, 940, 6225, 1835)
    round_rect(draw, inset, 38, "#FFFDF6", "#D3DED0", 3)
    text(draw, (5190, 997), "新疆 / 当前区域", 43, INK)
    lon_min, lon_max, lat_min, lat_max = 73.2, 96.8, 34.2, 49.5
    def mini(lon, lat):
        return (5195 + (lon-lon_min)/(lon_max-lon_min)*940,
                1190 + (lat_max-lat)/(lat_max-lat_min)*565)
    for ring in rings:
        draw.polygon([mini(lon, lat) for lon, lat in ring], fill="#DBE5D5", outline="#9CB2A4", width=3)
    route_corner = mini(75.7, 38.65)
    draw.ellipse((route_corner[0]-30, route_corner[1]-30, route_corner[0]+30, route_corner[1]+30),
                 fill="#D46A4B", outline="#FFFDF6", width=8)
    text(draw, (5720, 1700), "●  南疆行程范围", 30, "#688076")

    # At ~39° N, 50 km east-west occupies about this many image pixels.
    scale_px = 50 / (111.32 * math.cos(math.radians(39))) * 1830
    sx, sy = 450, 5775
    draw.line((sx, sy, sx+scale_px, sy), fill=INK, width=12)
    draw.line((sx, sy-22, sx, sy+22), fill=INK, width=8)
    draw.line((sx+scale_px, sy-22, sx+scale_px, sy+22), fill=INK, width=8)
    text(draw, (sx, sy+33), "0", 34, SEA)
    text(draw, (sx+scale_px-115, sy+33), "约 50 km", 34, SEA)


def legend(draw):
    text(draw, (1970, 5735), "每日线色", 36, MUTED)
    for i, color in enumerate(COLORS):
        x = 1970 + i*555
        round_rect(draw, (x, 5802, x+40, 5842), 16, color)
        text(draw, (x+50, 5790), f"D{i+1}", 46, INK)
    text(draw, (1970, 5935), "箭头 = 行进方向    ◯ = 地点锚点    虚线 = 道路至景点", 35, MUTED)


def point_labels(draw):
    # Small editorial stickers sit next to geographic anchors. Paired stops
    # remain grouped only on the map; the roadbook preserves every visit.
    clusters = [
        (["kashgar", "gaotai"], "01–02", "喀什古城 · 高台民居", "老城街巷  /  日落人文", (3010, 1035), 1420, 0),
        (["oytakh"], "03", "奥依塔克红山", "赭红山体  /  逆光剪影", (2300, 2170), 1300, 1),
        (["baisha", "osm-n12421270105"], "04–05", "白沙湖 · 二号观景台", "沙山映湖  /  黄昏候选", (400, 2690), 1460, 1),
        (["karakul"], "06", "喀拉库勒湖", "✦  雪峰星空首选取景", (350, 3520), 1460, 2),
        (["osm-n4808866521"], "11", "塔合曼湿地", "金色草甸  /  开放观景台", (340, 4260), 1360, 4),
        (["stone-city"], "07", "石头城遗址", "遗址日落  /  塔县落脚", (390, 4920), 1360, 2),
        (["osm-n13129567998", "osm-n13129567995"], "09–10", "班迪尔蓝湖 · 南北岸", "周边山区禁止露营", (2520, 4400), 1540, 3),
        (["panlong"], "08", "盘龙古道", "盘山曲线  /  俯拍机位", (2910, 5105), 1370, 3),
        (["shache", "osm-w958776273"], "12–13", "莎车老城 · 王陵", "叶尔羌土色  /  早晨扫街", (4780, 3250), 1450, 5),
    ]
    for ids, number, label, tag, (x, y), width, day_index in clusters:
        lon = sum(PLACES[item][1] for item in ids)/len(ids)
        lat = sum(PLACES[item][2] for item in ids)/len(ids)
        ax, ay = px(lon, lat)
        # Connect center of badge to its precise map coordinate.
        target_x = min(max(ax, x), x+width)
        target_y = min(max(ay, y), y+205)
        draw.line((ax, ay, target_x, target_y), fill="#668176", width=5)
        draw.ellipse((ax-25, ay-25, ax+25, ay+25), fill="#FFFDF8", outline=COLORS[day_index], width=9)
        round_rect(draw, (x, y, x+width, y+205), 40, "#FFFDF8", "#B9CABD", 3)
        round_rect(draw, (x+18, y+23, x+198, y+115), 28, COLORS[day_index])
        text(draw, (x+107, y+69), number, 38 if len(number)>2 else 52, "#FFFFFF", anchor="mm")
        text(draw, (x+218, y+38), label, 48, INK)
        round_rect(draw, (x+20, y+137, x+width-20, y+190), 20, "#EAF0E5")
        text(draw, (x+45, y+140), tag, 34, "#52756A")


def right_panel(draw, data):
    round_rect(draw, (6560, 760, 9740, 6140), 54, "#FFFDF8")
    round_rect(draw, (6750, 925, 9530, 2055), 42, "#EAF0E9")
    text(draw, (6830, 985), "NIGHT SKY / 星空与帐篷", 48, SEA)
    text(draw, (6830, 1080), "取景点和露营地要分开确认", 45, "#597369")
    draw.line((6830, 1190, 9465, 1190), fill="#CAD9CB", width=4)
    round_rect(draw, (6830, 1240, 7005, 1380), 35, COLORS[2])
    text(draw, (6917, 1310), "01", 54, "#FFFFFF", anchor="mm")
    text(draw, (7065, 1235), "喀拉库勒湖  ·  雪山与星空", 56, INK)
    text(draw, (7065, 1330), "最有画面；要拍到夜空，D3 住宿需改到获许可营地。", 39, MUTED)
    text(draw, (7065, 1405), "不周山营地在景区内；自带帐篷须先向经营方确认。", 37, MUTED)
    round_rect(draw, (6830, 1515, 7005, 1655), 35, COLORS[3])
    text(draw, (6917, 1585), "02", 54, "#FFFFFF", anchor="mm")
    text(draw, (7065, 1510), "塔县附近  ·  与原行程更合拍", 56, INK)
    text(draw, (7065, 1605), "D4 在有管理、允许夜拍的营地或住宿地看星。", 39, MUTED)
    text(draw, (7065, 1680), "班迪尔蓝湖周边山区禁止露营；别拍完再赶夜路。", 37, MUTED)
    draw.line((6830, 1815, 9465, 1815), fill="#CAD9CB", width=4)
    text(draw, (6830, 1860), "若 10/1 出发：10/3 下弦，后半程月光渐弱；还要看云量与风。", 37, SEA)

    text(draw, (6765, 2145), "DAILY ROADBOOK", 36, "#81958C")
    text(draw, (7160, 2120), "逐日顺序 · 7 DAYS", 65, INK)
    text(draw, (6765, 2230), "重复出现的地点代表折返；公里数是道路估算。", 35, MUTED)
    cy = 2360
    for number, day in enumerate(DAYS, 1):
        color = COLORS[number-1]
        y = cy+(number-1)*525
        round_rect(draw, (6750, y, 9540, y+500), 31, "#F4F4EC")
        round_rect(draw, (6800, y+40, 6945, y+169), 34, color)
        text(draw, (6872, y+103), f"D{number}", 49, "#FFFFFF", anchor="mm")
        text(draw, (7010, y+39), day["title"], 57, INK)
        road_km = round(data["days"][number-1]["distance_m"] / 1000)
        text(draw, (7010, y+130), f"夜宿 {day['stay']}  ·  自驾约 {road_km} km", 35, MUTED)
        draw.line((6800, y+220, 9480, y+220), fill="#DAE2D7", width=3)
        # Two rows and explicit arrows fit the densest day with five stops.
        names = day["line"]
        if len(names) == 5:
            rows = [names[:3], names[3:]]
        elif len(names) == 4:
            rows = [names[:2], names[2:]]
        else:
            rows = [names]
        for row_i, row in enumerate(rows):
            ry = y+258+row_i*90
            out = "  →  ".join(row)
            size = 45 if len(out) < 27 else 39
            text(draw, (6810, ry), out, size, INK)
        note = ["巷道 / 慢适应海拔", "红层 / 白沙湖岸", "高原湖 / 星空候选", "盘山路 / 蓝湖禁野营", "湿地 / 当天返城", "老城 / 王陵", "晨光 / 返程"][number-1]
        text(draw, (6810, y+430), f"◈  {note}", 35, "#7D9688")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch-routes", action="store_true", help="refresh publicly routed road geometry")
    args = parser.parse_args()
    data = fetch_routes() if args.fetch_routes else json.loads(ROUTE_DATA.read_text())
    assert [item["stops"] for item in data["days"]] == [day["stops"] for day in DAYS], "Route snapshot differs from selected stops"

    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    round_rect(draw, (0, 0, W, 650), 0, SEA)
    text(draw, (320, 68), "经纬  /  XINJIANG ATLAS", 46, "#C4DDD4")
    text(draw, (310, 164), "帕米尔与莎车 · 七日行进图", 125, "#FFFDF8")
    text(draw, (325, 412), "喀什 → 帕米尔 → 莎车 → 喀什    /    7 天的公路、停靠与星空取景", 56, "#D5E4D9")
    round_rect(draw, (7680, 119, 9680, 288), 80, "#D8E7D7")
    text(draw, (8680, 200), "7 天   /   莎车慢行   /   自驾   /   多点摄影", 48, SEA, anchor="mm")
    total_km = round(sum(day["distance_m"] for day in data["days"]) / 1000)
    text(draw, (7720, 393), f"13 个独立地图锚点  ·  道路估算约 {total_km:,} km", 45, "#D8E7D7")

    base_map(im, draw)
    draw_geometry(draw, data)
    point_labels(draw)
    legend(draw)
    right_panel(draw, data)

    text(draw, (315, 6250), "道路轨迹与里程据 OSRM / OpenStreetMap 估算；同路段颜色错位用于区分往返。取景点 ≠ 允许扎营地点；此图不能代替实时导航。", 35, MUTED)
    text(draw, (315, 6350), "政策与天象参考：阿克陶县文旅局、塔县文旅局、NASA SkyCal。边防证、景区开放、天气、营地可自搭及交通管制请临行确认。© OpenStreetMap contributors · ODbL", 32, MUTED)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUTPUT, optimize=True)
    print(f"Wrote {OUTPUT} ({W} × {H}; {OUTPUT.stat().st_size/1048576:.1f} MiB)")


if __name__ == "__main__":
    main()
