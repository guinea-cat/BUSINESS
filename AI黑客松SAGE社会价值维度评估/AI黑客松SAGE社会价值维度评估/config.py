"""配置管理模块"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent

# API Token配置
MODELSCOPE_API_TOKEN = os.getenv("MODELSCOPE_API_TOKEN", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# DeepSeek模型配置 (用于报告优化)
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "http://localhost:8000/v1")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "EMPTY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "Valdemardi/DeepSeek-R1-Distill-Qwen-32B-AWQ")

# 多Token池配置（逗号分隔）
GITHUB_TOKENS = [t.strip() for t in os.getenv("GITHUB_TOKENS", "").split(",") if t.strip()]
if GITHUB_TOKEN and GITHUB_TOKEN not in GITHUB_TOKENS:
    GITHUB_TOKENS.insert(0, GITHUB_TOKEN)

# 缓存配置
CACHE_DIR = BASE_DIR / os.getenv("CACHE_DIR", "./cache")
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 默认24小时

# 默认权重配置（社会价值评估框架 - AI黑客松专用 20/80 体系）
DEFAULT_WEIGHTS = {
    # === 基础项 (底线检查) 20分 ===
    "basic_ethics": 20,             # 伦理安全合规性基础分

    # === 核心亮点项 (深度评估) 80分 ===
    # 实际评估时会从以下四个维度中选择最突出的1个，该维度权重占亮点项的100%
    "social_impact": 80,            # 社会影响深度
    "environmental_friendliness": 80,  # 环境可持续性
    "charity_orientation": 80,      # 公益普惠导向
    "long_term_vision": 80,         # 长期愿景与变革潜力
}

# 社会价值等级划分
SOCIAL_VALUE_LEVELS = {
    (90, 100): ("卓越社会价值", "⭐⭐⭐⭐⭐"),
    (75, 89): ("显著社会价值", "⭐⭐⭐⭐"),
    (60, 74): ("良好社会价值", "⭐⭐⭐"),
    (40, 59): ("一般社会价值", "⭐⭐"),
    (0, 39): ("社会价值有限", "⭐"),
}

# 创新等级划分（兼容旧版本）
INNOVATION_LEVELS = {
    (90, 100): ("突破性创新", "⭐⭐⭐⭐⭐"),
    (75, 89): ("显著创新", "⭐⭐⭐⭐"),
    (60, 74): ("中等创新", "⭐⭐⭐"),
    (40, 59): ("渐进改进", "⭐⭐"),
    (0, 39): ("常规实现", "⭐"),
}

# 技术热度分类（2024-2025更新，支持多语言）
TECH_CATEGORIES = {
    "cutting_edge": [  # 前沿技术 (高分)
        # Python AI
        "vllm", "langchain", "langgraph", "autogen", "crewai",
        "lmdeploy", "ollama", "llamaindex", "llama-index", "dspy", "guidance",
        "outlines", "instructor", "pydantic-ai", "mirascope",
        "openai-agents", "smolagents", "agno", "phidata",
        "mem0", "letta", "browser-use", "crawl4ai",
        "unsloth", "axolotl", "trl",
        # JavaScript/TypeScript AI
        "ai", "@ai-sdk", "langchain", "llamaindex", "vercel-ai",
        "@langchain", "@anthropic-ai", "openai", "ai-sdk",
    ],
    "modern": [  # 现代技术 (中高分)
        # Python
        "transformers", "openai", "anthropic", "cohere", "together",
        "fastapi", "streamlit", "gradio", "chainlit", "mesop",
        "chromadb", "pinecone", "weaviate", "qdrant", "milvus", "pgvector",
        "sentence-transformers", "huggingface-hub",
        "litellm", "groq", "fireworks-ai", "replicate",
        "modal", "ray", "celery",
        # JavaScript/TypeScript
        "next", "react", "vue", "svelte", "solid-js",
        "hono", "elysia", "bun", "deno", "drizzle-orm", "prisma",
        "trpc", "zod", "turborepo", "nx",
    ],
    "standard": [  # 标准技术 (基础分)
        # Python
        "flask", "django", "requests", "numpy", "pandas",
        "scikit-learn", "matplotlib", "pillow", "opencv-python",
        "pydantic", "typer", "click", "rich",
        # JavaScript/TypeScript
        "express", "koa", "nestjs", "axios", "lodash",
        "typescript", "webpack", "vite", "eslint", "prettier",
    ],
}

# 工程化检测文件
ENGINEERING_FILES = {
    "ci_cd": [".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile"],
    "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
    "testing": ["pytest.ini", "setup.cfg", "pyproject.toml", "tox.ini", "conftest.py", "tests/"],
    "docs": ["docs/", "mkdocs.yml", "sphinx/", "CONTRIBUTING.md"],
    "quality": [".pre-commit-config.yaml", ".flake8", "ruff.toml", "mypy.ini"],
}

# GitHub API配置
GITHUB_API_TIMEOUT = 30  # 秒
GITHUB_MAX_RETRIES = 3

# 相似度阈值
SIMILARITY_THRESHOLD = {
    "high_risk": 0.85,  # 高风险相似度
    "medium_risk": 0.70,  # 中等风险
    "low_risk": 0.50,  # 低风险
}
