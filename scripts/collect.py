#!/usr/bin/env python3
"""
Paper Collector - 学术论文自动收集器
自动收集最新、最全的学术论文，用于毕业论文参考文献。
"""

import requests
import xml.etree.ElementTree as ET
import json
import os
import re
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

class PaperDetailCrawler:
    """爬取论文详情"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl_arxiv_detail(self, arxiv_url: str) -> Dict:
        """爬取 arXiv 论文详情"""
        try:
            response = self.session.get(arxiv_url, timeout=30)
            if response.status_code == 200:
                content = response.text
                detail = {
                    'url': arxiv_url,
                    'pdf_url': arxiv_url.replace('/abs/', '/pdf/'),
                    'source': 'arXiv',
                    'crawled': True
                }
                title_match = re.search(r'<title>(.*?)</title>', content)
                if title_match:
                    detail['title'] = title_match.group(1).replace(' arXiv:', '').strip()
                return detail
            return {'url': arxiv_url, 'crawled': False}
        except Exception as e:
            return {'url': arxiv_url, 'crawled': False, 'error': str(e)}
    
    def crawl_semantic_scholar_detail(self, paper_id: str) -> Dict:
        """爬取 Semantic Scholar 论文详情"""
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
            params = {
                "fields": "title,abstract,authors,year,citationCount,referenceCount,externalIds,openAccessPdf"
            }
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                detail = {
                    'title': data.get('title'),
                    'abstract': data.get('abstract'),
                    'authors': [a.get('name') for a in data.get('authors', [])],
                    'year': data.get('year'),
                    'citation_count': data.get('citationCount'),
                    'reference_count': data.get('referenceCount'),
                    'external_ids': data.get('externalIds', {}),
                    'pdf_url': data.get('openAccessPdf', {}).get('url') if data.get('openAccessPdf') else None,
                    'source': 'Semantic Scholar',
                    'crawled': True
                }
                return detail
            return {'crawled': False}
        except Exception as e:
            return {'crawled': False, 'error': str(e)}
    
    def crawl_openalex_detail(self, work_id: str) -> Dict:
        """爬取 OpenAlex 论文详情"""
        try:
            url = f"https://api.openalex.org/works/{work_id}"
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                detail = {
                    'title': data.get('title'),
                    'abstract': data.get('abstract_inverted_index'),
                    'authors': [a.get('author', {}).get('display_name') for a in data.get('authorships', [])],
                    'year': data.get('publication_year'),
                    'doi': data.get('doi'),
                    'citation_count': data.get('cited_by_count'),
                    'pdf_url': data.get('open_access', {}).get('oa_url'),
                    'source': 'OpenAlex',
                    'crawled': True
                }
                return detail
            return {'crawled': False}
        except Exception as e:
            return {'crawled': False, 'error': str(e)}
    
    def enrich_paper(self, paper: Dict) -> Dict:
        """丰富论文信息"""
        if paper.get('source') == 'arXiv' and paper.get('link'):
            detail = self.crawl_arxiv_detail(paper['link'])
            paper.update(detail)
        elif paper.get('source') == 'Semantic Scholar' and paper.get('link'):
            paper_id = paper['link'].split('/')[-1]
            detail = self.crawl_semantic_scholar_detail(paper_id)
            paper.update(detail)
        elif paper.get('source') == 'OpenAlex' and paper.get('doi'):
            work_id = paper['doi'].replace('https://doi.org/', '')
            detail = self.crawl_openalex_detail(work_id)
            paper.update(detail)
        return paper


class PaperCollector:
    def __init__(self):
        self.papers = []
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.crawler = PaperDetailCrawler()
    
    def get_arxiv_rss(self, categories: List[str] = None, max_results: int = 50) -> List[Dict]:
        """从 arXiv RSS 获取最新论文（每日更新）"""
        if categories is None:
            categories = ["cs.AI", "cs.CL", "cs.LG"]
        
        print(f"📡 正在获取 arXiv 最新论文...")
        papers = []
        
        for cat in categories:
            url = f"http://export.arxiv.org/rss/{cat}"
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    for item in root.findall('.//item')[:max_results]:
                        title = item.find('title').text.strip() if item.find('title') is not None else ''
                        link = item.find('link').text.strip() if item.find('link') is not None else ''
                        description = item.find('description').text.strip() if item.find('description') is not None else ''
                        pubDate = item.find('pubDate').text.strip() if item.find('pubDate') is not None else ''
                        paper = {
                            'title': title,
                            'link': link,
                            'abstract': description,
                            'published': pubDate[:10] if pubDate else '',
                            'source': 'arXiv',
                            'category': cat
                        }
                        papers.append(paper)
                        self.papers.append(paper)
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ 获取 {cat} 失败: {e}")
        
        print(f"  ✅ 获取 {len(papers)} 篇最新论文")
        return papers
    
    def get_arxiv_api(self, query: str, max_results: int = 50) -> List[Dict]:
        """从 arXiv API 获取最新论文"""
        print(f"📡 正在搜索 arXiv: {query}...")
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            root = ET.fromstring(response.content)
            papers = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                paper = {
                    'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                    'authors': [a.find('{http://www.w3.org/2005/Atom}name').text 
                               for a in entry.findall('{http://www.w3.org/2005/Atom}author')],
                    'abstract': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
                    'link': entry.find('{http://www.w3.org/2005/Atom}id').text,
                    'published': entry.find('{http://www.w3.org/2005/Atom}published').text[:10],
                    'source': 'arXiv'
                }
                papers.append(paper)
                self.papers.append(paper)
            print(f"  ✅ 获取 {len(papers)} 篇论文")
            return papers
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return []
    
    def get_huggingface_daily(self, limit: int = 30) -> List[Dict]:
        """从 Hugging Face 获取每日热门论文"""
        print("🤗 正在获取 Hugging Face Daily Papers...")
        url = "https://huggingface.co/api/daily_papers"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                papers = []
                for item in data[:limit]:
                    paper_data = item.get('paper', {})
                    paper = {
                        'title': paper_data.get('title', ''),
                        'authors': [a.get('name', '') for a in paper_data.get('authors', [])],
                        'abstract': paper_data.get('abstract', ''),
                        'link': f"https://arxiv.org/abs/{paper_data.get('id', '')}",
                        'published': paper_data.get('publishedAt', '')[:10],
                        'upvotes': paper_data.get('upvotes', 0),
                        'source': 'HuggingFace Daily'
                    }
                    papers.append(paper)
                    self.papers.append(paper)
                print(f"  ✅ 获取 {len(papers)} 篇热门论文")
                return papers
            else:
                print(f"  ❌ 获取失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return []
    
    def get_papers_with_code(self, query: str, limit: int = 30) -> List[Dict]:
        """从 Papers With Code 获取有代码的最新论文"""
        print(f"💻 正在获取 Papers With Code: {query}...")
        url = "https://paperswithcode.com/api/v1/papers/"
        params = {
            "q": query,
            "ordering": "-published_date",
            "items_per_page": limit
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                papers = []
                for item in data.get('results', []):
                    paper = {
                        'title': item.get('title', ''),
                        'authors': item.get('authors', []),
                        'abstract': item.get('abstract', ''),
                        'link': f"https://paperswithcode.com{item.get('url_abs', '')}",
                        'published': item.get('published', ''),
                        'arxiv_id': item.get('arxiv_id', ''),
                        'source': 'Papers With Code'
                    }
                    papers.append(paper)
                    self.papers.append(paper)
                print(f"  ✅ 获取 {len(papers)} 篇论文（有代码）")
                return papers
            else:
                print(f"  ❌ 获取失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return []
    
    def get_openalex(self, query: str, limit: int = 50) -> List[Dict]:
        """从 OpenAlex 获取论文（最全面）"""
        print(f"📚 正在搜索 OpenAlex: {query}...")
        url = "https://api.openalex.org/works"
        params = {
            "search": query,
            "per_page": limit,
            "sort": "publication_date:desc",
            "filter": "publication_year:2024-2026"
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            papers = []
            for work in data.get("results", []):
                paper = {
                    'title': work.get("title"),
                    'authors': [a.get("author", {}).get("display_name") for a in work.get("authorships", [])],
                    'year': work.get("publication_year"),
                    'doi': work.get("doi"),
                    'citation_count': work.get("cited_by_count"),
                    'source': 'OpenAlex'
                }
                papers.append(paper)
                self.papers.append(paper)
            print(f"  ✅ 获取 {len(papers)} 篇论文")
            return papers
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return []
    
    def get_semantic_scholar(self, query: str, limit: int = 50) -> List[Dict]:
        """从 Semantic Scholar 获取论文（引用分析）"""
        print(f"📚 正在搜索 Semantic Scholar: {query}...")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,abstract,citationCount,publicationDate",
            "sort": "publicationDate:desc"
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            papers = []
            for paper in data.get("data", []):
                paper_info = {
                    'title': paper.get("title"),
                    'authors': [a.get("name") for a in paper.get("authors", [])],
                    'year': paper.get("year"),
                    'abstract': paper.get("abstract"),
                    'citation_count': paper.get("citationCount"),
                    'published': paper.get("publicationDate"),
                    'source': 'Semantic Scholar'
                }
                papers.append(paper_info)
                self.papers.append(paper_info)
            print(f"  ✅ 获取 {len(papers)} 篇论文")
            return papers
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return []
    
    def get_crossref(self, query: str, limit: int = 50) -> List[Dict]:
        """从 CrossRef 获取论文（正式出版物）"""
        print(f"📚 正在搜索 CrossRef: {query}...")
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "rows": limit,
            "sort": "deposited",
            "order": "desc",
            "filter": "from-pub-date:2024-01-01"
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            papers = []
            for item in data.get("message", {}).get("items", []):
                paper = {
                    'title': item.get("title", [None])[0],
                    'authors': [f"{a.get('given', '')} {a.get('family', '')}" 
                               for a in item.get("author", [])],
                    'year': item.get("published-print", {}).get("date-parts", [[None]])[0][0],
                    'doi': item.get("DOI"),
                    'citation_count': item.get("is-referenced-by-count"),
                    'source': 'CrossRef'
                }
                papers.append(paper)
                self.papers.append(paper)
            print(f"  ✅ 获取 {len(papers)} 篇论文")
            return papers
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            return []
    
    def enrich_all_papers(self):
        """丰富所有论文的详情"""
        print(f"🔍 正在爬取论文详情...")
        enriched_count = 0
        for i, paper in enumerate(self.papers):
            if paper.get('link') and not paper.get('abstract'):
                try:
                    self.papers[i] = self.crawler.enrich_paper(paper)
                    if self.papers[i].get('crawled'):
                        enriched_count += 1
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ 爬取失败: {e}")
        print(f"  ✅ 成功爬取 {enriched_count} 篇论文详情")
        return self.papers
    
    def deduplicate(self) -> List[Dict]:
        """去重"""
        seen = set()
        unique_papers = []
        for paper in self.papers:
            title = paper.get("title", "").lower().strip()
            if title and title not in seen:
                seen.add(title)
                unique_papers.append(paper)
        self.papers = unique_papers
        return unique_papers
    
    def filter_recent(self, days: int = 30) -> List[Dict]:
        """只保留最近 N 天的论文"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        self.papers = [p for p in self.papers 
                       if p.get('published', '') and p.get('published', '') >= cutoff_date]
        print(f"📅 筛选出最近 {days} 天的论文: {len(self.papers)} 篇")
        return self.papers
    
    def sort_by_date(self) -> List[Dict]:
        """按发布日期排序"""
        self.papers.sort(key=lambda x: x.get('published', ''), reverse=True)
        return self.papers
    
    def export_markdown(self, filename: str = "latest_papers.md"):
        """导出 Markdown 格式"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 最新论文合集\n\n")
            f.write(f"收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"共 {len(self.papers)} 篇论文\n\n")
            f.write("---\n\n")
            for i, paper in enumerate(self.papers, 1):
                f.write(f"## {i}. {paper.get('title', 'N/A')}\n\n")
                if paper.get('authors'):
                    authors = paper['authors'][:5]
                    f.write(f"- **作者**: {', '.join(authors)}\n")
                f.write(f"- **发布日期**: {paper.get('published', 'N/A')}\n")
                f.write(f"- **来源**: {paper.get('source', 'N/A')}\n")
                if paper.get('citation_count'):
                    f.write(f"- **引用次数**: {paper['citation_count']}\n")
                if paper.get('upvotes'):
                    f.write(f"- **社区投票**: {paper['upvotes']}\n")
                if paper.get('doi'):
                    f.write(f"- **DOI**: {paper['doi']}\n")
                if paper.get('link'):
                    f.write(f"- **链接**: {paper['link']}\n")
                if paper.get('pdf_url'):
                    f.write(f"- **PDF**: {paper['pdf_url']}\n")
                if paper.get('abstract'):
                    abstract = paper['abstract'][:200] + '...' if len(paper['abstract']) > 200 else paper['abstract']
                    f.write(f"- **摘要**: {abstract}\n")
                f.write("\n")
        print(f"✅ 已导出 {len(self.papers)} 篇论文到 {filename}")
    
    def export_bibtex(self, filename: str = "latest_papers.bib"):
        """导出 BibTeX 格式"""
        with open(filename, "w", encoding="utf-8") as f:
            for i, paper in enumerate(self.papers, 1):
                key = f"paper{i}"
                f.write(f"@article{{{key},\n")
                f.write(f"  title = {{{paper.get('title', '')}}},\n")
                f.write(f"  author = {{{' and '.join(paper.get('authors', []))}}},\n")
                if paper.get('year'):
                    f.write(f"  year = {{{paper['year']}}},\n")
                if paper.get('doi'):
                    f.write(f"  doi = {{{paper['doi']}}},\n")
                if paper.get('link'):
                    f.write(f"  url = {{{paper['link']}}},\n")
                f.write(f"}}\n\n")
        print(f"✅ 已导出 BibTeX 到 {filename}")
    
    def export_json(self, filename: str = "papers.json"):
        """导出 JSON 格式"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.papers, f, ensure_ascii=False, indent=2)
        print(f"✅ 已导出 JSON 到 {filename}")


