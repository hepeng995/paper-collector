---
name: paper-collector
description: "自动收集最新最全的学术论文，支持6大数据源，可配置关键词和时间范围。"
tags: ["academic", "papers", "research", "arxiv", "citation"]
---

# Paper Collector - 学术论文自动收集器

自动收集最新、最全的学术论文，用于毕业论文参考文献。

## 数据源

| 来源 | 特点 | 更新频率 |
|------|------|----------|
| arXiv RSS | CS/AI 最新预印本 | 每日 |
| Hugging Face Daily | 社区投票热门论文 | 每日 |
| Papers With Code | 有代码的论文 | 每日 |
| OpenAlex | 2.5亿+ 全学科 | 实时 |
| Semantic Scholar | 2亿+ 引用分析 | 实时 |
| CrossRef | 1.5亿+ 正式出版 | 实时 |

## 使用方法

### 1. 交互式模式（推荐）

```bash
python3 scripts/collect.py
```

运行后会依次询问：
- 搜索关键词
- 时间范围
- 数量限制
- 输出目录
- 输出格式
- 是否爬取详情

### 2. 命令行模式

```bash
python3 scripts/collect.py \
  --query "large language model" \
  --days 30 \
  --limit 50 \
  --output ./papers \
  --format both \
  --crawl
```

### 3. 在 AI 助手中使用

直接告诉 AI：
> "帮我收集 large language model 最近 30 天的论文"

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --query | 搜索关键词 | 必填 |
| --days | 最近天数 | 30 |
| --limit | 每个来源最大数量 | 50 |
| --output | 输出目录 | ./papers |
| --format | 输出格式 (md/bib/both/json) | both |
| --crawl | 爬取论文详情 | false |

## 输出文件

- `latest_papers.md` - Markdown 格式论文列表
- `latest_papers.bib` - BibTeX 格式（LaTeX 用）
- `papers.json` - JSON 格式（程序处理用）

## 在其他平台使用

### Claude Code

1. 将此文件夹放到项目中
2. 在 Claude Code 中运行：
   > 帮我运行 paper-collector 收集最新论文

### Cursor / Windsurf

1. 将此文件夹放到项目中
2. 在 AI 助手中运行：
   > 运行 scripts/collect.py 收集论文

### 任何支持 Python 的环境

```bash
python3 scripts/collect.py --query "你的关键词"
```
