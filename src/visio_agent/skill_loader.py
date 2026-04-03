"""
Skill 加载器 - 从 SKILL.md 文件动态加载技能
遵循 LangChain Agent Skills 规范
"""
import os
import re
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path


class Skill:
    """从 SKILL.md 加载的技能对象"""

    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        path: str,
        allowed_tools: List[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        self.name = name  # 技能名称
        self.description = description  # 技能描述
        self.content = content  # SKILL.md 完整内容
        self.path = path  # 技能目录路径
        self.allowed_tools = allowed_tools or []  # 允许使用的工具列表
        self.metadata = metadata or {}  # 元数据

    def matches(self, query: str) -> float:
        """
        计算查询与技能描述的匹配分数
        返回 0 到 1 之间的分数
        """
        query_lower = query.lower()
        desc_lower = self.description.lower()

        score = 0.0

        # 检查技能名称关键词
        if self.name.lower().replace("-", " ") in query_lower:
            score += 0.3
        if self.name.lower().replace("-", "") in query_lower.replace("-", "").replace(" ", ""):
            score += 0.3

        # 检查描述关键词重叠
        desc_words = set(re.findall(r'\w+', desc_lower))
        query_words = set(re.findall(r'\w+', query_lower))

        # 词汇重叠
        overlap = desc_words & query_words
        if overlap:
            score += min(0.4, len(overlap) * 0.1)

        return min(1.0, score)


class SkillLoader:
    """从 SKILL.md 文件加载和管理技能"""

    _skills: Dict[str, Skill] = {}
    _skills_dir: Optional[str] = None

    @classmethod
    def load_skills_from_dir(cls, skills_dir: str) -> None:
        """
        从包含技能子目录的目录加载所有技能

        Args:
            skills_dir: 包含技能文件夹的目录路径
        """
        cls._skills_dir = skills_dir
        cls._skills = {}

        skills_path = Path(skills_dir)
        if not skills_path.exists():
            return

        for skill_dir in skills_path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                skill = cls._parse_skill_file(str(skill_md), str(skill_dir))
                if skill:
                    cls._skills[skill.name] = skill
            except Exception as e:
                print(f"加载技能失败 {skill_md}: {e}")

    @classmethod
    def _parse_skill_file(cls, file_path: str, skill_dir: str) -> Optional[Skill]:
        """解析 SKILL.md 文件，提取 frontmatter 和内容"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 分离 frontmatter 和内容
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        if not frontmatter_match:
            # 无 frontmatter，使用目录名作为名称
            name = os.path.basename(os.path.dirname(file_path))
            return Skill(
                name=name,
                description="",
                content=content,
                path=skill_dir,
            )

        frontmatter_text = frontmatter_match.group(1)
        body_content = frontmatter_match.group(2)

        # 解析 YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            frontmatter = {}

        name = frontmatter.get("name", os.path.basename(skill_dir))
        description = frontmatter.get("description", "")
        allowed_tools = frontmatter.get("allowed-tools", [])
        metadata = frontmatter.get("metadata", {})

        return Skill(
            name=name,
            description=description,
            content=body_content,
            path=skill_dir,
            allowed_tools=allowed_tools,
            metadata=metadata,
        )

    @classmethod
    def get_skill(cls, name: str) -> Optional[Skill]:
        """根据名称获取技能"""
        return cls._skills.get(name)

    @classmethod
    def get_all_skills(cls) -> Dict[str, Skill]:
        """获取所有已加载的技能"""
        return cls._skills.copy()

    @classmethod
    def all_skill_names(cls) -> List[str]:
        """获取所有已加载技能的名称"""
        return list(cls._skills.keys())

    @classmethod
    def detect_skill(cls, query: str) -> str:
        """
        检测与查询最匹配的技能

        Args:
            query: 用户描述或请求

        Returns:
            最佳匹配技能名称，默认为 "er-diagram"
        """
        if not cls._skills:
            # 基于关键词返回默认
            return cls._keyword_detect(query)

        best_score = 0.0
        best_skill = "er-diagram"  # 默认

        for name, skill in cls._skills.items():
            score = skill.matches(query)
            if score > best_score:
                best_score = score
                best_skill = name

        if best_score == 0:
            return cls._keyword_detect(query)

        return best_skill

    @classmethod
    def _keyword_detect(cls, description: str) -> str:
        """
        基于关键词的备用检测方法
        当没有加载技能时的初始检测
        """
        desc_lower = description.lower()

        # ER 图关键词
        er_keywords = ["er图", "er 图", "实体", "关系图", "entity", "relationship", "er diagram", "chen"]
        # 流程图关键词
        flowchart_keywords = ["流程图", "流程", "flowchart", "flow chart", "process", "workflow", "工作流"]
        # 时序图关键词
        sequence_keywords = ["时序图", "sequence", "时序", "参与者", "交互", "uml", "message"]

        er_score = sum(1 for k in er_keywords if k in desc_lower)
        flowchart_score = sum(1 for k in flowchart_keywords if k in desc_lower)
        sequence_score = sum(1 for k in sequence_keywords if k in desc_lower)

        scores = {
            "er-diagram": er_score,
            "flowchart": flowchart_score,
            "sequence-diagram": sequence_score,
        }

        max_score = max(scores.values())
        if max_score == 0:
            return "er-diagram"  # 默认

        for diagram_type, score in scores.items():
            if score == max_score:
                return diagram_type

        return "er-diagram"

    @classmethod
    def get_skill_content(cls, name: str) -> str:
        """获取技能的完整内容（用于系统提示词注入）"""
        skill = cls._skills.get(name)
        if skill:
            return skill.content
        return ""

    @classmethod
    def get_skill_tools(cls, name: str) -> List[str]:
        """获取技能允许使用的工具"""
        skill = cls._skills.get(name)
        if skill:
            return skill.allowed_tools
        return []


def register_skills(skills_dir: str = None) -> None:
    """
    从技能目录注册所有技能

    Args:
        skills_dir: 技能目录路径。如果为 None，使用默认路径
    """
    if skills_dir is None:
        # 默认为 visio_agent 下的 skills 子目录
        skills_dir = os.path.join(os.path.dirname(__file__), "skills")

    SkillLoader.load_skills_from_dir(skills_dir)


# 模块导入时自动注册技能
register_skills()
