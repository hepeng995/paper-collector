# Paper Collector

学术论文自动收集器，支持 6 大数据源。

## 功能特性

- ✅ 6 大数据源：arXiv、HuggingFace、PapersWithCode、OpenAlex、Semantic Scholar、CrossRef
- ✅ 交互式模式：运行后自动询问参数
- ✅ 命令行模式：支持直接传参
- ✅ 多种输出格式：Markdown、BibTeX、JSON
- ✅ 论文详情爬取：自动获取摘要、PDF链接等
- ✅ 自动去重：避免重复论文
- ✅ 时间筛选：只收集最新论文

## 快速开始

```bash
# 交互式模式（推荐新手）
python3 scripts/collect.py

# 命令行模式
python3 scripts/collect.py --query "large language model" --days 30
```

## 安装依赖

```bash
# 只需要 requests（通常已预装）
pip install requests
```

## 使用场景

- 毕业论文参考文献收集
- 学术研究文献调研
- 技术趋势跟踪
- 每日论文推送

## 许可证

MIT License
