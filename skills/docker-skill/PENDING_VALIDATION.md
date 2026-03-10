# docker-skill 资源场景验证待办

**状态：** 等待 Docker daemon 可用  
**创建：** 2026-03-08

## 验证清单（4 条）

- [ ] `docker ps` 正常
- [ ] `docker stats` 有真实 CPU / 内存输出
- [ ] 轻量容器可观测
- [ ] 高资源容器场景下，timeout / 资源信号是否稳定

## 触发条件

Docker daemon 可用时，跑这 4 条，结果写进 CHANGELOG.md。

## 完成后

更新 docker-skill CHANGELOG.md 和 SKILL.md，把"待补测"改为"已验证"。
更新 SKILLS_V2_REGRESSION_REPORT.md 状态。
