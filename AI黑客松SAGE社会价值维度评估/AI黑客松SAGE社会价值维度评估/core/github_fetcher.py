"""GitHub代码获取模块（优化版 - 直接使用REST API）

功能：
- 解析GitHub URL提取owner/repo
- 直接使用requests调用GitHub REST API（绕过PyGithub的SSL问题）
- 本地磁盘缓存（24小时有效）
- 优化：使用Git Tree API单次获取目录结构
"""
import re
import base64
import ssl
import os
import urllib3
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

import diskcache
import requests

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import GITHUB_TOKEN, CACHE_DIR, CACHE_TTL

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class RepoInfo:
    """仓库信息数据类"""
    owner: str
    name: str
    full_name: str
    description: str = ""
    stars: int = 0
    forks: int = 0
    language: str = ""
    topics: List[str] = field(default_factory=list)
    default_branch: str = "main"
    
    # 文件内容
    readme_content: str = ""
    requirements_content: str = ""
    pyproject_content: str = ""
    
    # 目录结构
    directory_tree: List[str] = field(default_factory=list)
    python_files: List[str] = field(default_factory=list)
    
    # 核心代码文件内容 {文件路径: 内容}
    code_files: Dict[str, str] = field(default_factory=dict)
    
    # 新增：深度GitHub数据
    open_issues_count: int = 0
    contributors_count: int = 0
    releases_count: int = 0
    last_commit_date: str = ""
    created_at: str = ""
    updated_at: str = ""
    license_name: str = ""
    
    # 社区活跃度数据
    recent_issues: List[Dict[str, Any]] = field(default_factory=list)  # 最近Issue
    recent_prs: List[Dict[str, Any]] = field(default_factory=list)  # 最近PR
    top_contributors: List[Dict[str, Any]] = field(default_factory=list)  # 主要贡献者
    
    # 依赖分析
    dependencies: List[str] = field(default_factory=list)  # 项目依赖
    
    # 研究辅助链接
    research_links: Dict[str, str] = field(default_factory=dict)


