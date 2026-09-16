# 地点数据来源与授权

`src/osmPlaces.json` 和 `src/landmarkPlaces.json` 是由 OpenStreetMap 贡献者的数据整理而成的地点索引，遵守 [Open Database License 1.0（ODbL）](https://opendatacommons.org/licenses/odbl/1-0/)。原始数据：[Geofabrik 新疆提取文件](https://download.geofabrik.de/asia/china/xinjiang.html)，使用 2026-09-14 版本。

我们筛选了旅游、历史和自然标签，保留有中文名称的对象；剔除了部分设施、泛称与重复标注；对区域对象计算了总览用锚点，并为每条记录保留 OpenStreetMap 原始对象链接。`src/landmarkPlaces.json` 是从同一提取文件中选出的知名地点，部分来源于自然水体或历史建筑等不同标签。完整整理结果以仓库中的 JSON 为准，可按 ODbL 条款继续使用和修改。

`src/atlasData.js` 的 22 个精选地点分别附有来源链接，部分位置是景区、村落或主题的范围锚点。这些数据和开放地图补充点都不能代替交通导航、景区入口或最新开放状态。代码采用 MIT 许可；摄影作品采用逐张标注的独立许可，详见 [`src/photoCatalog.json`](src/photoCatalog.json)。

`public/data/routes/pamir-7-slow-full-osrm.json` 是使用 OSRM 公共路由服务查询上述行程锚点而得到的 OpenStreetMap 道路轨迹缓存；与地点数据一样，底层地图数据库遵守 ODbL。`public/exports/pamir-shache-7-day-road-trip.png` 是据此生成的行程图，图内已署名 OpenStreetMap 贡献者。缓存中的道路形状和里程仅供行程总览，不保证导航时仍可通行。
