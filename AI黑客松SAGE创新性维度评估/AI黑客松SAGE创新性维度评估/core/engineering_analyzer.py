"""工程化创新分析器

维度4：分析项目的工程化程度
- CI/CD配置检测
- Docker容器化检测
- 测试覆盖率评估
- 部署方案识别
"""
import re
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class EngineeringResult:
    """工程化分析结果"""
    score: float  # 0-100分
    has_ci_cd: bool  # 是否有CI/CD配置
    has_docker: bool  # 是否有Docker配置
    has_tests: bool  # 是否有测试
    test_file_count: int  # 测试文件数量
    detected_tools: List[str]  # 检测到的工程化工具
    deployment_type: str  # 部署类型
    details: str  # 详细说明


class EngineeringAnalyzer:
    """工程化创新分析器"""
    
    # CI/CD配置文件
    CI_CD_FILES = {
        ".github/workflows": "GitHub Actions",
        ".gitlab-ci.yml": "GitLab CI",
        "azure-pipelines.yml": "Azure Pipelines",
        "Jenkinsfile": "Jenkins",
        ".circleci": "CircleCI",
        ".travis.yml": "Travis CI",
        "bitbucket-pipelines.yml": "Bitbucket Pipelines",
    }
    
    # Docker配置文件
    DOCKER_FILES = {
        "Dockerfile": "Docker",
        "docker-compose.yml": "Docker Compose",
        "docker-compose.yaml": "Docker Compose",
        ".dockerignore": "Docker",
    }
    
    # 测试相关文件/目录
    TEST_PATTERNS = [
        "test_",
        "_test.py",
        "tests/",
        "test/",
        "pytest.ini",
        "conftest.py",
        "tox.ini",
        ".coveragerc",
        # JS/TS测试
        "__tests__/",
        ".test.ts",
        ".test.tsx",
        ".test.js",
        ".spec.ts",
        ".spec.js",
        "jest.config",
        "vitest.config",
        "cypress/",
        "playwright/",
    ]
    
    # 部署相关文件
    DEPLOYMENT_FILES = {
        "kubernetes/": "Kubernetes",
        "k8s/": "Kubernetes",
        "helm/": "Helm",
        "terraform/": "Terraform",
        "serverless.yml": "Serverless Framework",
        "vercel.json": "Vercel",
        "netlify.toml": "Netlify",
        "fly.toml": "Fly.io",
        "railway.json": "Railway",
        "render.yaml": "Render",
        "Procfile": "Heroku",
        "app.yaml": "Google App Engine",
        "wrangler.toml": "Cloudflare Workers",
    }
    
    # 代码质量工具
    QUALITY_TOOLS = {
        ".pre-commit-config.yaml": "Pre-commit hooks",
        "pyproject.toml": "Modern Python tooling",
        "setup.cfg": "Setup config",
        ".pylintrc": "Pylint",
        ".flake8": "Flake8",
        "mypy.ini": "MyPy",
        ".mypy.ini": "MyPy",
        "ruff.toml": "Ruff",
        # JS/TS质量工具
        ".eslintrc": "ESLint",
        "eslint.config": "ESLint",
        ".prettierrc": "Prettier",
        "prettier.config": "Prettier",
        "biome.json": "Biome",
        "tsconfig.json": "TypeScript",
        ".husky/": "Husky Git Hooks",
        "turbo.json": "Turborepo",
    }
    
    def __init__(self):
        pass
    
    def _check_files_exist(self, directory_tree: List[str], patterns: Dict[str, str]) -> List[str]:
        """
        检查目录树中是否存在指定文件/目录
        
        Args:
            directory_tree: 目录树列表
            patterns: 文件模式 {文件名: 工具名}
            
        Returns:
            检测到的工具列表
        """
        detected = []
        tree_str = "\n".join(directory_tree).lower()
        
        for pattern, tool_name in patterns.items():
            if pattern.lower() in tree_str:
                detected.append(tool_name)
        
        return list(set(detected))
    
    def _count_test_files(self, directory_tree: List[str], python_files: List[str]) -> int:
        """
        统计测试文件数量
        
        Args:
            directory_tree: 目录树
            python_files: Python文件列表
            
        Returns:
            测试文件数量
        """
        count = 0
        all_items = directory_tree + python_files
        
        for item in all_items:
            item_lower = item.lower()
            if any(pattern in item_lower for pattern in ["test_", "_test.py", "/tests/", "/test/"]):
                count += 1
        
        return count
    
    def _analyze_readme_for_deployment(self, readme_content: str) -> str:
        """
        分析README中的部署信息
        
        Args:
            readme_content: README内容
            
        Returns:
            部署类型描述
        """
        readme_lower = readme_content.lower()
        
        deployment_keywords = {
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "docker": "Docker",
            "aws": "AWS",
            "gcp": "Google Cloud",
            "azure": "Azure",
            "heroku": "Heroku",
            "vercel": "Vercel",
            "serverless": "Serverless",
            "lambda": "AWS Lambda",
        }
        
        for keyword, deployment in deployment_keywords.items():
            if keyword in readme_lower:
                return deployment
        
        return "Unknown"
    
    def _calculate_score(self, has_ci_cd: bool, has_docker: bool, has_tests: bool,
                        test_count: int, tool_count: int, deployment_type: str) -> float:
        """
        计算工程化得分
        
        Args:
            has_ci_cd: 是否有CI/CD
            has_docker: 是否有Docker
            has_tests: 是否有测试
            test_count: 测试文件数
            tool_count: 工具数量
            deployment_type: 部署类型
            
        Returns:
            得分 0-100
        """
        score = 20.0  # 基础分
        
        # CI/CD配置 (+25分)
        if has_ci_cd:
            score += 25
        
        # Docker配置 (+20分)
        if has_docker:
            score += 20
        
        # 测试覆盖 (+20分)
        if has_tests:
            score += 10
            if test_count >= 5:
                score += 10
            elif test_count >= 2:
                score += 5
        
        # 工程化工具 (+15分)
        score += min(15, tool_count * 3)
        
        # 高级部署方案 (+10分)
        advanced_deployments = ["Kubernetes", "Serverless", "Terraform", "Helm"]
        if deployment_type in advanced_deployments:
            score += 10
        elif deployment_type not in ["Unknown", ""]:
            score += 5
        
        return min(100, max(0, score))
    
    def analyze(self, directory_tree: List[str], python_files: List[str] = None,
                readme_content: str = "") -> EngineeringResult:
        """
        分析工程化程度
        
        Args:
            directory_tree: 目录树列表
            python_files: Python文件列表
            readme_content: README内容
            
        Returns:
            EngineeringResult分析结果
        """
        python_files = python_files or []
        
        # 检测各类工程化文件
        ci_cd_tools = self._check_files_exist(directory_tree, self.CI_CD_FILES)
        docker_tools = self._check_files_exist(directory_tree, self.DOCKER_FILES)
        deployment_tools = self._check_files_exist(directory_tree, self.DEPLOYMENT_FILES)
        quality_tools = self._check_files_exist(directory_tree, self.QUALITY_TOOLS)
        
        # 统计测试文件
        test_count = self._count_test_files(directory_tree, python_files)
        
        # 分析部署类型
        if deployment_tools:
            deployment_type = deployment_tools[0]
        elif readme_content:
            deployment_type = self._analyze_readme_for_deployment(readme_content)
        else:
            deployment_type = "Unknown"
        
        # 汇总检测到的工具
        all_tools = ci_cd_tools + docker_tools + deployment_tools + quality_tools
        all_tools = list(set(all_tools))
        
        # 判断各项是否存在
        has_ci_cd = len(ci_cd_tools) > 0
        has_docker = len(docker_tools) > 0
        has_tests = test_count > 0
        
        # 计算得分
        score = self._calculate_score(
            has_ci_cd, has_docker, has_tests, 
            test_count, len(all_tools), deployment_type
        )
        
        # 生成详细说明
        details_parts = []
        if has_ci_cd:
            details_parts.append(f"CI/CD: {', '.join(ci_cd_tools)}")
        if has_docker:
            details_parts.append("已容器化")
        if has_tests:
            details_parts.append(f"测试文件: {test_count}个")
        if quality_tools:
            details_parts.append(f"代码质量工具: {', '.join(quality_tools[:3])}")
        
        if not details_parts:
            details_parts.append("未检测到明显的工程化配置")
        
        return EngineeringResult(
            score=score,
            has_ci_cd=has_ci_cd,
            has_docker=has_docker,
            has_tests=has_tests,
            test_file_count=test_count,
            detected_tools=all_tools,
            deployment_type=deployment_type,
            details="; ".join(details_parts),
        )


# 测试代码
if __name__ == "__main__":
    analyzer = EngineeringAnalyzer()
    
    test_tree = [
        ".github/",
        "  workflows/",
        "    ci.yml",
        "src/",
        "  main.py",
        "tests/",
        "  test_main.py",
        "  conftest.py",
        "Dockerfile",
        "docker-compose.yml",
        "pyproject.toml",
        "README.md",
    ]
    
    test_py_files = ["src/main.py", "tests/test_main.py", "tests/conftest.py"]
    
    result = analyzer.analyze(test_tree, test_py_files)
    print(f"得分: {result.score:.1f}")
    print(f"CI/CD: {result.has_ci_cd}")
    print(f"Docker: {result.has_docker}")
    print(f"测试: {result.has_tests} ({result.test_file_count}个)")
    print(f"工具: {result.detected_tools}")
    print(f"详情: {result.details}")
