"""Guard optional UI/UX instructions shipped to both supported agents."""

import unittest

from ai_devlop.cli import SKILLS, load_payload


class UiUxLinkageTests(unittest.TestCase):
    def setUp(self):
        self.payload = load_payload()

    def test_linkage_does_not_add_a_bundled_skill(self):
        self.assertEqual(len(SKILLS), 8)
        self.assertEqual(set(self.payload), set(SKILLS))
        self.assertNotIn("ui-ux-pro-max", self.payload)

    def test_page_work_automatically_attempts_and_unavailable_capability_skips(self):
        for name in SKILLS:
            if name == "ai-devlop-constitution":
                continue
            with self.subTest(skill=name):
                text = self.payload[name]["SKILL.md"].decode("utf-8")
                section = text.split("## UI/UX 可选联动\n", 1)[1].split("## 工作流程", 1)[0]
                for rule in (
                    "自动尝试调用", "ui-ux-pro-max", "无需用户主动启用或额外确认",
                    "不涉及界面的工作跳过", "用户明确禁止时不调用",
                    "当前 Agent 提供的技能发现与加载机制", "当前会话已加载时复用",
                    "未安装、无法发现、无法加载、调用失败或所需能力不受支持",
                    "主动放弃本次调用并跳过", "不反复重试、不追问启用、不自动安装、下载或修复依赖",
                    "不阻塞主流程", "不再重复尝试已失败能力", "不声称已使用",
                    "不自动推进其他开发阶段", "不扩大本技能", "不创建子代理",
                ):
                    self.assertIn(rule, section)

    def test_design_is_actionable_without_the_external_skill(self):
        text = self.payload["ai-devlop-plan"]["SKILL.md"].decode("utf-8")
        self.assertIn("不新增强制的第四份设计文档", text)
        template = self.payload["ai-devlop-plan"]["assets/详细设计.md"].decode("utf-8")
        for rule in ("页面与交互设计", "不涉及界面时删除本节", "即使后续无法调用外部技能也能实施",
                     "关联场景", "交互状态", "响应式与可访问性", "计划验证方式"):
            self.assertIn(rule, template)

    def test_stage_boundaries_and_evidence_remain_explicit(self):
        contracts = {
            "spec": ("不提前选择配色", "建议不是已确认业务规则"),
            "clarify": ("不把建议当作用户回答", "不新建设计或实施代码"),
            "task": ("不以调用外部技能作为任务或完成标准", "不补写缺失设计"),
            "implement": ("沿用已确定的设计", "不逐页面重新选风格"),
            "check": ("不修改被检查文档", "不执行外部技能的脚本、测试或构建"),
            "verify": ("不自动修复", "未验证", "不得以构建通过、静态阅读或外部意见代替视觉和交互验证"),
        }
        for stage, rules in contracts.items():
            text = self.payload["ai-devlop-" + stage]["SKILL.md"].decode("utf-8")
            for rule in rules:
                with self.subTest(stage=stage, rule=rule):
                    self.assertIn(rule, text)


if __name__ == "__main__":
    unittest.main()
