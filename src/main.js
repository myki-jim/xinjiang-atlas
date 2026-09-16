import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './style.css';
import { places, groups } from './atlasData.js';
import photos from './photoCatalog.json';
import { routePlans, planId, routeSources } from './routes.js';

const $ = (selector) => document.querySelector(selector);
const esc = (value = '') => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const urlParams = new URLSearchParams(location.search);
const state = { group: '全部', query: '', selected: null, sidebarOpen: false };
const routeFromUrl = urlParams.get('route');
const routeState = {
  days: routeFromUrl?.includes('-3') ? 3 : routeFromUrl?.includes('-5') ? 5 : 7,
  style: routeFromUrl?.endsWith('-slow') ? 'slow' : 'remote',
  mode: ['drive', 'rail', 'air'].includes(urlParams.get('mode')) ? urlParams.get('mode') : 'drive',
  pace: ['relaxed', 'balanced', 'full'].includes(urlParams.get('pace')) ? urlParams.get('pace') : 'balanced',
  start: /^\d{4}-\d{2}-\d{2}$/.test(urlParams.get('start') || '') ? urlParams.get('start') : '2026-10-01',
  day: null,
  open: !urlParams.get('place'),
};
const filtered = () => places.filter((place) => (state.group === '全部' || (state.group === '精选' ? !place.sourceKind : state.group === place.group)) &&
  `${place.name} ${place.region} ${place.type} ${place.subtitle} ${place.note}`.toLowerCase().includes(state.query.toLowerCase()));

$('#app').innerHTML = `<div class="atlas">
  <div id="map" class="map-canvas" aria-label="可缩放的新疆街道地图"></div>
  <div id="map-loading" class="map-loading"><span class="loading-dot"></span>正在载入街道地图</div>
  <header class="topbar"><button id="menu-button" class="mobile-menu" aria-label="打开地点列表">☰</button><div class="brand"><span class="brand-mark">经纬</span><span class="brand-divider"></span><span>新疆地点图鉴</span></div><span class="topbar-note">先看地点，再决定路线</span><button id="route-toggle" class="route-toggle">◈ &nbsp;推荐路线 · 7 天</button><button id="fit-top" class="topbar-fit">⌖ &nbsp;新疆全图</button></header>
  <aside id="sidebar" class="sidebar"><div class="sidebar-head"><span class="eyebrow"><span class="eyebrow-line"></span> THE XINJIANG ATLAS / 01</span><h1>把想去的地方<br><em>放在同一张地图上。</em></h1><p>先标出新疆的地点与街巷，再慢慢挑选值得深入了解的地方。</p></div>
    <label class="search-box"><span class="search-icon">⌕</span><input id="search" type="search" autocomplete="off" placeholder="搜索地点、城市或地貌" aria-label="搜索地点" /><kbd>⌘ K</kbd></label>
    <div id="filters" class="filters" role="group" aria-label="地点类别"></div><div class="list-header"><span id="list-count">全部地点</span><span>点击查看位置 ↗</span></div><div id="place-list" class="place-list"></div>
    <div class="sidebar-foot"><span class="foot-symbol">✳</span><span>地点来自精选清单与开放地图，锚点仅供总览。<a href="${import.meta.env.BASE_URL}COPYRIGHT.html" target="_blank" rel="noopener">图片来源与版权说明 ↗</a></span></div></aside>
  <div class="map-controls"><button id="zoom-in" aria-label="放大地图">＋</button><button id="zoom-out" aria-label="缩小地图">−</button><span class="control-rule"></span><button id="fit-map" aria-label="新疆全图">⌖</button></div>
  <div class="map-hint"><span class="hint-dot"></span><span id="map-status">新疆全景</span><span class="hint-divider">/</span><span id="zoom-status">缩放 --</span></div>
  <section id="detail-panel" class="detail-panel" aria-live="polite"></section><section id="route-panel" class="route-panel" aria-label="行程路线规划"></section><div id="mobile-shade" class="mobile-shade" hidden></div>
</div>`;

