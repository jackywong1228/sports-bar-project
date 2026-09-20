// 场地小程序码 scene 值 → 桌号名称 映射表
//
// 背景：场馆内张贴的小程序码（wxacode.getUnlimited，page=pages/food-menu/food-menu）
// 通过 scene 参数携带场地编码，顾客扫码进入点单页后自动填好桌号（仍可修改）。
// scene 只能用 ASCII（微信限制：数字、大小写英文及部分符号，≤32 字符）。
//
// 以后新增场地码：在下方映射或循环规则里加一行即可，无需改点单页代码。

const SCENE_TABLE_MAP = {
  PK1: '匹克球1号场',
  PK2: '匹克球2号场',
  GOLF1: '高尔夫包厢',
  SQ1: '壁球1号场',
  SQ2: '壁球2号场',
  TEN1: '网球发球机学练场',
}

// 室外吧台 OUT1~OUT12、室内 IN1~IN7 按规则批量生成
for (let i = 1; i <= 12; i++) SCENE_TABLE_MAP['OUT' + i] = '室外吧台' + i + '号'
for (let i = 1; i <= 7; i++) SCENE_TABLE_MAP['IN' + i] = '室内' + i + '号'

// scene → 桌号名称；未知 scene 返回空串（点单页回退到上次保存的桌号/手动输入）
function sceneToTableNo(scene) {
  if (!scene) return ''
  const key = String(scene).trim().toUpperCase()
  return SCENE_TABLE_MAP[key] || ''
}

module.exports = {
  SCENE_TABLE_MAP,
  sceneToTableNo,
}
