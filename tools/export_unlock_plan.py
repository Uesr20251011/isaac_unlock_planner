#!/usr/bin/env python3
"""Export the public, reproducible unlock plan as a readable report and table."""
import collections
import csv
from build_recommendation_profiles import ROOT,read_json


def main():
    plan=read_json(ROOT/'tools/unlock_plan.json');rows=plan['entries'];labels=plan['resourceTypeLabels']
    directory=ROOT/'docs/research';directory.mkdir(parents=True,exist_ok=True)
    with (directory/'unlock-plan-v2.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['建议名次','并行顺序','成就ID','奖励','奖励类型','内置优先级','收藏道具综合强度','综合名次','开荒优先分','阶段','条件','相对成本点','证据类型','推荐依据','限制说明'])
        for row in rows:
            writer.writerow([row['unlockRank'],row['parallelOrder'],row['achievementId'],row['name'],
                ' / '.join(labels[t] for t in row['rewardTypes']),row['priority'],
                ' / '.join(ref['relativeTier'] for ref in row['ensembleReferences']),
                ' / '.join(str(ref['rank']) for ref in row['ensembleReferences']),row['priorityScore'],row['phaseName'],
                row['condition'],row['effort'],row['evidenceKind'],row['reason'],row['caveat']])
    priorities={'strong':'强烈推荐','recommended':'推荐','normal':'普通','discouraged':'不推荐提前解锁'}
    def table(selected):
        lines=['| 建议位置 | 奖励 | 条件 | 内置优先级 |','|---:|---|---|---|']
        for row in selected:
            lines.append(f"| {'并行 '+str(row['parallelOrder']) if row['parallelOrder'] else '#'+str(row['unlockRank'])} | {row['name']} | {row['condition']} | {priorities[row['priority']]} |")
        return '\n'.join(lines)
    types=collections.Counter(t for row in rows for t in row['rewardTypes'])
    resource_types={'card','rune','soulstone','trinket','pill','pickup','interactive'}
    lines=['# 开荒解锁顺序与特殊资源推荐 v2','',plan['date'],'',
        f"现有606个目标全部获得建议：{plan['numbered']}项固定编号与{plan['parallel']}项并行提醒。271个目标接入收藏道具综合榜，{plan['resourceCount']}个目标涉及特殊资源或互动机制。项目仍有部分游戏成就未展开为独立攻略，本轮不宣称覆盖游戏全部641项。",'',
        '## 推荐如何使用','',
        '总攻略默认按解锁排名显示。选择目标分类与奖励类型，两组筛选共同生效；同组取并集，混合奖励按成就去重。读取存档后，已记录前置全部满足的目标优先；隐藏已解锁与搜索不会重新编号。并行提醒用于安排每日、捐款及角色准备，不要求先清完才能推进主线。','',
        '道具与资源榜可切换718项综合道具榜、特殊资源推荐与719条社区原榜。资源推荐按开荒顺序显示，可多选卡牌、符文、魂石、饰品、胶囊、特殊掉落与互动资源。个人修改或导入的颜色保留，建议名次独立于个人颜色。','',
        '## 顺序计算','',
        '```text','优先分 = 收益 × 剩余价值 ÷ (1 + 相对成本点 / 100) + 路线增益 − 风险','```','',
        '收藏道具收益采用冻结综合模型分数；多道具奖励保留各自名次，基准收益取其中较高者。资源收益使用已注明的机制评估或历史作者意见；混合奖励可由明确的组合收益评估修正。资源的编辑收益分不冒充收藏道具的多榜S/A等级。','',
        '阶段依次为主线/早期准备、常规打标补强、困难角色与深层目标、终盘全成就。前置在目标前；有用目标可把必要的低收益标记提前。并行提醒不向其昂贵前置传播“第零阶段”，避免把1000捐款店主误列为新档第一步。','',
        '成本点及收益锚点是公开的编辑默认值，不是小时、局数或胜率。普通标记按目标路线成本估计，另计角色难度、捆绑标记和已明确的特殊条件。资源收益5档主要锚点为90/78/60/40/20；历史GOD/GOOD/MILD/BAD/SHIT参考锚点为90/75/55/30/15，逐项机制复核可以覆盖旧意见。','',
        '静态剩余价值：死亡证明对“后续全角色打标”取0（解锁时标记已齐，仍能帮助剩余图鉴）；超级蘑菇默认取0.5，表示仍有里角色阶段的价值。其他明确大范围完成奖励另计成本。这些默认值没有根据玩家当前存档实时学习；存档用于完成状态和已记录前置的可做性。','',
        '记录的门槛包含角色开放、挑战前置、更贪婪500捐款、秘密出口、奇怪的门等。该图不是游戏全部条件的形式证明，仍以每项目标的文字条件为准。','',
        '## 覆盖与证据','',
        '| 奖励类型 | 目标数（混合奖励可跨类型） |','|---|---:|']
    for kind,count in types.items():lines.append(f'| {labels[kind]} | {count} |')
    lines+=['',
        '收藏道具模型依旧只有399项有多来源覆盖、319项单来源估计；详见[综合公式与试算](ensemble-v1/ensemble-trial-report-v1.md)。该证据范围不因新增解锁建议而扩大。','',
        '资源部分的机制核验来自EID当前描述与wiki.gg原页面；解锁意见另参考已逐格核验的Another Matt历史解锁表。2025归档不是忏悔+的受控实战数据，也不与同作者天使池视频重复算作两家独立意见。源码、原表链接、快照标识和逐项限制保存在tools/unlock_plan_reviews.json及unlock_resource_references.json。','',
        '本轮核对了桦木符文在忏悔+召唤蝗虫、黏性镍币的新版本替换差异、木箱子与旧箱子的区别、金电池拾取伤害等。未独立核实的符文碎片精确池概率阈值不写成确定规则。','',
        '## 前20个编号建议','',table([row for row in rows if row['unlockRank'] and row['unlockRank']<=20]),'',
        '## 代表性的特殊资源','']
    examples={90,94,95,96,97,98,541,618,629,607,616,613,617,611}
    lines+=[table([row for row in rows if row['achievementId'] in examples]),'',
        '## 高强度、高成本的区别','']
    lines+=[table([row for row in rows if row['achievementId'] in {29,43,429,433,156,501,547,636}]),'',
        '神性的综合强度仍为S级第9。开荒推荐同时考虑游魂全困难标记成本，并提前安排对应必要标记；死亡证明保持终盘位置。建议名次表示本项目目标中的相对安排，不能当成固定不变的每局操作脚本。','',
        '## 重建','',
        '```text','python tools/build_unlock_plan.py --update-priorities','python tools/build_recommendation_profiles.py','python tools/build_research_rankings.py','python tools/export_unlock_plan.py','python tools/prepare_publish.py 20261105-unlocks2','```','',
        '全量数据：[606项CSV](unlock-plan-v2.csv)。自动更新仅修改公开内置方案；已自定义的浏览器配置由原有迁移逻辑保留。']
    (directory/'unlock-plan-v2.md').write_text('\n'.join(lines)+'\n','utf-8')
    print(f"Exported{len(rows)} public targets and{plan['resourceCount']} special-resource suggestions")


if __name__=='__main__':main()
