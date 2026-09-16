# 经纬 · 新疆地点图鉴

一个开源的新疆 2D 景点地图。可缩放到街道，搜索、筛选并点击标点查看位置依据。当前收录 536 个地点：22 个精选、20 个著名地标，以及 494 个开放地图补充点。全疆视图会聚合密集标点，放大后逐步展开。开放地图索引覆盖不均，不能视为全部景区的官方名录。

## 本地运行

```bash
npm install
npm run dev
```

生产构建：`npm run build`。部署由 `.github/workflows/pages.yml` 在推送至 `main` 后自动完成。

## 操作

- 拖动地图，使用滚轮或右下角按钮放大、缩小；放大后可看街道。
- 点击地图标点或地点列表查看说明、经纬度和位置来源。
- 按精选、自然、湖泊、人文筛选；`⌘/Ctrl + K` 聚焦搜索，`Esc` 关闭卡片。
- 点击顶部“推荐路线”，切换 3、5、7 天南疆行程；7 天可选西极荒原或莎车慢行。选择出发日期、自驾／火车加包车／飞机加包车、游玩地点数量，地图会重排停靠顺序并按天定位。
- 选择“7 天 / 莎车慢行 / 自驾 / 多点摄影”后，可下载 [10000 × 6600 的完整行进图](public/exports/pamir-shache-7-day-road-trip.png)，含每天的道路轨迹、方向、停靠顺序、比例尺、区域定位、摄影标签和星空取景建议。生成脚本为 `scripts/export_pamir_route.py`，需要 Python Pillow 和中文字体；离线执行 `python3 scripts/export_pamir_route.py` 可重绘，需要重新获取路由数据时才运行 `python3 scripts/export_pamir_route.py --fetch-routes`。
- 已获开放许可的摄影作品会在地点卡片中展示，并逐张列出作者、原图来源和许可证。没有合适授权的地点暂时只显示位置。
- 窄屏用左上角菜单查看地点列表；可分享带 `?place=地点ID` 的网址。

## 数据与授权

