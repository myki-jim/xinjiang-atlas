// These are editorial day plans. Polylines in the UI connect anchors for
// orientation; they are not a road graph, navigation instructions or schedules.
const city = { title: '喀什慢起步', stay: '喀什', stops: ['kashgar', 'gaotai'], note: '抵达后只走古城和高台民居，为高原段留出休息时间。' };
const baisha = { title: '白沙山与湖岸', stay: '布伦口附近', stops: ['kashgar', 'baisha'], note: '沿 G314 往高原缓行，把下午留给白沙湖不同岸线；住宿和通行事先确认。' };
const karakul = { title: '雪峰、喀拉库勒湖', stay: '塔什库尔干', stops: ['baisha', 'karakul', 'stone-city'], note: '慢看慕士塔格峰下的湖面，抵达塔县后可散步石头城附近。' };
const panlong = { title: '盘龙与班迪尔蓝湖', stay: '塔什库尔干', stops: ['stone-city', 'panlong', 'osm-n13129567998', 'stone-city'], note: '山路弯多，留整天走盘龙古道和班迪尔湖岸；只在当日道路允许时进入。' };
const returnKashgar = { title: '塔合曼湿地、返回喀什', stay: '喀什', stops: ['stone-city', 'osm-n4808866521', 'kashgar'], note: '沿原有公路走塔合曼湿地观景点，长距离返回喀什，尽量不安排夜间山路。' };

export const routePlans = {
  'pamir-3': {
    name: '帕米尔 3 天精华', short: '3 天 · 紧凑', days: 3, tone: '浓缩雪山、湖泊与盘龙古道',
    intro: '适合已经到达喀什、能接受连续山路的旅客。第一天行车和海拔变化较集中。',
    daysList: [
      { title: '白沙湖、喀拉库勒湖', stay: '塔什库尔干', stops: ['kashgar', 'baisha', 'karakul', 'stone-city'], note: '从喀什出发，沿 G314 上高原；留意天气和身体适应情况。' },
      panlong,
      returnKashgar,
    ],
  },
  'pamir-5': {
    name: '昆仑 5 天慢环线', short: '5 天 · 均衡', days: 5, tone: '把雪峰和湖泊分开两天看',
    intro: '从喀什出发并返回；在布伦口和塔县分段停留，比 3 天方案更从容。',
    daysList: [city, baisha, karakul, panlong, returnKashgar],
  },
  'pamir-7-remote': {
    name: '昆仑与西极 · 7 天', short: '7 天 · 壮阔小众', days: 7, tone: '高原湖泊、盘龙、边境荒原与红山峡谷',
    intro: '优先广阔地貌，走喀什—帕米尔—西极—奥依塔克。西极日需提前核查边境通行证，节假日也无法保证人少。',
    daysList: [
      city, baisha, karakul, panlong, returnKashgar,
      { title: '向西极去，看荒原', stay: '喀什', stops: ['kashgar', 'xiji', 'kashgar'], note: '吉根乡方向为边境管理区；提前办妥通行证，并核实当天道路与景区开放。往返距离长，不赶夜路。', permit: true },
      { title: '奥依塔克红山与冰川', stay: '喀什 / 返程', stops: ['kashgar', 'oytakh', 'osm-w1428173533', 'kashgar'], note: '把最后一天留给红山峡谷和冰川公园；出行前确认开放、道路和返程时间。' },
    ],
  },
  'pamir-7-slow': {
    name: '帕米尔与莎车 · 7 天', short: '7 天 · 古城慢行', days: 7, tone: '雪山湖泊之后接叶尔羌的老街巷',
    intro: '保留帕米尔的大景观，最后两天放慢节奏到莎车；铁路方案可在喀什—莎车段换乘。',
    daysList: [
      city,
      { ...baisha, stops: ['kashgar', 'oytakh', 'baisha'], note: '途中可择一处奥依塔克红山观景，再沿 G314 到白沙湖；不要把所有观景点塞进一天。' },
      karakul, panlong, returnKashgar,
      { title: '叶尔羌古城街巷', stay: '莎车', stops: ['kashgar', 'shache', 'osm-w958776273'], note: '走莎车老城和叶尔羌汗国王陵；铁路方案在喀什—莎车之间乘车，市内接驳另计。', rail: true },
      { title: '莎车晨光、回到喀什', stay: '喀什 / 返程', stops: ['shache', 'kashgar'], note: '留半天给街巷和返程；铁路方案以 12306 当日可购车次为准。', rail: true },
    ],
  },
};

export function planId(days, style) {
  return days === 7 ? `pamir-7-${style}` : `pamir-${days}`;
}

export const routeSources = [
  { title: '自治区文旅厅 · 帕米尔精品线路', url: 'https://wlt.xinjiang.gov.cn/wlt/c112786/202402/04ec109e9ce24ac5aa955ca8eb8c6c7a.shtml' },
  { title: '新疆 2026 年国庆放假安排', url: 'https://www.xinjiang.gov.cn/xinjiang/tzgg/202512/aaece21b6906443e8d50b981070764a8.shtml' },
  { title: '克州边境通行证说明', url: 'https://www.xjkz.gov.cn/xjkz/c102165/202307/e661dc3ce5534e55bca0bb30c8735474.shtml' },
  { title: '铁路 12306 实时查询', url: 'https://www.12306.cn/' },
];