function renderFilters() {
  $('#filters').innerHTML = groups.map((group) => `<button class="filter ${state.group === group ? 'active' : ''}" data-group="${group}">${group}</button>`).join('');
}

function renderList() {
  const items = filtered();
  $('#list-count').textContent = `${state.group === '全部' ? '全部地点' : state.group} / ${items.length}`;
  $('#place-list').innerHTML = items.length ? items.map((place) => {
    return `<button class="place-row ${state.selected?.id === place.id ? 'selected' : ''}" data-place="${place.id}" aria-label="查看${esc(place.name)}">
      <div class="row-image ${place.group === '湖泊' ? 'water' : place.group === '人文' ? 'culture' : 'nature'}"><span class="row-symbol">${place.group === '湖泊' ? '≈' : place.group === '人文' ? '⌂' : '△'}</span><span class="row-index">${String(places.indexOf(place) + 1).padStart(2, '0')}</span></div>
      <div class="row-copy"><span class="row-region">${esc(place.region)}</span><strong>${esc(place.name)}</strong><span class="row-meta">${esc(place.type)} <i>·</i> ${esc(place.precision)}</span></div><span class="row-arrow">↗</span></button>`;
  }).join('') : '<div class="empty-results"><strong>没有找到匹配的地点</strong><span>试试“喀什”“湖泊”或清空搜索。</span></div>';
}

function renderDetail() {
  const panel = $('#detail-panel');
  if (!state.selected) { panel.classList.remove('open'); panel.innerHTML = ''; return; }
  const place = state.selected;
  const gallery = photos[place.id] || [];
  panel.innerHTML = `<div class="detail-scroll"><div class="detail-top"><span class="detail-index">${place.sourceKind ? 'OPEN MAP' : 'FIELD NOTE'} / ${String(places.indexOf(place) + 1).padStart(2, '0')}</span><button id="close-detail" class="close-detail" aria-label="关闭地点卡片">×</button></div>
    <div class="detail-intro"><span class="detail-region">${esc(place.region)} <span>·</span> ${esc(place.type)}</span><h2>${esc(place.name)}</h2><p>${esc(place.subtitle)}</p></div>
    ${gallery.length ? `<div class="photo-gallery">${gallery.map((photo, index) => `<figure class="photo-card"><a href="${esc(photo.source)}" target="_blank" rel="noopener noreferrer" aria-label="查看${esc(photo.title)}的原始页面"><img src="${import.meta.env.BASE_URL}${esc(photo.file)}" loading="${index ? 'lazy' : 'eager'}" alt="${esc(photo.alt)}" /></a><figcaption><span>${esc(photo.title)} · 摄影 ${esc(photo.author)}</span><span><a href="${esc(photo.source)}" target="_blank" rel="noopener noreferrer">原图来源</a> · <a href="${esc(photo.licenseUrl)}" target="_blank" rel="noopener noreferrer">${esc(photo.license)}</a></span></figcaption></figure>`).join('')}</div>` : `<div class="location-hero"><span>MAP / XINJIANG</span><strong>${esc(place.name)}</strong><small>${place.coord[1].toFixed(4)}° N &nbsp; ${place.coord[0].toFixed(4)}° E</small></div><p class="photo-pending">摄影作品尚在筛选授权，欢迎推荐可公开使用的原图。</p>`}
    <p class="photo-terms">本站为非商业旅行整理。每张图片保留作者、来源和独立许可；开源代码许可不涵盖摄影作品。<a href="${import.meta.env.BASE_URL}COPYRIGHT.html" target="_blank" rel="noopener">版权与撤图说明 ↗</a></p>
    <div class="location-card"><span class="eyebrow">ON THE MAP</span><h3>位置说明</h3><p>${esc(place.note)}</p><div class="location-bottom"><span class="precision">⌖ ${esc(place.precision)}</span><a href="${esc(place.locationSource)}" target="_blank" rel="noopener noreferrer">位置依据 ↗</a></div></div>
    <button id="focus-place" class="focus-button">在地图中定位 <span>↗</span></button></div>`;
  panel.classList.add('open');
  requestAnimationFrame(() => { const gallery = panel.querySelector('.photo-gallery'); if (gallery) gallery.scrollLeft = 0; });
}