- 地图由 [Leaflet](https://leafletjs.com/) 渲染，底图来自 [OpenStreetMap](https://www.openstreetmap.org/copyright)。请遵守 [OSM 瓦片使用政策](https://operations.osmfoundation.org/policies/tiles/)。
- 新疆省界来自 [geoBoundaries](https://www.geoboundaries.org/) 公共领域数据，经简化用于视觉高亮。
- 精选地点位置与来源记录在 `src/atlasData.js`，地标位置记录在 `src/landmarkPlaces.json`，补充地点记录在 `src/osmPlaces.json`。后两者提取自 [Geofabrik 新疆 OSM 数据](https://download.geofabrik.de/asia/china/xinjiang.html)，按地点名称与旅游标签筛选、去重并计算区域锚点。处理过程见 `scripts/build_osm_places.py`；使用的是 2026-09-14 的提取版本。
- 衍生地点数据库遵守 [OpenStreetMap ODbL 1.0](https://www.openstreetmap.org/copyright)，与代码的 [MIT 许可证](LICENSE) 分开。详见 [DATA_LICENSE.md](DATA_LICENSE.md)。大型景区、湖泊和老城片区的标点仅供总览，**不能用于导航**。
- 14 幅摄影作品来自 Wikimedia Commons 和 Flickr 的开放许可作品，分布在 4 个地点。每幅图片独立遵守其标注的 CC BY 或 CC BY-SA 许可，详情见 [图片目录](src/photoCatalog.json)及网站的[摄影来源与版权说明](public/COPYRIGHT.html)。代码的 MIT 许可不覆盖摄影作品。
- 路线编辑数据在 `src/routes.js`，默认出发日期 2026-10-01。参考 [自治区文旅厅帕米尔线路](https://wlt.xinjiang.gov.cn/wlt/c112786/202402/04ec109e9ce24ac5aa955ca8eb8c6c7a.shtml) 和 [2026 年新疆国庆放假安排](https://www.xinjiang.gov.cn/xinjiang/tzgg/202512/aaece21b6906443e8d50b981070764a8.shtml)。地图线路是按停靠点连接的**行程示意**，不是实际道路导航；不包含实时路况、交通时刻或车程估算。西极所在的吉根乡等边境区域应参照[克州边境通行证说明](https://www.xjkz.gov.cn/xjkz/c102165/202307/e661dc3ce5534e55bca0bb30c8735474.shtml)事先办理。火车车次、余票以[铁路 12306](https://www.12306.cn/)为准。
- 单张导出图额外使用 [OSRM 公共路由服务](https://project-osrm.org/) 计算路段，缓存轨迹位于 `public/data/routes/pamir-7-slow-full-osrm.json`。图上里程为路由估算，景点可能离道路有距离；道路开放、景区入口与行车方案均需临行再核实。路线及底层道路数据来自 OpenStreetMap 贡献者，按 ODbL 署名。

## 星空取景与帐篷

这条线的星空画面以**喀拉库勒湖—雪峰**为首选取景构想；若要在 D3 拍到夜空并过夜，需要把原本的塔县住宿改为景区内经确认可接待的营地。阿克陶县[官方公告曾提及通往不周山营地公园的景区道路](https://www.xjakt.gov.cn/xjakt/c103519/202511/a12a2a3b973f4a689556373313bdefb6.shtml)，但不代表游客可自行在湖边搭帐篷，应事先询问营地经营方关于自带帐篷、夜间拍摄、停车及当季营业的规定。若保留原行程，D4 在塔县附近有管理且允许夜拍的住宿地更从容。

不要在班迪尔蓝湖周边山区或未开放区域搭帐篷：[塔县文旅局 2026 年公告](https://www.btzx.com.cn/web/2026/5/3/ARTI1777778943656676.html)明确将班迪尔蓝湖周边山区列入禁止户外露营范围；[阿克陶县文旅局公告](https://www.xjakt.gov.cn/xjakt/c104939/202508/aad4037e56714e7ea7f33c12d1388df0.shtml)也禁止擅自在未开放区域、山林河谷、危险路段及牧道露营。阿克陶县[2026 年出游提示](https://www.xjakt.gov.cn/xjakt/c103525/202604/857cc4a4dd904b3fa70d53c05313a27e.shtml)要求相关边境景区提前办理边境通行证，注意高原身体反应、保暖、离线地图和野外禁火。

若按默认 2026-10-01 出发，[NASA 2026 天象表](https://eclipse.gsfc.nasa.gov/SKYCAL/SKYCAL.html?cal=2026)显示 10 月 3 日下弦、10 月 10 日新月；由此推断后半程的月光干扰通常比前几天小。实际拍摄还要看云量、风、月出时刻和合法可进入的拍摄范围。

本项目供朋友做非商业旅行规划。**“非商业”“注明来源”“侵权告知删除”不能替代图片授权**；许可不明的照片仅保存在未公开的本地目录。若发现图片归属、署名或使用问题，请通过 [GitHub Issue 提交版权与撤图请求](https://github.com/myki-jim/xinjiang-atlas/issues/new?title=%E5%9B%BE%E7%89%87%E7%89%88%E6%9D%83%E4%B8%8E%E6%92%A4%E5%9B%BE)，提供地点和图片链接，我们会核查、更正或撤除。公开 Issue 中请勿发布私密证件。

如需重新生成地点索引，从 Geofabrik 下载新疆 `.osm.pbf`，使用 `osmium tags-filter` 提取 `tourism=attraction,museum,viewpoint,zoo,theme_park,gallery,aquarium`、`historic=archaeological_site,castle,monument,memorial,ruins`、`natural=waterfall`、`leisure=nature_reserve`，再用 `osmium export -f geojson -u type_id` 转为 GeoJSON，执行 `python3 scripts/build_osm_places.py <文件>`。更新图片目录后运行 `python3 scripts/build_rights_page.py` 同步版权清单。

## 参考

[World Monitor 的开发文档](https://github.com/koala73/worldmonitor/blob/main/docs/getting-started.mdx)说明其桌面地图使用 MapLibre GL + deck.gl、移动地图使用 D3.js + TopoJSON。本项目只需展示景点标点，因此使用轻量的 Leaflet。
