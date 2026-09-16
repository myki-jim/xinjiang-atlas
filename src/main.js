import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './style.css';
import { places, groups } from './atlasData.js';

const $ = (selector) => document.querySelector(selector);
const esc = (value = '') => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
const state = { group: '全部', query: '', selected: null, sidebarOpen: false };
const filtered = () => places.filter((place) => (state.group === '全部' || state.group === place.group) &&
  `${place.name} ${place.region} ${place.type} ${place.subtitle} ${place.note}`.toLowerCase().includes(state.query.toLowerCase()));

$('#app').innerHTML = `<div class="atlas">
  <div id="map" class="map-canvas" aria-label="可缩放的新疆街道地图"></div>
  <div id="map-loading" class="map-loading"><span class="loading-dot"></span>正在载入街道地图</div>
  <header class="topbar"><button id="menu-button" class="mobile-menu" aria-label="打开地点列表">☰</button><div class="brand"><span class="brand-mark">经纬</span><span class="brand-divider"></span><span>新疆地点图鉴</span></div><span class="topbar-note">先看地点，再决定路线</span><button id="fit-top" class="topbar-fit">⌖ &nbsp;新疆全图</button></header>
  <aside id="sidebar" class="sidebar"><div class="sidebar-head"><span class="eyebrow"><span class="eyebrow-line"></span> THE XINJIANG ATLAS / 01</span><h1>把想去的地方<br><em>放在同一张地图上。</em></h1><p>先标出新疆的地点与街巷，再慢慢挑选值得深入了解的地方。</p></div>
    <label class="search-box"><span class="search-icon">⌕</span><input id="search" type="search" autocomplete="off" placeholder="搜索地点、城市或地貌" aria-label="搜索地点" /><kbd>⌘ K</kbd></label>
    <div id="filters" class="filters" role="group" aria-label="地点类别"></div><div class="list-header"><span id="list-count">全部地点 / 20</span><span>点击查看位置 ↗</span></div><div id="place-list" class="place-list"></div>
    <div class="sidebar-foot"><span class="foot-symbol">✳</span><span>灰色区域随缩放渐隐；范围锚点仅用于比较位置，出行时请查看位置依据。</span></div></aside>
  <div class="map-controls"><button id="zoom-in" aria-label="放大地图">＋</button><button id="zoom-out" aria-label="缩小地图">−</button><span class="control-rule"></span><button id="fit-map" aria-label="新疆全图">⌖</button></div>
  <div class="map-hint"><span class="hint-dot"></span><span id="map-status">新疆全景</span><span class="hint-divider">/</span><span id="zoom-status">缩放 --</span></div>
  <section id="detail-panel" class="detail-panel" aria-live="polite"></section><div id="mobile-shade" class="mobile-shade" hidden></div>
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
  panel.innerHTML = `<div class="detail-scroll"><div class="detail-top"><span class="detail-index">FIELD NOTE / ${String(places.indexOf(place) + 1).padStart(2, '0')}</span><button id="close-detail" class="close-detail" aria-label="关闭地点卡片">×</button></div>
    <div class="detail-intro"><span class="detail-region">${esc(place.region)} <span>·</span> ${esc(place.type)}</span><h2>${esc(place.name)}</h2><p>${esc(place.subtitle)}</p></div>
    <div class="location-hero"><span>MAP / XINJIANG</span><strong>${esc(place.name)}</strong><small>${place.coord[1].toFixed(4)}° N &nbsp; ${place.coord[0].toFixed(4)}° E</small></div>
    <div class="location-card"><span class="eyebrow">ON THE MAP</span><h3>位置说明</h3><p>${esc(place.note)}</p><div class="location-bottom"><span class="precision">⌖ ${esc(place.precision)}</span><a href="${esc(place.locationSource)}" target="_blank" rel="noopener noreferrer">位置依据 ↗</a></div></div>
    <button id="focus-place" class="focus-button">在地图中定位 <span>↗</span></button></div>`;
  panel.classList.add('open');
}

const map = L.map('map', { zoomControl: false, attributionControl: false, preferCanvas: true, zoomSnap: 0.25, minZoom: 3.5, maxZoom: 19, zoomAnimation: true }).setView([42.2, 84.5], 4.35);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  crossOrigin: true,
}).addTo(map);
L.control.attribution({ prefix: false, position: 'bottomright' }).addTo(map);
const markerLayer = L.layerGroup().addTo(map);
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
  for (const place of filtered()) {
    const marker = markers.get(place.id);
    marker.setIcon(markerIcon(place, state.selected?.id === place.id));
    markerLayer.addLayer(marker);
  }
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
const initial = new URLSearchParams(location.search).get('place');
if (initial && places.some((place) => place.id === initial)) selectPlace(initial); else fitXinjiang();
map.on('zoomend', () => {
  $('#zoom-status').textContent = `缩放 ${map.getZoom().toFixed(1)}`;
  if (outerShade) outerShade.setStyle({ fillOpacity: Math.min(0.82, 0.24 + (map.getZoom() - 3.5) * 0.11) });
  $('#map').classList.toggle('street-zoom', map.getZoom() >= 7);
});
map.fire('zoomend');
fetch(`${import.meta.env.BASE_URL}data/xinjiang.geojson`).then((response) => response.json()).then((boundary) => {
  const world = [[-85, -180], [-85, 180], [85, 180], [85, -180], [-85, -180]];
  const hole = boundary.geometry.coordinates[0].map(([longitude, latitude]) => [latitude, longitude]);
  outerShade = L.polygon([world, hole], { color: 'transparent', stroke: false, fillColor: '#f3f0e8', fillOpacity: Math.min(0.82, 0.24 + (map.getZoom() - 3.5) * 0.11), fillRule: 'evenodd', interactive: false }).addTo(map);
  L.geoJSON(boundary, { style: { color: '#b9995a', weight: 1.4, opacity: .65, fill: false, interactive: false } }).addTo(map);
  markerLayer.bringToFront?.();
}).catch((error) => console.warn('Boundary unavailable', error));

renderFilters(); renderList();
$('#filters').onclick = (event) => { const button = event.target.closest('[data-group]'); if (!button) return; state.group = button.dataset.group; renderFilters(); renderList(); refreshMarkers(); };
$('#search').oninput = (event) => { state.query = event.target.value.trim(); renderList(); refreshMarkers(); };
$('#place-list').onclick = (event) => { const row = event.target.closest('[data-place]'); if (row) selectPlace(row.dataset.place); };
$('#detail-panel').onclick = (event) => { if (event.target.closest('#close-detail')) closePlace(); if (event.target.closest('#focus-place') && state.selected) focusPlace(state.selected); };
$('#zoom-in').onclick = () => map.zoomIn(); $('#zoom-out').onclick = () => map.zoomOut(); $('#fit-map').onclick = fitXinjiang; $('#fit-top').onclick = fitXinjiang;
$('#menu-button').onclick = () => { state.sidebarOpen = true; $('#sidebar').classList.add('mobile-open'); $('#mobile-shade').hidden = false; };
$('#mobile-shade').onclick = () => { state.sidebarOpen = false; $('#sidebar').classList.remove('mobile-open'); $('#mobile-shade').hidden = true; };
document.addEventListener('keydown', (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#search').focus(); } if (event.key === 'Escape') { if (state.sidebarOpen) $('#mobile-shade').click(); else if (state.selected) closePlace(); } });