def interactive_mode():
    """交互式模式 - 询问用户参数"""
    print("=" * 60)
    print("📚 Paper Collector - 学术论文自动收集器")
    print("=" * 60)
    print()
    
    # 询问搜索关键词
    query = input("🔍 请输入搜索关键词（如: large language model）: ").strip()
    if not query:
        print("❌ 关键词不能为空")
        sys.exit(1)
    
    # 询问时间范围
    days_input = input("📅 请输入最近天数（默认 30）: ").strip()
    days = int(days_input) if days_input.isdigit() else 30
    
    # 询问数量限制
    limit_input = input("📊 请输入每个来源最大数量（默认 50）: ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 50
    
    # 询问输出目录
    output = input("📁 请输入输出目录（默认 ./papers）: ").strip()
    if not output:
        output = "./papers"
    
    # 询问输出格式
    format_choice = input("📄 请选择输出格式 (1=md, 2=bib, 3=both, 4=json)（默认 3）: ").strip()
    format_map = {'1': 'md', '2': 'bib', '3': 'both', '4': 'json'}
    output_format = format_map.get(format_choice, 'both')
    
    # 询问是否爬取详情
    crawl_input = input("🔍 是否爬取论文详情？(y/n)（默认 n）: ").strip().lower()
    crawl = crawl_input == 'y'
    
    print()
    print("=" * 60)
    print(f"📋 配置确认:")
    print(f"   关键词: {query}")
    print(f"   时间范围: 最近 {days} 天")
    print(f"   数量限制: 每个来源 {limit} 篇")
    print(f"   输出目录: {output}")
    print(f"   输出格式: {output_format}")
    print(f"   爬取详情: {'是' if crawl else '否'}")
    print("=" * 60)
    print()
    
    confirm = input("✅ 确认开始收集？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        sys.exit(0)
    
    return {
        'query': query,
        'days': days,
        'limit': limit,
        'output': output,
        'format': output_format,
        'crawl': crawl
    }


def main():
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        parser = argparse.ArgumentParser(description='学术论文自动收集器')
        parser.add_argument('--query', '-q', required=True, help='搜索关键词')
        parser.add_argument('--days', '-d', type=int, default=30, help='最近天数 (默认: 30)')
        parser.add_argument('--limit', '-l', type=int, default=50, help='每个来源最大数量 (默认: 50)')
        parser.add_argument('--output', '-o', default='./papers', help='输出目录 (默认: ./papers)')
        parser.add_argument('--format', '-f', choices=['md', 'bib', 'both', 'json'], default='both', help='输出格式 (默认: both)')
        parser.add_argument('--crawl', '-c', action='store_true', help='爬取论文详情')
        
        args = parser.parse_args()
        config = {
            'query': args.query,
            'days': args.days,
            'limit': args.limit,
            'output': args.output,
            'format': args.format,
            'crawl': args.crawl
        }
    else:
        # 交互式模式
        config = interactive_mode()
    
    # 创建输出目录
    os.makedirs(config['output'], exist_ok=True)
    
    collector = PaperCollector()
    
    print(f"{'='*60}")
    print(f"🔍 收集最新论文: {config['query']}")
    print(f"{'='*60}\n")
    
    # 收集论文
    collector.get_arxiv_rss(["cs.AI", "cs.CL", "cs.LG"], config['limit'])
    collector.get_arxiv_api(config['query'], config['limit'])
    collector.get_huggingface_daily(config['limit'])
    collector.get_papers_with_code(config['query'], config['limit'])
    collector.get_openalex(config['query'], config['limit'])
    collector.get_semantic_scholar(config['query'], config['limit'])
    collector.get_crossref(config['query'], config['limit'])
    
    # 处理
    print(f"\n{'='*60}")
    print(f"📊 处理数据")
    print(f"{'='*60}")
    
    collector.deduplicate()
    collector.filter_recent(config['days'])
    collector.sort_by_date()
    
    if config['crawl']:
        collector.enrich_all_papers()
    
    # 导出
    print(f"\n{'='*60}")
    print(f"📤 导出结果")
    print(f"{'='*60}")
    
    if config['format'] in ['md', 'both']:
        collector.export_markdown(os.path.join(config['output'], "latest_papers.md"))
    if config['format'] in ['bib', 'both']:
        collector.export_bibtex(os.path.join(config['output'], "latest_papers.bib"))
    if config['format'] == 'json':
        collector.export_json(os.path.join(config['output'], "papers.json"))
    
    print(f"\n✅ 完成！共收集 {len(collector.papers)} 篇最新论文")
    print(f"📁 输出目录: {config['output']}")


if __name__ == "__main__":
    main()
