"""Render the public photo credits from the same catalog used by the UI."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = json.loads((ROOT / "src/photoCatalog.json").read_text())
NAMES = {"tomur": "温宿托木尔大峡谷", "kashgar": "喀什古城", "gaotai": "高台民居", "kizil": "克孜尔千佛洞"}


def e(value):
    return html.escape(str(value), quote=True)


rows = []
for place_id, photos in PHOTOS.items():
    for photo in photos:
        rows.append(
            f'<tr><td>{e(NAMES[place_id])}</td><td><a href="{e(photo["source"])}" target="_blank" rel="noopener noreferrer">{e(photo["title"])}</a></td>'
            f'<td>{e(photo["author"])}</td><td><a href="{e(photo["licenseUrl"])}" target="_blank" rel="noopener noreferrer">{e(photo["license"])}</a></td>'
            f'<td>网页展示使用缩放副本</td></tr>'
        )

page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>摄影来源与版权说明 · 新疆地点图鉴</title>
<style>body{{margin:0;background:#f6f5ee;color:#24453e;font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:900px;margin:40px auto;padding:32px;background:#fffefa;border:1px solid #e6e7dc;border-radius:10px}}h1{{font-size:28px;line-height:1.3}}h2{{font-size:18px;margin-top:34px}}p,li{{color:#586d64}}a{{color:#a36645;text-underline-offset:3px}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #e9ede6;vertical-align:top}}th{{background:#eef2eb}}.scroll{{overflow:auto}}.small{{font-size:12px}}@media(max-width:650px){{main{{margin:0;padding:22px;border:0}}table{{min-width:780px}}}}</style></head>
<body><main><a href="./">← 返回地图</a><h1>摄影来源与版权说明</h1>
<p>这是一个供朋友规划旅行的非商业开源地图。每幅公开展示的摄影作品都在下表和地点卡片中标注作者、原始页面、独立许可证。<strong>开源代码的 MIT 许可不适用于摄影图片；“非商业”“注明来源”或“侵权告知删除”也不构成图片使用授权。</strong>使用图片前，请阅读对应许可和原始页面的限制；本站不对图片附加与其许可冲突的限制。</p>
<p>下列作品使用了适于网页展示的缩放副本，画面内容未作改绘；原图、作者说明和完整许可请以链接页面为准。开放许可并不代表摄影作品属于本站或完全没有其他权利限制。</p>
<h2>图片逐张来源（{len(rows)} 幅）</h2><div class="scroll"><table><thead><tr><th>地点</th><th>原始作品 / 来源</th><th>署名</th><th>图片许可</th><th>展示变化</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>版权联系与撤图</h2><p>如果您是权利人并认为某张图片的来源、署名、许可或使用方式有误，请在 <a href="https://github.com/myki-jim/xinjiang-atlas/issues/new?title=%E5%9B%BE%E7%89%87%E7%89%88%E6%9D%83%E4%B8%8E%E6%92%A4%E5%9B%BE" target="_blank" rel="noopener noreferrer">GitHub 提交版权与撤图请求</a>，注明地点名称、图片或原始页面链接以及希望更正或撤除的内容。我们会核查并及时更正或移除有问题的图片。Issue 是公开的，请勿在其中发布身份证件或其他私人材料。</p>
<h2>地点与底图</h2><p>底图和补充地点源自 <a href="https://www.openstreetmap.org/copyright">OpenStreetMap 贡献者</a>；地点数据遵守 <a href="https://opendatacommons.org/licenses/odbl/1-0/">ODbL 1.0</a>，代码许可证和数据说明请看 <a href="https://github.com/myki-jim/xinjiang-atlas">项目仓库</a>。地图位置仅作总览，不能替代导航或当地开放信息。</p>
<p class="small">更新日期：2026-09-17 · <a href="./">返回地图</a></p></main></body></html>'''
(ROOT / "public/COPYRIGHT.html").write_text(page)
print(f"Wrote {len(rows)} photo credits")
