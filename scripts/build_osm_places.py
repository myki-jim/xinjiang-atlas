"""Build a small, attributed POI index from a Geofabrik Xinjiang OSM export.

Usage: python3 scripts/build_osm_places.py /tmp/xj-tourism.geojson
The input is produced with osmium tags-filter and osmium export; see README.
The generated data remains under the OpenStreetMap ODbL, separate from code.
"""

import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src" / "osmPlaces.json"
CURATED = ROOT / "src" / "atlasData.js"
LANDMARKS = ROOT / "src" / "landmarkPlaces.json"
TOURISM = {"attraction", "museum", "viewpoint", "zoo", "theme_park", "gallery", "aquarium"}
HISTORIC = {"archaeological_site", "castle", "monument", "memorial", "ruins"}
FACILITIES = ("游客中心", "游客服务中心", "服务中心", "服务大厅", "售票处", "停车场", "卫生间", "厕所", "检票口", "观光车站", "景区入口", "景区出口", "景区大门", "导览图", "指示牌", "打卡点", "栈道入口", "索道观光车", "出发站", "农家", "農家", "驿站")
HUMAN_WORDS = ("古城", "故城", "遗址", "博物馆", "纪念", "石窟", "佛寺", "寺院", "麻扎", "巴扎", "墓", "烽火台", "石碑", "岩画", "王府", "宫殿", "清真寺")


def name_for(tags):
    name = unicodedata.normalize("NFKC", tags.get("name:zh") or tags.get("name") or "").strip()
    if not re.search(r"[\u4e00-\u9fff]", name):
        return ""
    # Prefer the Chinese name when an English main name supplies it in brackets.
    match = re.search(r"[（(]([^()]*[\u4e00-\u9fff][^()]*)[）)]", name)
    if match and not re.search(r"[\u4e00-\u9fff]", name[:match.start()]):
        name = match.group(1)
    name = re.split(r"\s[-—–]\s", name, maxsplit=1)[0].strip()
    name = re.sub(r"\s{2,}", " ", name)
    if len(name) < 2 or len(name) > 36 or any(part in name for part in FACILITIES):
        return ""
    if name in {"观景点", "观景台", "观景亭", "旅游景区", "旅游区", "景区", "纪念碑", "古城遗址", "无名遗址", "人民广场", "音乐广场", "游憩广场", "禾木入口"}:
        return ""
    if re.match(r"^[0-9一二三四五六七八九十]+号.*(建筑|房址|窑址)", name):
        return ""
    return name


def ring_center(ring):
    # The largest polygon's centroid is only a map overview anchor.
    signed = 0.0
    cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        cross = x1 * y2 - x2 * y1
        signed += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(signed) > 1e-10:
        return [cx / (3 * signed), cy / (3 * signed)]
    return [sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)]


def center_of(geometry):
    typ, coords = geometry["type"], geometry["coordinates"]
    if typ == "Point":
        return coords
    if typ == "MultiPolygon":
        rings = [polygon[0] for polygon in coords if polygon and polygon[0]]
        if not rings:
            return None
        ring = max(rings, key=lambda r: abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(r, r[1:]))))
        return ring_center(ring)
    if typ == "Polygon":
        return ring_center(coords[0])
    if typ == "LineString":
        return coords[len(coords) // 2] if coords else None
    return None


def category(tags, name):
    tourism = tags.get("tourism")
    historic = tags.get("historic")
    if tourism in {"museum", "gallery"}:
        return "人文", "博物馆" if tourism == "museum" else "展馆"
    if historic in HISTORIC:
        kind = {"archaeological_site": "考古遗址", "castle": "古城与城堡", "monument": "历史地标", "memorial": "纪念地", "ruins": "历史遗迹"}[historic]
        return "人文", kind
    if any(word in name for word in HUMAN_WORDS):
        return "人文", "人文景点"
    if any(word in name for word in ("湖", "湿地", "泉", "水库")):
        return "湖泊", "湖泊与湿地"
    if tourism == "viewpoint":
        return "自然", "观景点"
    if tourism == "theme_park":
        return "人文", "主题景区"
    if tourism == "zoo":
        return "自然", "动物园"
    if tags.get("leisure") == "nature_reserve":
        return "自然", "自然保护区"
    if tags.get("natural") == "waterfall":
        return "自然", "瀑布"
    return "自然", "风景地点"


def normal(name):
    return re.sub(r"[·\s\W]|风景名胜区|旅游风景区|旅游区|风景区|景区", "", name)


def kilometres(a, b):
    x = (a[0] - b[0]) * math.cos(math.radians((a[1] + b[1]) / 2)) * 111
    y = (a[1] - b[1]) * 111
    return math.hypot(x, y)


def main(path):
    features = json.loads(Path(path).read_text())["features"]
    curated_text = CURATED.read_text()
    curated = []
    for name, lon, lat in re.findall(r"name: '([^']+)'.*?coord: \[([\d.]+), ([\d.]+)\]", curated_text):
        curated.append((normal(name), [float(lon), float(lat)]))
    for place in json.loads(LANDMARKS.read_text()):
        curated.append((normal(place["name"]), place["coord"]))
    records = []
    chosen = {}
    for feature in features:
        tags = feature["properties"]
        if not (tags.get("tourism") in TOURISM or tags.get("historic") in HISTORIC or tags.get("natural") == "waterfall" or tags.get("leisure") == "nature_reserve"):
            continue
        name = name_for(tags)
        coord = center_of(feature["geometry"])
        if not name or not coord or not (73 <= coord[0] <= 97 and 34 <= coord[1] <= 50):
            continue
        key = normal(name)
        if any((key == other or (len(key) >= 4 and len(other) >= 4 and (key in other or other in key))) and kilometres(coord, c) < 2 for other, c in curated):
            continue
        if any(kilometres(coord, old) < 2 for old in chosen.get(key, [])):
            continue
        chosen.setdefault(key, []).append(coord)
        group, kind = category(tags, name)
        osm_id = feature["id"]
        osm_type = {"n": "node", "w": "way", "r": "relation"}.get(osm_id[0])
        if not osm_type:
            continue
        records.append({
            "id": "osm-" + osm_id,
            "name": name,
            "coord": [round(coord[0], 6), round(coord[1], 6)],
            "group": group,
            "type": kind,
            "precision": "OSM 地图点" if feature["geometry"]["type"] == "Point" else "OSM 区域锚点",
            "source": f"https://www.openstreetmap.org/{osm_type}/{osm_id[1:]}",
        })
    records.sort(key=lambda record: (record["group"], record["name"], record["id"]))
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Wrote {len(records)} named OSM places to {OUTPUT}")


if __name__ == "__main__":
    main(sys.argv[1])
