# 以撒开荒解锁规划器

一个纯前端的《以撒的结合》开荒解锁规划器。浏览器直接读取 `persistentgamedata*.dat` 的成就块，根据角色、Boss、挑战和其他成就展示解锁奖励，并用推荐优先级帮助新档决定先刷什么。

[点击这里尝试](https://momo-tori.github.io/isaac_unlock_planner/)

## 主要功能

- 本地读取 `persistentgamedata*.dat`，不会上传存档。
- 默认打开 **总攻略**：汇总项目现有的角色、挑战与其他成就，无需先选择角色。
- 总攻略支持六类内容任意组合，提供 **全部 / 仅角色 / 仅挑战** 快捷筛选、关键词搜索，并合并重复成就。
- 按 **角色 / Boss / 挑战解锁 / 其他成就** 查看解锁进度。
- 新浏览器默认按解锁排名排序，也可选择重要度、社区强度或默认顺序。
- 支持隐藏已解锁目标，只保留还需要完成的内容。
- 支持在页面内调整推荐优先级，并导出 / 导入本地推荐配置。
- 提供离线单文件版本 `isaac-unlock-planner-offline.html`。
- 可选的本地启动入口：绑定存档、每 30 秒自动同步，并创建 Windows 桌面快捷方式。

## 总攻略

总攻略复用原页面的数据、奖励效果、推荐方案、优先级菜单和存档状态。分类可任意组合；勾选多个分类取并集，同一成就只出现一次。关闭 **显示已解锁** 后，可按解锁排名参考下一批目标；有前置时先推进主线，并行任务随正常局累计。

| 分类 | 内容 |
|---|---|
| 角色通关 | 所有表 / 里角色的 Boss 目标及捆绑解锁条件 |
| 挑战奖励 | 全部 45 个挑战、前置成就开放状态及奖励 |
| 主线推进 | 主线成就的条件与奖励 |
| 角色解锁 | 表 / 里角色的解锁条件 |
| 次数 / 累计 | 多次通关、捐款等累计目标 |
| 完成类成就 | 其他完成条件与奖励 |

“仅角色”同时选中角色通关与角色解锁；“仅挑战”只选中挑战奖励。分类组合、排序与显示已解锁设置会在本浏览器中保留。搜索可以使用角色中英文名、Boss 名称、奖励名、解锁条件或成就 ID。

当前版本整合原项目的 **606 个不同成就目标**（340 条角色通关规则、45 个挑战奖励及其他成就，去重后计数）。这是项目现有数据的总览，不代表游戏全部 641 个成就均已有详细攻略；挑战前置成就的状态仍展示在对应挑战内。

## 直接使用

1. 通过 GitHub Pages、普通 FTP 静态空间、本地 HTTP 服务，或直接双击 `index.html` 打开页面。
2. 点击 **读取 persistentgamedata**，或把 `.dat` 拖到顶部区域。
3. 在总攻略中组合分类，或切换至原有视图查看解锁目标。
4. 载入存档后关闭 **显示已解锁**，即可只看未完成目标。

页面顶部会提示常见 Windows 存档位置：

```text
%USERPROFILE%\Documents\My Games\Binding of Isaac Repentance
%USERPROFILE%\Documents\My Games\Binding of Isaac Repentance+\save_backups
```

在其中寻找时间最近的 `...persistentgamedata*.dat`；文件名中星号 `*` 对应第几个存档。

Steam 云存档也可能在 `Steam/userdata/<账号数字ID>/250900/remote/` 下。Repentance+ 常用文件名为 `rep+persistentgamedata1.dat`，请根据自己使用的版本、存档槽和修改时间选择，不要误选备份或其他账号的存档。

## 本地启动与自动同步（Windows，可选）

普通静态网页和离线版仍可直接使用，无需安装运行环境。只有自动读取绑定文件时，需要 Node.js 20 或更新版本；本地服务不需要安装任何 npm 依赖。

1. 在项目根目录创建 `.local/config.json`，填入自己正在使用的存档文件绝对路径，例如：

   ```json
   {
     "port": 18789,
     "savePath": "E:/Steam/userdata/12345678/250900/remote/rep+persistentgamedata1.dat"
   }
   ```

   JSON 路径使用 `/`，或将反斜线写成 `\\`。`savePath` 也支持相对于项目根目录的路径；如 Node.js 不在 PATH 中，可增加 `nodePath` 指定 `node.exe` 的绝对路径。

2. 双击根目录的 **`Start-Planner.cmd`**。它在后台启动本地服务，确认就绪后用默认浏览器打开总攻略；重复打开会复用已有服务。
3. 可在 PowerShell 中运行以下命令创建带项目图标的桌面入口：

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\create-shortcut.ps1 -Name "以撒解锁总攻略"
   ```

绑定成功后，页面顶部显示本地同步状态，每 30 秒以及重新聚焦页面时检查一次。游戏写入文件后可点击 **立即同步**；写入尚未完成或服务暂时中断时保留上次成功读取的进度，稍后重试。

**暂停自动同步** 可暂时固定进度；手动读取其他存档或清除缓存也会暂停同步，点击 **立即同步** 或 **恢复自动同步** 可重新读取绑定文件。修改绑定配置后需要重启本地服务。

服务只监听 `127.0.0.1`，只读绑定文件，不修改游戏存档。静态文件仅开放页面、脚本、数据和图片；本机绑定路径、存档、日志及测试产物均存放在已忽略的 `.local/` 中，不会被提交。不要将整个项目目录用普通静态服务器公开到外网。

## 推荐配置

- 首次打开时，页面会把内置推荐方案复制到当前站点的 `localStorage`。
- 每条角色/Boss、挑战和其他成就记录右侧都有优先级菜单，可改成 `strong / recommended / normal / discouraged`。
- 未自定义的内置方案会在刷新时载入最新评级；已经修改或导入的自定义配置完整保留。需要采用新版内置方案时，先导出自己的配置，再在推荐方案中选择 **萌新开荒推荐**。
- 当前配置可导出为 JSON，也可以重新导入。
- 同一目标同时属于角色通关和其他成就时，共用优先级；导入旧配置存在冲突时，明确设置的成就优先级优先，后续编辑会同步更新两种记录。
- 成功读取的存档原始内容也会保存在 `localStorage`，下次进入会自动重新解析。普通静态页面在游戏进度更新后仍需重新选择最新 `.dat`；绑定本地启动入口后自动同步。

### 研究排名与评级修订（2026-11-04）

研究目标是提高后续全角色打标效率、最终完成全成就。已研究 **65/606 项目标**，其中 **55 项有编号的解锁建议、10 项为并行任务**。编号表示研究范围内的编辑综合建议，前置开放、熟练度和路线机会仍需考虑；不是依赖完整的逐步通关流程或统计最优顺序。每日、捐款与特定角色起始能力可随主线推进，不要求先做完才能开始编号列表。

四种排序的口径：

| 排序 | 含义 |
| --- | --- |
| 解锁排名 | 先显示并行提醒，再按研究建议名次排列，未评审条目随后；筛选或隐藏已解锁不会重编号 |
| 社区强度 | 按 Unduel 的全局原始名次排列，覆盖271个已确认的道具解锁目标，无需先经过综合复核；缺少适用名次的目标随后。多道具奖励取其中最靠前名次排序，分别显示各道具名次 |
| 重要度顺序 | 按当前推荐配置的四档颜色分组，可保留个人调整 |
| 默认顺序 | 原项目的角色、Boss、挑战或成就顺序 |

页面同时显示 **道具强度参考** 与 **解锁优先级**。例如神性强度为 S，但获取成本高，解锁优先级为推荐；死亡证明是强度顶端的终盘奖励。每条研究记录可展开“评级依据”，查看条件、取舍、置信度、来源和旧/新评级。综合研究覆盖之外的目标，已有社区名次时照常显示，并标注“尚未综合复核解锁顺序”；已有颜色不表示本轮已复核。没有适用社区名次的饰品、卡牌、机制等目标，不套用收藏道具排名。

**道具总榜** 页面收录来源榜单的全部 **719 条记录**，支持中文名、英文名、道具 ID 搜索，保留原始全局名次和每件道具的投票记录数。与项目目标对应的道具可直接跳转查看解锁条件和存档进度；总攻略支持 `#6` 形式的精确成就 ID 搜索。初始道具等无对应解锁目标的条目也保留在总榜中。65项综合复核、55项解锁顺序建议、719条社区名次是不同范围，不能互相替代。

全量源保存在 [tools/community_rankings.json](tools/community_rankings.json)。其中718条可对应道具实体 ID，另有来源排名第710的旧版 Tonsil 条目：该条保留并注明，不将它误配给当前 ID474 的损坏的玻璃大炮，也不套用于扁桃体饰品。夏娃起始剃刀片、游魂起始神圣屏障属于起始装备升级，不作为对应道具入池解锁参与社区排序。

在已有基础上修订 **18 项**优先级：

| 目标 | 修订 |
| --- | --- |
| 商店600捐款升级、更贪婪模式 | 普通 → 推荐 |
| 里莉莉丝 | 普通 → 强烈推荐，作为作孽双子前置 |
| 店主起始木制硬币 | 推荐 → 强烈推荐，适用于已开放店主时 |
| 马骑符文、被吞下的硬币、符文袋 | 强烈推荐 → 推荐，保留机制和组合条件 |
| D20、选择？、嗝屁猫的眼睛 | 强烈推荐 → 推荐，计入运营条件和取得成本 |
| 谷底石、达摩克里斯、十字圣球 | 强烈推荐 → 推荐，计入组合、死亡风险或困难角色成本 |
| 巴风特之印、生死逆转、无底坑 | 强烈推荐 → 推荐，计入挑战、操作与路线成本 |
| D8 | 强烈推荐 → 普通，评价分歧与属性波动明显 |
| 编号丢失 | 普通 → 不推荐提前解锁，最终清标仍需完成 |

参考 [jnub 解锁取舍指南](https://steamcommunity.com/sharedfiles/filedetails/?id=2994836310)、[完整 Rep+ 路线](https://steamcommunity.com/sharedfiles/filedetails/?id=3712501774)、[NiCobra 解锁依赖图](https://maniacobra.com/isaac-graph/)、中文打标路线与 IsaacGuru 机制资料，逐项来源保存在 [tools/research_rankings.json](tools/research_rankings.json)。名次和颜色为编辑性综合，没有直接平均不同口径榜单。社区名次单独引自 [Unduel](https://unduel.com/t/the-binding-of-isaac-rebirth/the-binding-of-isaac-items-75IgVOPw3H343hrv6Vh4MP/ranked-list) 的719件道具榜、2026-10-28快照，版本标注为 Repentance；投票偏好不等于胜率，也不冒充忏悔+专榜或多来源共识。饰品、卡牌不在该榜范围。

### 多来源综合公式与试算（2026-11-04）

[公式与权重](docs/research/ensemble-v1/ensemble-formula-v1.md)、[试算报告](docs/research/ensemble-v1/ensemble-trial-report-v1.md)和[完整718项结果](docs/research/ensemble-v1/ensemble-results-v1.csv)提供一版可重算的综合强度排名。它将已核验的原始比较按来源质量、版本、覆盖与曝光加权，同源合并限权，再求统一分数；相对等级采用S前5%、A累计前20%、B累计前45%、C累计前70%、D累计前90%、F后10%。

本轮纳入Unduel 718项、Best Item 399项及Another Matt已核对的天使池S级12项，共399项有至少两族意见、319项仍是单来源估计。结果附来源数及13种情景的敏感性名次范围；该范围不代表统计置信区间。饰品、卡牌与解锁成本另行处理，资料缺失不补造名次。页面当前仍显示上文说明的原始社区榜，综合公式试算作为独立研究数据保留，详见同目录的冻结输入、检查记录与复算脚本。

## 目录

```text
index.html
isaac-unlock-planner-offline.html
styles.css
js/
  app.js
  guide.js
  rankings.js
  save-parser.js
data/
  unlocks.js
  challenges.js
  achievements.js
  effects.js
  effects-report.json
  overrides.js
  recommendation_profiles.js
  research_rankings.js
assets/
  icon.png
  character/
  boss/
  achievement/
    Achievement_sprite.jpg
tools/
  data-rebuild.md
  rebuild_data.py
  build_unlocks.py
  build_challenges.py
  build_achievements.py
  crawl_effects.py
  prepare_publish.py
  local-server.cjs
  start-planner.ps1
  create-shortcut.ps1
  achievement_priority.json
  research_rankings.json
  community_rankings.json
  build_research_rankings.py
tests/
  guide.test.cjs
  local-server.test.cjs
  browser-smoke.js
  local-sync-smoke.js
  offline-smoke.js
  ratings-smoke.js
  test_recommendation_profiles.py
  rankings.test.cjs
  rankings-smoke.js
  community-smoke.js
  test_research_rankings.py
Start-Planner.cmd
```

## 开发与数据维护

数据生成、效果抓取、推荐配置校验、离线单文件构建等维护流程见 [tools/data-rebuild.md](tools/data-rebuild.md)。

存档解析由 `js/save-parser.js` 完成，只读取当前工具需要的 Achievement block。工具不会修改存档，也不需要 CRC 写回逻辑。

筛选与本地服务的回归检查使用 Node.js 内置测试，无额外依赖：

```powershell
node --test tests/guide.test.cjs tests/rankings.test.cjs tests/local-server.test.cjs
python tools/validate_priorities.py
python -m unittest discover -s tests -p "test_*.py"
```

浏览器检查可使用 Playwright CLI（本机需安装 Edge），在本地服务运行后执行：

```powershell
npm install --prefix .local/browser-tools --no-audit --no-fund @playwright/cli
.\.local\browser-tools\node_modules\.bin\playwright-cli.cmd -s=isaac open http://127.0.0.1:18789/ --browser=msedge
.\.local\browser-tools\node_modules\.bin\playwright-cli.cmd -s=isaac run-code --filename=tests/browser-smoke.js
# 已绑定存档时，额外检查同步暂停、清除缓存与恢复行为：
.\.local\browser-tools\node_modules\.bin\playwright-cli.cmd -s=isaac run-code --filename=tests/local-sync-smoke.js
# 使用隔离测试浏览器打开本地服务上的离线 HTML，可运行 offline-smoke.js；它会清空该测试浏览器的本站存储并阻断其他请求。
# 使用隔离测试浏览器可运行 ratings-smoke.js，验证补评、旧内置方案更新和自定义配置保留。
# rankings-smoke.js 检查排名、社区版本说明、评级修订、组合筛选及自定义颜色保留；同样需隔离浏览器。
# community-smoke.js 检查全量719条、271个目标映射、尚未综合复核条目的社区名次、总榜搜索和旧版条目隔离。
.\.local\browser-tools\node_modules\.bin\playwright-cli.cmd -s=isaac close
```

## 图片说明

- 网页图标使用 `assets/icon.png`。
- 角色头像读取本地 `assets/character/<characterId>.png`。
- Boss 选择图读取本地 `assets/boss/<bossId>.png`。
- 奖励和成就图片使用 `assets/achievement/Achievement_sprite.jpg`，按 Achievement ID 定位。

## 数据来源

- 角色、Boss、挑战和成就数据：灰机 Wiki 保存页。
- 挑战奖励名称辅助核对：IsaacGuru Challenges。
- 存档结构：灰机 Wiki `Persistentgamedata.js`。
- 高价值推荐：狐九郎整理的 Bilibili 动态，以及项目用户提供的当前版本修订。
- 效果构建源：External Item Descriptions 的简体中文 / 英文数据。
- Boss 图片：网络素材与自修改绘制图片。
- 角色图片、网页图标和 Achievement 图标：项目内素材。
