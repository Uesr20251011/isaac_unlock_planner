"""Publish readable research artifacts from the computed results, without changing the app."""
import collections
import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'ensemble-results-v1.json').read_text('utf-8'))
    entries=result['entries']; n=len(entries)
    tiers=collections.Counter(row['relativeTier'] for row in entries)
    stable=sum(row['tierStability']==1 for row in entries)
    source_ids={row['id']:row['family'] for row in result['sourceAudit']}
    def rank(value):return str(int(value)) if value==int(value) else str(value)
    def position(row):return f"{row['weightScenarioRankMin']}–{row['weightScenarioRankMax']}"
    def table(rows):
        lines=['| 排名 | 道具 | 分数 | 等级 | 来源族数 | 敏感性名次范围 |',
               '|---:|---|---:|:---:|---:|---:|']
        for row in rows:
            lines.append(f"| {rank(row['rank'])} | {row['nameZh']} / {row['name']} | {row['score']:.1f} | {row['relativeTier']} | {row['familyCount']} | {position(row)} |")
        return '\n'.join(lines)
    lines=[
        '# 以撒道具综合试算报告 v1',
        '',
        '2026-11-04。已完成公式、完整试算名次、总分、相对分级及敏感性检查。本轮结果是研究产物，网页目前仍保留既有社区榜。',
        '',
        '**推荐采用来源去重、版本与覆盖折扣、来源影响上限约束的成对偏好公式。** 先把各来源可核实的“i优于j”合并，再拟合潜在强度，输出对本次候选集合的0–100综合相对偏好分。详式、权重表、选择理由见[公式说明](ensemble-formula-v1.md)。',
        '',
        '## 资料覆盖',
        '',
        f'- 本次计算{n}个收藏道具：来自既有719条原榜中能对应到当前实体的718条。不是606个成就，也不宣称覆盖游戏全部隐藏实体或所有补丁新增道具。',
        f"- 独立来源族{result['familyCount']}个：Unduel 718项、Best Item 399项、Another Matt已核对的天使池S级12项。Matt这12项均在Best Item覆盖内。",
        f"- 至少两族覆盖{result['multipleSourceItems']}项，其中12项三族；另{n-result['multipleSourceItems']}项只有Unduel，必须保留单来源标记。",
        '- Best Item原始接口返回400条，逐项映射后排除当前集合以外的C551铲子第二碎片。站点id不当作游戏id；399项不存在重复映射。原始同分组内不编造先后。',
        '- 饰品、卡牌及路线/角色功能不混进收藏道具强度总榜。黄油、碎裂王冠等饰品需要独立的饰品比较集合和来源；本模型没有给未收集到评价的奖励补造低分或总名次。',
        '',
        '本轮没有把中文开荒路线、历史解锁优先级表和项目65条编辑建议复制成独立强度选票。它们继续用于解锁成本、前置路线与机制复核。神性强度很高，不代表新档应该第9个去解锁神性。',
        '',
        '## 分数与分级约定',
        '',
        '来源初始权重 = 质量q × 目标相关性r × 来源级曝光饱和H × 覆盖折扣 × 版本系数，并按比较数量归一化、同源合并限额。主试算q为Unduel0.80、Best Item0.65、Matt0.75；版本系数目前均0.60。这些是公开的人工默认判断，没有真实通关标签支持“最优权重”之说。',
        '',
        '最终总分 = 对候选集合中其余道具的模型偏好概率之平均 × 100。分数不是实战胜率、伤害倍率或百分位。榜内总分均值为50；增加候选道具或新来源可能改变分数，不宜跨版本直接相减。',
        '',
        '按用户选择，等级只表示相对位置：S前5%、A累计前20%、B累计前45%、C累计前70%、D累计前90%、F后10%。本轮人数：'+ '、'.join(f'{tier}{tiers[tier]}项' for tier in 'SABCDF')+'。精确并列保留共同名次区间，跨边界显示双等级。',
        '',
        '仅展示一位小数，排序用未四舍五入的模型结果。相近分数不代表能够可靠分辨谁实战更强，例如本次D6与神性都显示87.8分。',
        '',
        '## 前20项',
        '',
        table(entries[:20]),
        '',
        '## 代表性分歧项',
        '',
    ]
    names={'Godhead','The Stairway','Spirit Sword','The Wafer','Stop Watch','Crown of Light',
           'Broken Modem','Glowing Hourglass','Lil Portal'}
    lines.extend([table([row for row in entries if row['name'] in names]),'',
        '这里的范围合并13种情景：三族权重各上下25%、正则0.01/0.1、曝光半饱和参数25/100、线性覆盖折扣、可形成完整榜的两种留一来源。是参数与来源敏感性范围，不是95%置信区间。',
        '',
        f'{stable}/{n}项在所选13种情景中等级保持一致。单来源条目即使分级稳定，也不等于得到了多源共识。天堂阶梯的具体名次变动明显，但本轮各情景均为S；损坏的调制解调器处于A/B边界，应保留争议标记。',
        '',
        '## 来源之间的一致程度',
        '',
        '| 来源对 | 共同道具 | 双方都严格排序的比较对数 | 一致比例 |',
        '|---|---:|---:|---:|'])
    for pair in result['sourceAgreements']:
        lines.append(f"| {source_ids[pair['first']]} / {source_ids[pair['second']]} | {pair['commonItems']} | {pair['comparablePairs']} | {pair['agreement']:.1%} |")
    lines.extend(['',
        '只统计共同且双方都给出严格顺序的道具；同分组不算反对票。成千上万的比较对来自同一张榜，不能当作独立玩家数量或据此计算窄置信区间。',
        '',
        '## 留一来源与参数检查',
        '',
        '| 移除来源 | 可否形成完整718项榜 | 剩余有比较证据的道具 | 最大名次变化 |',
        '|---|:---:|---:|---:|'])
    for hold in result['holdouts']:
        lines.append(f"| {hold['removedFamily']} | {'可以' if hold['globalComparable'] else '不可以'} | {hold['observedItems']} | {rank(hold['maxRankChange']) if hold['globalComparable'] else '不编造全榜'} |")
    lines.extend(['',
        '移除Unduel后剩399项有比较证据，因此拒绝借助正则项补出319个没有依据的全榜位置。当前整体仍依赖Unduel提供连接；不能把“3个来源族”描述成每件道具都被三家验证。',
        '',
        '| 敏感性情景 | 与主榜的名次相关系数 | 最大名次变化 |',
        '|---|---:|---:|'])
    for scene in result['scenarioDiagnostics']:
        lines.append(f"| {scene['name']} | {scene['rankCorrelation']:.4f} | {rank(scene['maxRankChange'])} |")
    lines.extend(['',
        '上述相关系数只是整体排序变化的描述，不证明排名正确。中部道具、机制特殊或较有争议的道具仍可能移动上百名。',
        '',
        '## 验证与文件',
        '',
        f"主模型收敛，最大梯度{result['convergence']['gradientMax']:.2g}，13种完整榜敏感性情景均收敛。13项模型测试通过，包括数值梯度、局部榜不评价圈外、同源全表及摘录不增权、同等级不虚构次序、0票/不适用版本不参评、并列跨等级边界、完整单榜不因曝光差异被重新排列。单独Unduel的718项顺序改变数为0。",
        '',
        '- [全部718项结果（CSV）](ensemble-results-v1.csv)：含中英文名、总分、等级、来源数和敏感性范围。',
        '- [便于阅读的中文列名CSV](道具综合试算榜-v1.csv)。',
        '- [完整公式与来源权重](ensemble-formula-v1.md)。',
        '- [冻结输入快照](ensemble-inputs-v1.json)、[完整结果与检查记录](ensemble-results-v1.json)、[Best Item逐条映射审计](bestitem-mapping-audit.json)。',
        '',
        '同目录内使用Python和NumPy即可重算冻结输入：',
        '',
        '```text',
        'python -m unittest -v test_ensemble_model.py',
        'python run_ensemble.py --inputs ensemble-inputs-v1.json --sensitivity',
        'python write_trial_report.py',
        '```',
        '',
        '这套方法可作为综合总榜的v1默认公式。下一轮改进应优先补充真正独立、版本明确的完整强度来源与逐项机制修正，更新冻结快照后重算；调整权重不能替代缺少的证据。'])
    (HERE/'ensemble-trial-report-v1.md').write_text('\n'.join(lines)+'\n','utf-8')
    with (HERE/'道具综合试算榜-v1.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['总排名','道具','英文名','综合分','相对等级','独立来源数','敏感性名次范围','来源原排名','证据说明'])
        for row in entries:
            writer.writerow([rank(row['rank']),row['nameZh'],row['name'],f"{row['score']:.1f}",row['relativeTier'],
                             row['familyCount'],position(row),row['originalRank'],
                             '单来源估计' if row['familyCount']==1 else '多来源意见；敏感性范围非置信区间'])
    files=['ensemble-inputs-v1.json','ensemble-results-v1.json','ensemble-results-v1.csv','道具综合试算榜-v1.csv',
           'ensemble_model.py','run_ensemble.py','test_ensemble_model.py','prepare_bestitem.py',
           'ensemble-formula-v1.md','ensemble-trial-report-v1.md','bestitem-mapping-audit.json',
           'english-ensemble-bestitem-ranking-raw.json','english-ensemble-bestitem-api-metadata.json',
           'ensemble-sources-extra.json','write_trial_report.py']
    # Keep text integrity checks portable across Git's Windows newline conversion.
    manifest={name:hashlib.sha256((HERE/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in files}
    (HERE/'ensemble-manifest-v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(dict(total=n,stableTierItems=stable,tierCounts=dict(tiers),manifestFiles=len(manifest)),ensure_ascii=True))


if __name__=='__main__':main()
