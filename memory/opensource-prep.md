# AIOS 开源准备清单

**创建时间：** 2026-03-07 04:18  
**目标：** 将 AIOS 项目准备好开源发布

---

## 📋 核心检查项

### 1. 代码清理
- [ ] 移除所有硬编码的个人信息（路径、API密钥、Telegram ID等）
- [ ] 检查所有配置文件，确保使用环境变量或配置模板
- [ ] 清理测试数据和临时文件
- [ ] 移除或归档废弃代码

### 2. 文档完善
- [x] README.md（已有）
- [x] QUICKSTART.md（已有）
- [x] ARCHITECTURE.md（已有）
- [x] CONTRIBUTING.md（已有）
- [ ] 补充安装文档（多平台）
- [ ] API文档
- [ ] 示例代码和教程
- [ ] FAQ

### 3. 许可证和法律
- [x] LICENSE 文件（已有）
- [ ] 确认所有依赖的许可证兼容性
- [ ] 添加版权声明
- [ ] 第三方组件归属说明

### 4. 测试覆盖
- [ ] 单元测试覆盖率 >80%
- [ ] 集成测试
- [ ] 端到端测试
- [ ] CI/CD 配置（GitHub Actions）

### 5. 安全审查
- [ ] 扫描敏感信息泄露
- [ ] 依赖安全漏洞检查
- [ ] 代码安全审计
- [ ] 设置 SECURITY.md

### 6. 发布准备
- [ ] 版本号规范（语义化版本）
- [ ] CHANGELOG.md 完善
- [ ] Release Notes
- [ ] PyPI 打包配置
- [ ] Docker 镜像

### 7. 社区准备
- [ ] Issue 模板
- [ ] PR 模板
- [ ] Code of Conduct
- [ ] 贡献指南
- [ ] Roadmap 公开

---

## 🔍 需要特别关注的文件

### 配置文件
- `config.yaml` - 确保没有硬编码密钥
- `env_config.json` - 提供模板文件
- `.gitignore` - 确保敏感文件不被提交

### 个人化内容
- `USER.md` - 移除或提供模板
- `IDENTITY.md` - 移除或提供模板
- `MEMORY.md` - 不应包含在开源版本中
- `memory/` 目录 - 添加到 .gitignore

### 测试数据
- `demo_data/` - 确保是通用示例
- `*.jsonl` 日志文件 - 清理或提供示例

---

## 📦 打包策略

### 开源版本（GitHub）
- 完整源代码
- 文档和示例
- 测试套件
- CI/CD 配置

### PyPI 版本
- 核心功能包
- 最小依赖
- 安装脚本

### Docker 版本
- 预配置环境
- 一键启动
- 示例配置

---

## ⏰ 时间规划

### Phase 1: 代码清理（1-2天）
- 移除敏感信息
- 配置模板化
- 清理废弃代码

### Phase 2: 文档完善（2-3天）
- 补充安装文档
- API 文档
- 示例和教程

### Phase 3: 测试和安全（3-5天）
- 提升测试覆盖率
- 安全审查
- CI/CD 配置

### Phase 4: 发布准备（1-2天）
- 版本发布
- PyPI 打包
- Docker 镜像

### Phase 5: 社区准备（1天）
- Issue/PR 模板
- 贡献指南
- 宣传材料

**预计总时间：** 8-13天

---

## 🎯 优先级

### P0（必须完成）
- 移除敏感信息
- 基础文档完善
- LICENSE 确认
- 安全审查

### P1（重要）
- 测试覆盖率提升
- CI/CD 配置
- PyPI 打包
- Docker 镜像

### P2（可选）
- 详细 API 文档
- 视频教程
- 社区运营准备

---

## 📝 检查清单模板

开源前最终检查：
```bash
# 1. 敏感信息扫描
git grep -i "password\|secret\|token\|api_key" --cached

# 2. 个人路径检查
git grep -i "C:\\Users\\A" --cached
git grep -i "/Users/shanhuhai" --cached

# 3. 测试运行
pytest tests/ -v

# 4. 打包测试
python setup.py sdist bdist_wheel

# 5. Docker 构建测试
docker build -t aios:test .
docker run --rm aios:test python -c "import aios; print(aios.__version__)"
```

---

**下一步行动：** 等待珊瑚海确认开源时间表，然后按优先级逐项完成。
