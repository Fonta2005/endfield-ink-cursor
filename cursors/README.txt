祀 · 水墨笔 — 指针组 + 水波点击特效
=====================================

【点击特效 · 这一版】
  形状   单个行波峰 → 只有一圈；环宽固定 2.0px，任何半径下都是细环
  大小   窗口 76px，环半径 9→22px
  时长   720ms（时间驱动，最高约 90fps）
  亮度   不再发白：主色用 ±偏移，且按背景亮度自适应
          背景亮(lum>0.55)：亮侧 +5、暗侧 −34  → 白底上是一圈淡灰
          背景暗(lum<0.33)：亮侧 +30、暗侧 −6  → 黑底上是一圈微光
          中间值线性过渡
  透明   只画环本身，平坦处完全透明，没有方形补丁/边界白圈
  收尾   环继续外扩，只有对比度在最后 60% 平滑归零，不是向内缩

【调参（SiInkClick\SiInkClick.cs）】
  TOTAL_MS = 720        总时长
  side = (int)(76*dpi)  面积        Rf = 9 + 13*t   扩散
  ringW = 2.0           环粗细       amp = 7.4        折射量
  hiK / loK             亮/暗强度（在构造函数里按背景亮度算）
  vis = (t-0.40)/0.60   渐隐起点
  重编：csc /nologo /unsafe /target:winexe /out:SiInkClick.exe /win32icon:app.ico
        /resource:app.ico,AppIcon /r:System.dll /r:System.Drawing.dll
        /r:System.Windows.Forms.dll SiInkClick.cs

【指针】
  · 笔身青光：玉质笔杆遮罩内的流动亮带 + 反向窄亮带 + 轻微呼吸
  · 配色贴蓝色壁纸：冷青 #68DED6、冷白光晕
  · 文本光标 44 单位、手形笔 22.5 单位
  · 1024 母版 + 预乘 alpha/线性光重采样 + 逐尺寸描边锐化

【安装】install.cmd / install-static.cmd / install.reg；还原 restore.cmd / restore.reg
  本机执行策略 Restricted，请用 .cmd 包装。

【备份】versions\v2-small-green\ 与 .zip

【版权】角色“祀”及毛笔造型版权归上海鹰角网络科技有限公司所有；个人同人作品，请勿商用。