class GitHubFetcher:
    """GitHub代码获取器（直接使用REST API，绕过SSL问题）"""
    
    API_BASE = "https://api.github.com"
    
    # GitHub URL正则匹配
    URL_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/\s?#]+)"
    )
    
    def __init__(self, token: str = None):
        """初始化GitHub获取器"""
        self.token = token or GITHUB_TOKEN
        
        # 创建session，禁用SSL验证
        self.session = requests.Session()
        self.session.verify = False
        
        # 设置headers
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SAGE-Innovation-Evaluator"
        })
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        
        # 初始化缓存
        cache_path = Path(CACHE_DIR)
        cache_path.mkdir(parents=True, exist_ok=True)
        self.cache = diskcache.Cache(str(cache_path / "github_cache"))
    
    def _api_get(self, endpoint: str, timeout: int = 20, retries: int = 3) -> Optional[Dict]:
        """发起GET请求（带重试）"""
        url = f"{self.API_BASE}{endpoint}"
        
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=timeout, verify=False)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    return None  # 仓库不存在，不重试
                elif resp.status_code == 403:
                    print(f"API限流，等待重试...")
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
            except requests.exceptions.Timeout:
                print(f"请求超时，重试 {attempt + 1}/{retries}")
                continue
            except Exception as e:
                print(f"API请求失败: {e}")
                if attempt < retries - 1:
                    import time
                    time.sleep(1)
                    continue
                return None
        return None
    
    def parse_url(self, url: str) -> tuple[str, str]:
        """解析GitHub URL"""
        match = self.URL_PATTERN.match(url.strip())
        if not match:
            raise ValueError(f"无效的GitHub URL: {url}")
        owner = match.group(1)
        repo = match.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
    
    def _get_file_content(self, owner: str, repo: str, path: str) -> str:
        """获取单个文件内容"""
        data = self._api_get(f"/repos/{owner}/{repo}/contents/{path}")
        if data and data.get("encoding") == "base64":
            try:
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            except:
                return ""
        return ""
    
    def fetch(self, url: str, use_cache: bool = True) -> RepoInfo:
        """
        获取仓库信息（优化版：最少API调用）
        
        总计最多8次API调用：
        1. 仓库基本信息
        2. Git Tree（目录结构）
        3. README.md
        4. requirements.txt 或 pyproject.toml
        5-7. 最多3个核心Python文件
        """
        owner, repo_name = self.parse_url(url)
        cache_key = f"{owner}/{repo_name}"
        
        # 检查缓存
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached:
                return cached
        
        # 1. 获取仓库基本信息（1次API调用）
        repo_data = self._api_get(f"/repos/{owner}/{repo_name}")
        if not repo_data:
            raise ValueError(f"无法获取仓库信息: {owner}/{repo_name}")
        
        info = RepoInfo(
            owner=owner,
            name=repo_name,
            full_name=repo_data.get("full_name", f"{owner}/{repo_name}"),
            description=repo_data.get("description") or "",
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            language=repo_data.get("language") or "",
            default_branch=repo_data.get("default_branch", "main"),
        )
        
        # 2. 使用Git Tree API获取目录结构（1次API调用）
        tree_data = self._api_get(f"/repos/{owner}/{repo_name}/git/trees/{info.default_branch}?recursive=1")
        
        code_files_found = []
        dir_tree = []
        exclude = ["__pycache__", "node_modules", ".git", "vendor", "dist", "build", ".next", "coverage"]
        
        # 工程化检测关键文件
        engineering_keywords = [
            ".github", "dockerfile", "docker-compose", ".dockerignore",
            "jest.config", "vitest.config", "cypress", "playwright",
            ".eslintrc", "eslint.config", ".prettierrc", "biome.json",
            "tsconfig", "turbo.json", ".husky", "vercel.json", "netlify",
            "kubernetes", "k8s", "helm", "terraform", "serverless",
            "pytest", "conftest", "tox.ini", ".coveragerc",
            "pyproject.toml", "setup.cfg", ".pre-commit",
            "tests/", "test/", "__tests__",
        ]
        
        # 根据项目语言确定要搜索的文件扩展名
        lang = info.language.lower() if info.language else ""
        if lang in ["typescript", "javascript"]:
            code_extensions = (".ts", ".tsx", ".js", ".jsx")
        elif lang == "python":
            code_extensions = (".py",)
        elif lang in ["go", "golang"]:
            code_extensions = (".go",)
        elif lang == "rust":
            code_extensions = (".rs",)
        elif lang == "java":
            code_extensions = (".java",)
        else:
            code_extensions = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")
        
        if tree_data and "tree" in tree_data:
            for item in tree_data["tree"][:500]:  # 增加处理数量
                path = item.get("path", "")
                item_type = item.get("type", "")
                path_lower = path.lower()
                
                # 跳过排除的路径（但保留工程化文件）
                is_engineering = any(kw in path_lower for kw in engineering_keywords)
                if any(e in path_lower for e in exclude) and not is_engineering:
                    continue
                
                # 目录树：保留前3层 + 所有工程化相关文件
                parts = path.split("/")
                if len(parts) <= 3 or is_engineering:
                    dir_tree.append(path + ("/" if item_type == "tree" else ""))
                
                # 收集代码文件（优先核心文件）
                if item_type == "blob" and path.endswith(code_extensions) and len(code_files_found) < 5:
                    if any(k in path_lower for k in ["main", "app", "core", "api", "agent", "index", "server"]):
                        code_files_found.insert(0, path)
                    elif len(code_files_found) < 5:
                        code_files_found.append(path)
        
        info.directory_tree = dir_tree[:100]  # 增加目录树条目
        info.python_files = code_files_found[:5]
        
        # 3. 获取关键文件（根据语言类型）
        info.readme_content = self._get_file_content(owner, repo_name, "README.md")
        
        # 根据语言获取依赖文件
        if lang in ["typescript", "javascript"]:
            info.requirements_content = self._get_file_content(owner, repo_name, "package.json")
        else:
            info.requirements_content = self._get_file_content(owner, repo_name, "requirements.txt")
            if not info.requirements_content:
                info.pyproject_content = self._get_file_content(owner, repo_name, "pyproject.toml")
        
        # 4. 获取核心代码文件（最多3个）
        for code_file in info.python_files[:3]:
            content = self._get_file_content(owner, repo_name, code_file)
            if content:
                info.code_files[code_file] = content
        
        # 5. 获取深度GitHub数据（额外API调用）
        self._fetch_deep_github_data(info, owner, repo_name, repo_data)
        
        # 6. 生成研究辅助链接
        info.research_links = self._generate_research_links(info)
        
        # 缓存结果
        self.cache.set(cache_key, info, expire=CACHE_TTL)
        
        return info
    
    def _fetch_deep_github_data(self, info: RepoInfo, owner: str, repo_name: str, repo_data: Dict) -> None:
        """
        获取深度GitHub数据（Issue、PR、Contributors等）
        """
        # 基本元数据
        info.open_issues_count = repo_data.get("open_issues_count", 0)
        info.created_at = repo_data.get("created_at", "")
        info.updated_at = repo_data.get("updated_at", "")
        info.license_name = repo_data.get("license", {}).get("name", "") if repo_data.get("license") else ""
        
        # 获取最近Issue（功能请求 vs Bug的比例可以说明项目成熟度）
        try:
            issues_data = self._api_get(f"/repos/{owner}/{repo_name}/issues?state=all&per_page=10&sort=created&direction=desc")
            if issues_data:
                info.recent_issues = [
                    {
                        "title": issue.get("title", ""),
                        "state": issue.get("state", ""),
                        "labels": [l.get("name", "") for l in issue.get("labels", [])],
                        "created_at": issue.get("created_at", ""),
                        "is_pr": "pull_request" in issue,
                    }
                    for issue in issues_data[:10]
                ]
        except:
            pass
        
        # 获取主要贡献者
        try:
            contributors_data = self._api_get(f"/repos/{owner}/{repo_name}/contributors?per_page=5")
            if contributors_data:
                info.contributors_count = len(contributors_data)
                info.top_contributors = [
                    {
                        "login": c.get("login", ""),
                        "contributions": c.get("contributions", 0),
                        "html_url": c.get("html_url", ""),
                    }
                    for c in contributors_data[:5]
                ]
        except:
            pass
        
        # 获取最近commit日期
        try:
            commits_data = self._api_get(f"/repos/{owner}/{repo_name}/commits?per_page=1")
            if commits_data and len(commits_data) > 0:
                info.last_commit_date = commits_data[0].get("commit", {}).get("committer", {}).get("date", "")
        except:
            pass
        
        # 获取Release数量
        try:
            releases_data = self._api_get(f"/repos/{owner}/{repo_name}/releases?per_page=10")
            if releases_data:
                info.releases_count = len(releases_data)
        except:
            pass
    
    def _generate_research_links(self, info: RepoInfo) -> Dict[str, str]:
        """
        生成研究辅助链接（帮助评委快速查找相关资料）
        """
        links = {}
        
        # 从项目描述和README中提取关键词
        text = f"{info.description} {info.readme_content[:500]}"
        keywords = self._extract_search_keywords(text, info.topics)
        
        # 生成各平台搜索链接
        if keywords:
            keyword_query = "+".join(keywords[:3])
            
            # GitHub搜索（同类项目）
            links["github_search"] = f"https://github.com/search?q={keyword_query}&type=repositories&s=stars&o=desc"
            
            # arXiv搜索（学术论文）
            arxiv_query = "+AND+".join(keywords[:3])
            links["arxiv_search"] = f"https://arxiv.org/search/?query={arxiv_query}&searchtype=all&source=header"
            
            # Hugging Face搜索
            links["huggingface_search"] = f"https://huggingface.co/models?search={keyword_query}"
            
            # Papers With Code搜索
            links["paperswithcode_search"] = f"https://paperswithcode.com/search?q={keyword_query}"
        
        # 项目特定链接
        links["github_repo"] = f"https://github.com/{info.full_name}"
        links["github_issues"] = f"https://github.com/{info.full_name}/issues"
        links["github_prs"] = f"https://github.com/{info.full_name}/pulls"
        links["github_releases"] = f"https://github.com/{info.full_name}/releases"
        links["github_contributors"] = f"https://github.com/{info.full_name}/graphs/contributors"
        
        # Hacker News搜索
        hn_query = info.name.replace("-", " ")
        links["hackernews_search"] = f"https://hn.algolia.com/?q={hn_query}"
        
        return links
    
    def _extract_search_keywords(self, text: str, topics: List[str]) -> List[str]:
        """
        从文本中提取搜索关键词
        """
        keywords = []
        
        # 优先使用GitHub topics
        if topics:
            keywords.extend(topics[:3])
        
        # AI/ML相关关键词检测
        ai_keywords = [
            "llm", "langchain", "agent", "rag", "retrieval", "embedding", "vector",
            "gpt", "transformer", "nlp", "chatbot", "memory", "ai", "machine learning",
            "deep learning", "neural", "model", "inference", "fine-tune"
        ]
        
        text_lower = text.lower()
        for kw in ai_keywords:
            if kw in text_lower and kw not in keywords:
                keywords.append(kw)
                if len(keywords) >= 5:
                    break
        
        return keywords[:5]
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()


# 测试代码
if __name__ == "__main__":
    fetcher = GitHubFetcher()
    
    # 测试URL解析
    test_urls = [
        "https://github.com/langchain-ai/langchain",
        "github.com/openai/openai-python",
    ]
    
    for url in test_urls:
        try:
            owner, repo = fetcher.parse_url(url)
            print(f"URL: {url} -> {owner}/{repo}")
        except ValueError as e:
            print(f"Error: {e}")
