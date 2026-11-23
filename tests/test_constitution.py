"""Regression checks for the constitution resource and downstream contract."""

import unittest

from ai_devlop.cli import load_payload, SKILLS


class ConstitutionTests(unittest.TestCase):
    def test_templates_cover_required_domains(self):
        payload = load_payload()["ai-devlop-constitution"]
        domains = {
            "engineering.md": ("编码规范", "代码质量", "测试规范", "依赖管理",
                               "错误处理", "日志规范", "构建规范", "持续集成与交付", "文档规范"),
            "architecture.md": ("架构风格", "分层边界", "模块边界", "依赖规则",
                                "数据归属", "接口契约", "事务边界", "外部集成",
                                "扩展性约束", "架构测试"),
            "security.md": ("身份认证", "权限控制", "数据隔离", "敏感数据",
                            "输入校验", "安全通信", "审计日志",
                            "依赖安全", "安全错误处理", "安全测试"),
        }
        for filename, headings in domains.items():
            text = payload["assets/" + filename].decode("utf-8")
            for heading in headings:
                with self.subTest(filename=filename, heading=heading):
                    self.assertIn(heading, text)
        self.assertIn("assets/constitution.md", payload)

    def test_all_downstream_skills_read_project_rules(self):
        payload = load_payload()
        for name in SKILLS:
            if name == "ai-devlop-constitution":
                continue
            text = payload[name]["SKILL.md"].decode("utf-8")
            for filename in (".ai-dev/memory/constitution.md", "engineering.md", "architecture.md", "security.md"):
                with self.subTest(skill=name, filename=filename):
                    self.assertIn(filename, text)

    def test_constitution_templates_are_pure_and_independent(self):
        payload = load_payload()["ai-devlop-constitution"]
        forbidden_terms = ("变更与审批记录", "待批准修订", "审批主体", "首次批准日期", "L1 Reference",
                           "依据 L1", "草案未生效")
        cross_file_refs = ("constitution.md", "engineering.md", "architecture.md", "security.md")
        for asset in ("assets/constitution.md", "assets/engineering.md",
                      "assets/architecture.md", "assets/security.md"):
            text = payload[asset].decode("utf-8")
            with self.subTest(asset=asset):
                for term in forbidden_terms:
                    self.assertNotIn(term, text)
                for ref in cross_file_refs:
                    self.assertNotIn(ref, text)

    def test_java_spring_boot_preset_is_packaged_and_complete(self):
        payload = load_payload()["ai-devlop-constitution"]
        preset_key = "assets/presets/java-spring-boot.md"
        self.assertIn(preset_key, payload)
        text = payload[preset_key].decode("utf-8")
        for marker in ("通用底座规范", "单体应用专属规范", "分布式 / 微服务专属规范",
                       "Spring Boot 3", "MyBatis-Plus", "Redis"):
            self.assertIn(marker, text)

    def test_vue_ts_vite_preset_is_packaged_and_complete(self):
        payload = load_payload()["ai-devlop-constitution"]
        preset_key = "assets/presets/vue-ts-vite.md"
        self.assertIn(preset_key, payload)
        text = payload[preset_key].decode("utf-8")
        for marker in ("标准目录结构", "命名规范", "Pinia", "Vue 3", "TypeScript", "Vite"):
            self.assertIn(marker, text)

    def test_security_baseline_preset_is_packaged_and_complete(self):
        payload = load_payload()["ai-devlop-constitution"]
        preset_key = "assets/presets/security-baseline.md"
        self.assertIn(preset_key, payload)
        text = payload[preset_key].decode("utf-8")
        for marker in ("输入校验与防注入", "权限控制与防越权", "敏感数据与密码学安全",
                       "文件与网络请求安全", "业务逻辑与并发安全", "客户端代码安全"):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
