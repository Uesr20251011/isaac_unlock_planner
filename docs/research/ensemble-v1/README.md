# 多来源道具强度公式试算 v1

先阅读[试算报告](ensemble-trial-report-v1.md)及[完整公式](ensemble-formula-v1.md)。

本目录保存冻结输入、718项分数/名次/分级、来源覆盖审计、敏感性检查、Best Item原始只读响应及复算脚本。当前有399项多来源覆盖，319项单来源估计。公开的人工默认权重不冒充实战数据学出的最优参数；结果不覆盖饰品、卡牌或全部解锁目标。

复算需要Python 3.10或更新版本及NumPy（本轮验证环境为Python 3.12、NumPy 1.26.4），不影响网页运行环境。使用冻结快照不需要联网或读取本机存档：

```text
python -m unittest -v test_ensemble_model.py
python run_ensemble.py --inputs ensemble-inputs-v1.json --sensitivity
python write_trial_report.py
```

`prepare_bestitem.py`可依据冻结道具目录重新核验400条原始记录的对应关系；它只写本目录的研究文件。`ensemble-manifest-v1.json`记录主要输入、脚本、报告和结果的SHA256（统一以LF换行核对，兼容Git的Windows换行转换），复算后可重新生成。映射审计中另存原始Best Item响应的原字节SHA256。

网页当前保留Unduel原始社区总榜，本目录为独立的综合公式研究试算。来源链接、版本局限、未纳入主公式的资料均在公式说明中列明。
