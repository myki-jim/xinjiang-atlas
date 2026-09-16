# 经纬 · 新疆地点图鉴

一个开源的新疆 2D 景点地图。可缩放到街道，搜索、筛选并点击标点查看位置依据。地图先显示标点，再异步加载街道瓦片。当前首批标记 20 个地点；全疆景点索引正在扩充。

## 本地运行

```bash
npm install
npm run dev
```

生产构建：`npm run build`。部署由 `.github/workflows/pages.yml` 在推送至 `main` 后自动完成。

## 操作

- 拖动地图，使用滚轮或右下角按钮放大、缩小；放大后可看街道。
- 点击地图标点或地点列表查看说明、经纬度和位置来源。
- 按自然、湖泊、人文筛选；`⌘/Ctrl + K` 聚焦搜索，`Esc` 关闭卡片。
- 窄屏用左上角菜单查看地点列表；可分享带 `?place=地点ID` 的网址。

## 数据与授权

- 地图由 [Leaflet](https://leafletjs.com/) 渲染，底图来自 [OpenStreetMap](https://www.openstreetmap.org/copyright)。请遵守 [OSM 瓦片使用政策](https://operations.osmfoundation.org/policies/tiles/)。
- 新疆省界来自 [geoBoundaries](https://www.geoboundaries.org/) 公共领域数据，经简化用于视觉高亮。
- 首批地点位置与来源记录在 `src/atlasData.js`。大型景区、湖泊和老城片区的标点仅供总览，**不能用于导航**。
- 代码采用 [MIT 许可证](LICENSE)。OpenStreetMap 地图数据遵守其自身的授权和署名要求。

摄影图片仍在筛选转载授权，**不包含在开源仓库或公开网页中**。接下来先扩充全疆地点；图片和攻略后续再做。

## 参考

[World Monitor 的开发文档](https://github.com/koala73/worldmonitor/blob/main/docs/getting-started.mdx)说明其桌面地图使用 MapLibre GL + deck.gl、移动地图使用 D3.js + TopoJSON。本项目只需展示景点标点，因此使用轻量的 Leaflet。