const currentPlan = () => routePlans[planId(routeState.days, routeState.style)];
const routePlace = (id) => places.find((place) => place.id === id);
function activeDays() {
  return currentPlan().daysList.map((day, index) => {
    let stops = [...day.stops];
    let title = day.title;
    let note = day.note;
    if (routeState.pace === 'relaxed') {
      stops = stops.filter((id) => !['gaotai', 'osm-n13129567998', 'osm-n4808866521', 'osm-w1428173533', 'osm-w958776273'].includes(id));
      if (day.stops.includes('panlong')) { title = '盘龙古道慢行'; note = '只留盘龙古道作为这天的主要风景；道路不开放时在塔县休息。'; }
      if (day.stops.includes('osm-w1428173533')) title = '奥依塔克红山';
    } else if (routeState.pace === 'full') {
      const insertAfter = (anchor, extra) => { const i = stops.indexOf(anchor); if (i >= 0) stops.splice(i + 1, 0, extra); };
      if (stops.includes('baisha') && !stops.includes('karakul')) insertAfter('baisha', 'osm-n12421270105');
      if (stops.includes('osm-n13129567998')) insertAfter('osm-n13129567998', 'osm-n13129567995');
      if (stops.includes('osm-w1428173533')) insertAfter('osm-w1428173533', 'osm-w1428173531');
    }
    return { ...day, title, note, stops };
  });
}
function dateForDay(index) {
  const date = new Date(`${routeState.start}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + index);
  return `${date.getUTCMonth() + 1}月${date.getUTCDate()}日`;
}
function routeModeLabel(day, index) {
  if (routeState.mode === 'rail') return day.rail ? '火车 · 市内接驳' : index === 0 ? '火车抵达 · 当地包车' : '当地包车';
  if (routeState.mode === 'air') return index === 0 ? '飞机抵达 · 当地包车' : '当地包车';
  return '自驾';
}
function renderRoutePanel() {
  const panel = $('#route-panel');
  const plan = currentPlan();
  const days = activeDays();
  const scenicCount = new Set(days.flatMap((day) => day.stops)).size;
  $('#route-toggle').textContent = `◈  推荐路线 · ${plan.days} 天`;
  panel.classList.toggle('open', routeState.open);
  panel.innerHTML = `<div class="route-scroll"><div class="route-head"><div><span class="eyebrow">THE FIELD ROUTE / SOUTH XINJIANG</span><h2>选一条路，<br><em>去看更大的风景。</em></h2></div><button id="close-route" class="close-detail" aria-label="关闭路线规划">×</button></div>
    <div class="route-controls"><span class="route-control-label">行程天数</span><div class="route-options">${[3, 5, 7].map((days) => `<button data-days="${days}" class="${routeState.days === days ? 'active' : ''}">${days} 天</button>`).join('')}</div>
      ${routeState.days === 7 ? `<span class="route-control-label">路线偏好</span><div class="route-options">${[['remote', '西极荒原'], ['slow', '莎车慢行']].map(([value, name]) => `<button data-style="${value}" class="${routeState.style === value ? 'active' : ''}">${name}</button>`).join('')}</div>` : ''}
      <span class="route-control-label">交通方式</span><div class="route-options">${[['drive', '自驾'], ['rail', '火车 + 包车'], ['air', '飞机 + 包车']].map(([value, name]) => `<button data-mode="${value}" class="${routeState.mode === value ? 'active' : ''}">${name}</button>`).join('')}</div>
      <span class="route-control-label">游玩地点数量</span><div class="route-options">${[['relaxed', '少量停靠'], ['balanced', '标准'], ['full', '多点摄影']].map(([value, name]) => `<button data-pace="${value}" class="${routeState.pace === value ? 'active' : ''}">${name}</button>`).join('')}</div>
      <label class="route-date">出发日期 <input id="route-start" type="date" value="${esc(routeState.start)}" aria-label="路线出发日期" /></label></div>
    <div class="route-summary"><span class="eyebrow">RECOMMENDED JOURNEY</span><h3>${esc(plan.name)}</h3><p>${esc(plan.tone)}</p><div class="route-metrics"><span><strong>${plan.days}</strong> 天</span><span><strong>${scenicCount}</strong> 个地图停靠点</span><span>喀什出发 · 返回喀什</span></div><p class="route-intro">${esc(plan.intro)}</p><button id="fit-route" class="fit-route">⌖ 在地图上看完整顺序</button></div>
    <p class="route-mode-note">${routeState.mode === 'drive' ? '喀什取还车；高原、盘龙和西极段都需要实地核查天气与道路。' : routeState.mode === 'rail' ? '铁路用于抵达喀什；莎车方案的喀什—莎车城际段也可乘火车。帕米尔和西极没有可替代的景点间铁路，需当地车辆。' : '飞机用于往返喀什；景点之间仍需租车或包车，没有把短途航班虚构为景区接驳。'}${routeState.pace === 'full' ? ' 多点摄影增加顺路观景点，依现场开放与停车条件取舍。' : ''}</p>
    <div class="route-days">${days.map((day, index) => `<article class="route-day ${routeState.day === index ? 'active' : ''}"><button class="route-day-select" data-day="${index}" aria-label="在地图上查看第${index + 1}天"><span class="route-day-index">D${index + 1}</span><span class="route-day-main"><small>${dateForDay(index)} · ${routeModeLabel(day, index)}</small><strong>${esc(day.title)}</strong><em>夜宿 ${esc(day.stay)}</em></span><span>↗</span></button><p>${esc(day.note)}</p><div class="route-stop-links">${day.stops.map((id, i) => { const place = routePlace(id); return place ? `<button data-stop="${esc(id)}">${i + 1}. ${esc(place.name)}</button>` : ''; }).join('')}</div>${day.permit ? `<a class="permit-link" href="https://www.xjkz.gov.cn/xjkz/c102165/202307/e661dc3ce5534e55bca0bb30c8735474.shtml" target="_blank" rel="noopener noreferrer">边境通行证办理说明 ↗</a>` : ''}</article>`).join('')}</div>
    <div class="route-sources"><h3>出行前再确认</h3><p>地图中的线只连接地点锚点，<strong>不是实际道路或实时导航</strong>。不估算车程、不显示未核实的航班车次；国庆道路、票务、海拔适应和边境证件请临行确认。</p>${routeSources.map((source) => `<a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗</a>`).join('')}</div></div>`;
}

const map = L.map('map', { zoomControl: false, attributionControl: false, preferCanvas: true, zoomSnap: 0.25, minZoom: 3.5, maxZoom: 19, zoomAnimation: true }).setView([42.2, 84.5], 4.35);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  crossOrigin: true,
}).addTo(map);
L.control.attribution({ prefix: false, position: 'bottomright' }).addTo(map);
const markerLayer = L.layerGroup().addTo(map);
const clusterLayer = L.layerGroup().addTo(map);
map.createPane('routePane').style.zIndex = '650';
const routeLayer = L.layerGroup().addTo(map);
const markers = new Map();
let outerShade;

function markerIcon(place, selected = false) {
  const tone = place.group === '湖泊' ? 'water' : place.group === '人文' ? 'culture' : 'nature';
  return L.divIcon({ className: 'destination-icon', iconSize: [1, 1], iconAnchor: [0, 0], html: `<span class="destination-pin ${tone} ${selected ? 'active' : ''}"><span class="destination-dot"></span><span class="destination-name">${esc(place.name)}</span></span>` });
}

for (const place of places) {
  const marker = L.marker([place.coord[1], place.coord[0]], { icon: markerIcon(place), title: place.name, keyboard: true, riseOnHover: true }).on('click', () => selectPlace(place.id));
  markers.set(place.id, marker);
}

function refreshMarkers() {
  markerLayer.clearLayers();
  clusterLayer.clearLayers();
  const size = map.getZoom() < 8 ? 65 : map.getZoom() < 12 ? 46 : 30;
  const buckets = new Map();
  for (const place of filtered()) {
    if (place.id === state.selected?.id) {
      const marker = markers.get(place.id);
      marker.setIcon(markerIcon(place, true));
      markerLayer.addLayer(marker);
      continue;
    }
    const pixel = map.latLngToLayerPoint([place.coord[1], place.coord[0]]);
    const key = `${Math.floor(pixel.x / size)}:${Math.floor(pixel.y / size)}`;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(place);
  }
  for (const bucket of buckets.values()) {
    if (bucket.length === 1) {
      const place = bucket[0];
      const marker = markers.get(place.id);
      marker.setIcon(markerIcon(place));
      markerLayer.addLayer(marker);
      continue;
    }
    const lat = bucket.reduce((sum, place) => sum + place.coord[1], 0) / bucket.length;
    const lng = bucket.reduce((sum, place) => sum + place.coord[0], 0) / bucket.length;
    const icon = L.divIcon({ className: 'cluster-icon', iconSize: [36, 36], iconAnchor: [18, 18], html: `<span class="cluster-pin">${bucket.length}</span>` });
    L.marker([lat, lng], { icon, title: `附近 ${bucket.length} 个地点` }).on('click', () => map.flyTo([lat, lng], Math.min(19, map.getZoom() + 2.5), { duration: .6 })).addTo(clusterLayer);
  }
}

function drawRoute() {
  routeLayer.clearLayers();
  $('#map').classList.toggle('route-active', routeState.open);
  if (!routeState.open) return;
  const plan = currentPlan();
  const colors = ['#bb8355', '#58a0a3', '#5d7e69', '#b46d5a', '#688b92', '#9273a0', '#b09154'];
  const firstVisits = new Map();
  const days = activeDays();
  days.forEach((day, dayIndex) => {
    const points = day.stops.map(routePlace).filter(Boolean);
    for (const place of points) if (!firstVisits.has(place.id)) firstVisits.set(place.id, dayIndex);
    for (let i = 1; i < points.length; i++) {
      const rail = day.rail && routeState.mode === 'rail';
      L.polyline([[points[i - 1].coord[1], points[i - 1].coord[0]], [points[i].coord[1], points[i].coord[0]]], {
        color: rail ? '#4d82a1' : colors[dayIndex], weight: routeState.day === dayIndex ? 4.5 : 3,
        opacity: routeState.day === null || routeState.day === dayIndex ? .87 : .24,
        dashArray: rail ? '2 8' : '8 8', interactive: false,
      }).addTo(routeLayer);
    }
  });
  [...firstVisits].forEach(([id, dayIndex], index) => {
    const place = routePlace(id);
    const active = routeState.day === null || days[routeState.day].stops.includes(id);
    const icon = L.divIcon({ className: 'route-icon', iconSize: [37, 43], iconAnchor: [18, 38], html: `<span class="route-pin ${active ? 'active' : 'muted'}" style="--route-color:${colors[dayIndex]}"><strong>${index + 1}</strong><small>D${dayIndex + 1}</small><span class="route-label">${esc(place.name)}</span></span>` });
    L.marker([place.coord[1], place.coord[0]], { icon, pane: 'routePane', zIndexOffset: 1000, title: `${index + 1}. ${place.name}` }).on('click', () => focusRouteDay(dayIndex)).addTo(routeLayer);
  });
}
function routeBounds(dayIndex = null) {
  const days = dayIndex === null ? activeDays() : [activeDays()[dayIndex]];
  return L.latLngBounds(days.flatMap((day) => day.stops).map(routePlace).filter(Boolean).map((place) => [place.coord[1], place.coord[0]]));
}
function fitRoute(dayIndex = null) {
  if (!routeState.open) return;
  const bounds = routeBounds(dayIndex);
  const size = map.getSize();
  const desktop = innerWidth > 850;
  const safeLeft = desktop ? (innerWidth > 1080 ? 410 : 366) : 28;
  const safeRight = desktop ? size.x - (innerWidth > 1080 ? 470 : 405) : size.x - 28;
  const safeTop = 112;
  const safeBottom = desktop ? size.y - 45 : size.y * .39 - 22;
  const padding = L.point(Math.max(0, size.x - (safeRight - safeLeft)), Math.max(0, size.y - (safeBottom - safeTop)));
  const zoom = Math.min(map.getBoundsZoom(bounds, false, padding), dayIndex === null ? 8.25 : 11.5);
  map.setView(bounds.getCenter(), zoom, { animate: false });
  map.panBy([(size.x - safeLeft - safeRight) / 2, (size.y - safeTop - safeBottom) / 2], { animate: false });
  $('#map-status').textContent = dayIndex === null ? currentPlan().name : `第 ${dayIndex + 1} 天 · ${activeDays()[dayIndex].title}`;
}
function routeUrl() {
  const params = new URLSearchParams({ route: planId(routeState.days, routeState.style), mode: routeState.mode, pace: routeState.pace, start: routeState.start });
  history.replaceState({}, '', `${location.pathname}?${params}`);
}
function focusRouteDay(index) {
  routeState.day = index;
  renderRoutePanel(); drawRoute(); fitRoute(index); routeUrl();
  $('#route-panel .route-day.active')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}
function changeRoute(changes) {
  Object.assign(routeState, changes, { day: null, open: true });
  renderRoutePanel(); drawRoute(); fitRoute(); routeUrl();
}
function toggleRoute() {
  if (routeState.open) {
    routeState.open = false; routeState.day = null;
    renderRoutePanel(); drawRoute();
    return;
  }
  if (state.selected) closePlace();
  routeState.open = true; renderRoutePanel(); drawRoute(); fitRoute(); routeUrl();
}

function fitXinjiang() {
  const desktop = innerWidth > 850;
  map.fitBounds([[34.4, 73.5], [49.4, 96.7]], { paddingTopLeft: desktop ? [420, 96] : [18, 80], paddingBottomRight: desktop ? [state.selected ? 445 : 65, 72] : [18, 115], maxZoom: desktop ? 5.6 : 5, animate: true, duration: 0.65 });
  if (!state.selected) $('#map-status').textContent = '新疆全景';
}
function focusPlace(place) {
  map.flyTo([place.coord[1], place.coord[0]], Math.max(map.getZoom(), Math.min(place.zoom, 14)), { animate: true, duration: 0.85 });
  $('#map-status').textContent = place.name;
}
function selectPlace(id) {
  const place = places.find((item) => item.id === id);
  if (!place) return;
  state.selected = place; state.sidebarOpen = false;
  routeState.open = false; renderRoutePanel(); drawRoute();
  $('#sidebar').classList.remove('mobile-open'); $('#mobile-shade').hidden = true;
  renderList(); renderDetail(); refreshMarkers(); focusPlace(place);
  history.replaceState({}, '', `?place=${encodeURIComponent(place.id)}`);
}
function closePlace() {
  state.selected = null; renderList(); renderDetail(); refreshMarkers(); $('#map-status').textContent = '自由探索';
  history.replaceState({}, '', location.pathname);
}

refreshMarkers();
$('#map-loading').classList.add('done');
const initial = urlParams.get('place');
renderRoutePanel();
if (initial && places.some((place) => place.id === initial)) selectPlace(initial);
else if (routeState.open) { drawRoute(); fitRoute(); }
else fitXinjiang();
map.on('zoomend', () => {
  $('#zoom-status').textContent = `缩放 ${map.getZoom().toFixed(1)}`;
  if (outerShade) outerShade.setStyle({ fillOpacity: Math.min(0.82, 0.24 + (map.getZoom() - 3.5) * 0.11) });
  $('#map').classList.toggle('street-zoom', map.getZoom() >= 7);
  refreshMarkers();
});
map.on('moveend', refreshMarkers);
map.fire('zoomend');
fetch(`${import.meta.env.BASE_URL}data/xinjiang.geojson`).then((response) => response.json()).then((boundary) => {
  const world = [[-85, -180], [-85, 180], [85, 180], [85, -180], [-85, -180]];
  const hole = boundary.geometry.coordinates[0].map(([longitude, latitude]) => [latitude, longitude]);
  outerShade = L.polygon([world, hole], { color: 'transparent', stroke: false, fillColor: '#f3f0e8', fillOpacity: Math.min(0.82, 0.24 + (map.getZoom() - 3.5) * 0.11), fillRule: 'evenodd', interactive: false }).addTo(map);
  L.geoJSON(boundary, { style: { color: '#b9995a', weight: 1.4, opacity: .65, fill: false, interactive: false } }).addTo(map);
  markerLayer.bringToFront?.(); clusterLayer.bringToFront?.();
}).catch((error) => console.warn('Boundary unavailable', error));

renderFilters(); renderList();
$('#filters').onclick = (event) => { const button = event.target.closest('[data-group]'); if (!button) return; state.group = button.dataset.group; renderFilters(); renderList(); refreshMarkers(); };
$('#search').oninput = (event) => { state.query = event.target.value.trim(); renderList(); refreshMarkers(); };
$('#place-list').onclick = (event) => { const row = event.target.closest('[data-place]'); if (row) selectPlace(row.dataset.place); };
$('#detail-panel').onclick = (event) => { if (event.target.closest('#close-detail')) closePlace(); if (event.target.closest('#focus-place') && state.selected) focusPlace(state.selected); };
$('#route-toggle').onclick = toggleRoute;
$('#route-panel').onclick = (event) => {
  const target = event.target.closest('button');
  if (!target) return;
  if (target.id === 'close-route') toggleRoute();
  else if (target.id === 'fit-route') fitRoute();
  else if (target.dataset.days) changeRoute({ days: Number(target.dataset.days) });
  else if (target.dataset.style) changeRoute({ style: target.dataset.style });
  else if (target.dataset.mode) changeRoute({ mode: target.dataset.mode });
  else if (target.dataset.pace) changeRoute({ pace: target.dataset.pace });
  else if (target.dataset.day !== undefined) focusRouteDay(Number(target.dataset.day));
  else if (target.dataset.stop) selectPlace(target.dataset.stop);
};
$('#route-panel').onchange = (event) => { if (event.target.id === 'route-start' && /^\d{4}-\d{2}-\d{2}$/.test(event.target.value)) changeRoute({ start: event.target.value }); };
$('#zoom-in').onclick = () => map.zoomIn(); $('#zoom-out').onclick = () => map.zoomOut(); $('#fit-map').onclick = fitXinjiang; $('#fit-top').onclick = fitXinjiang;
$('#menu-button').onclick = () => { state.sidebarOpen = true; $('#sidebar').classList.add('mobile-open'); $('#mobile-shade').hidden = false; };
$('#mobile-shade').onclick = () => { state.sidebarOpen = false; $('#sidebar').classList.remove('mobile-open'); $('#mobile-shade').hidden = true; };
document.addEventListener('keydown', (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#search').focus(); } if (event.key === 'Escape') { if (state.sidebarOpen) $('#mobile-shade').click(); else if (state.selected) closePlace(); } });
