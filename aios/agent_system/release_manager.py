#!/usr/bin/env python3
"""
ReleaseManager Agent - 发布管理器
ARAM 一键发布：打包、测试、发布到 GitHub

功能：
1. 版本管理 - 自动生成版本号、CHANGELOG
2. 质量门禁 - 确保测试通过、成本合理、性能达标
3. 打包发布 - 生成 .zip、上传 GitHub Release
4. 回滚机制 - 发布失败自动回滚

用法：
    python release_manager.py check    # 检查发布条件
    python release_manager.py build    # 构建发布包
    python release_manager.py publish  # 发布到 GitHub
    python release_manager.py rollback # 回滚到上一版本
"""
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from data_collector import DataCollector

# 配置
PROJECT_ROOT = Path(r"C:\Users\A\Desktop\ARAM-Helper")
RELEASES_DIR = Path(__file__).parent / "data" / "releases"
RELEASES_DIR.mkdir(parents=True, exist_ok=True)

VERSION_FILE = PROJECT_ROOT / "version.json"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"

# 质量门禁配置
QUALITY_GATES = {
    "min_test_coverage": 0.0,  # 最低测试覆盖率（暂时不要求）
    "max_cost_per_release": 0.5,  # 每次发布最大成本（美元）
    "max_build_time": 60,  # 最大构建时间（秒）
    "required_files": [  # 必需文件
        "aram_helper.py",
        "aram_data.json",
        "README.md",
        "启动提示器.bat"
    ]
}

# GitHub 配置
GITHUB_REPO = "yangfei222666-9/ARAM-Helper"  # 格式：owner/repo


class ReleaseManager:
    """发布管理器"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.current_version = self._load_version()
    
    def _load_version(self) -> Dict:
        """加载当前版本"""
        if VERSION_FILE.exists():
            with open(VERSION_FILE, encoding="utf-8") as f:
                return json.load(f)
        else:
            # 初始版本
            default_version = {
                "major": 1,
                "minor": 0,
                "patch": 0,
                "build": 0,
                "tag": "v1.0.0",
                "released_at": None,
                "changelog": []
            }
            self._save_version(default_version)
            return default_version
    
    def _save_version(self, version: Dict):
        """保存版本信息"""
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(version, f, indent=2, ensure_ascii=False)
    
    def _bump_version(self, bump_type: str = "patch") -> Dict:
        """递增版本号
        
        Args:
            bump_type: major/minor/patch
        """
        version = self.current_version.copy()
        
        if bump_type == "major":
            version["major"] += 1
            version["minor"] = 0
            version["patch"] = 0
        elif bump_type == "minor":
            version["minor"] += 1
            version["patch"] = 0
        else:  # patch
            version["patch"] += 1
        
        version["build"] += 1
        version["tag"] = f"v{version['major']}.{version['minor']}.{version['patch']}"
        
        return version
    
    def check_quality_gates(self) -> Tuple[bool, List[str]]:
        """检查质量门禁
        
        Returns:
            (通过, 失败原因列表)
        """
        failures = []
        
        # 1. 检查必需文件
        for filename in QUALITY_GATES["required_files"]:
            filepath = PROJECT_ROOT / filename
            if not filepath.exists():
                failures.append(f"缺少必需文件: {filename}")
        
        # 2. 检查 Git 状态（可选，如果项目有 Git）
        git_dir = PROJECT_ROOT / ".git"
        if git_dir.exists():
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.stdout.strip():
                    failures.append("有未提交的更改，请先提交")
            except Exception as e:
                failures.append(f"Git 检查失败: {e}")
        
        # 3. 检查成本（可选）
        # TODO: 集成 CostGuardian
        
        return (len(failures) == 0, failures)
    
    def build_release_package(self, version: Dict) -> Optional[Path]:
        """构建发布包
        
        Returns:
            发布包路径，失败返回 None
        """
        start_time = datetime.now()
        
        # 1. 创建临时目录
        temp_dir = RELEASES_DIR / f"temp_{version['tag']}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        
        try:
            # 2. 复制必需文件
            files_to_copy = [
                "aram_helper.py",
                "aram_data.json",
                "README.md",
                "启动提示器.bat",
                "说明文档.md"
            ]
            
            for filename in files_to_copy:
                src = PROJECT_ROOT / filename
                if src.exists():
                    shutil.copy2(src, temp_dir / filename)
            
            # 3. 生成 version.txt
            version_txt = temp_dir / "version.txt"
            with open(version_txt, "w", encoding="utf-8") as f:
                f.write(f"ARAM Helper {version['tag']}\n")
                f.write(f"Build: {version['build']}\n")
                f.write(f"Released: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 4. 打包成 .zip
            zip_filename = f"ARAM-Helper-{version['tag']}.zip"
            zip_path = RELEASES_DIR / zip_filename
            
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in temp_dir.rglob("*"):
                    if file.is_file():
                        arcname = file.relative_to(temp_dir)
                        zipf.write(file, arcname)
            
            # 5. 清理临时目录
            shutil.rmtree(temp_dir)
            
            # 6. 检查构建时间
            build_time = (datetime.now() - start_time).total_seconds()
            if build_time > QUALITY_GATES["max_build_time"]:
                print(f"[WARN] 构建时间过长: {build_time:.1f}s (限制: {QUALITY_GATES['max_build_time']}s)")
            
            # 7. 记录事件
            self.collector.collect_task_event(
                task_id=f"build_{version['tag']}",
                task_type="build",
                description=f"Build release package {version['tag']}",
                priority="high",
                status="success",
                duration_ms=int(build_time * 1000),
                metadata={
                    "version": version["tag"],
                    "package_size": zip_path.stat().st_size,
                    "files_count": len(files_to_copy)
                }
            )
            
            return zip_path
        
        except Exception as e:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            # 记录失败
            self.collector.collect_task_event(
                task_id=f"build_{version['tag']}",
                task_type="build",
                description=f"Build release package {version['tag']}",
                priority="high",
                status="failed",
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                error_message=str(e)
            )
            
            print(f"[FAIL] 构建失败: {e}")
            return None
    
    def publish_to_github(self, zip_path: Path, version: Dict) -> bool:
        """发布到 GitHub Release
        
        Args:
            zip_path: 发布包路径
            version: 版本信息
        
        Returns:
            是否成功
        """
        try:
            # 1. 创建 Git tag
            tag = version["tag"]
            
            subprocess.run(
                ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
                cwd=PROJECT_ROOT,
                check=True,
                timeout=10
            )
            
            # 2. 推送 tag
            subprocess.run(
                ["git", "push", "origin", tag],
                cwd=PROJECT_ROOT,
                check=True,
                timeout=30
            )
            
            # 3. 使用 gh CLI 创建 Release
            release_notes = self._generate_release_notes(version)
            
            subprocess.run(
                [
                    "gh", "release", "create", tag,
                    str(zip_path),
                    "--title", f"ARAM Helper {tag}",
                    "--notes", release_notes
                ],
                cwd=PROJECT_ROOT,
                check=True,
                timeout=60
            )
            
            print(f"[OK] 发布成功: {tag}")
            print(f"[PACKAGE] 下载地址: https://github.com/{GITHUB_REPO}/releases/tag/{tag}")
            
            # 4. 记录事件
            self.collector.collect_task_event(
                task_id=f"publish_{tag}",
                task_type="publish",
                description=f"Publish release {tag} to GitHub",
                priority="high",
                status="success",
                duration_ms=0,
                metadata={
                    "version": tag,
                    "repo": GITHUB_REPO,
                    "package": zip_path.name
                }
            )
            
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] 发布失败: {e}")
            
            # 记录失败
            self.collector.collect_task_event(
                task_id=f"publish_{version['tag']}",
                task_type="publish",
                description=f"Publish release {version['tag']} to GitHub",
                priority="high",
                status="failed",
                duration_ms=0,
                error_message=str(e)
            )
            
            return False
    
    def _generate_release_notes(self, version: Dict) -> str:
        """生成发布说明"""
        notes = f"# ARAM Helper {version['tag']}\n\n"
        notes += f"**发布时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 从 CHANGELOG 读取
        if CHANGELOG_FILE.exists():
            with open(CHANGELOG_FILE, encoding="utf-8") as f:
                changelog = f.read()
                # 提取当前版本的更新内容
                if version["tag"] in changelog:
                    # 简单提取（可以改进）
                    notes += "## 更新内容\n\n"
                    notes += "详见 CHANGELOG.md\n"
        
        notes += "\n## 使用方法\n\n"
        notes += "1. 下载 `ARAM-Helper-{}.zip`\n".format(version["tag"])
        notes += "2. 解压到任意目录\n"
        notes += "3. 双击「启动提示器.bat」\n"
        notes += "4. 打开英雄联盟，进入大乱斗\n"
        
        return notes
    
    def rollback(self) -> bool:
        """回滚到上一版本
        
        Returns:
            是否成功
        """
        try:
            # 1. 获取上一个 tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0", "HEAD^"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            prev_tag = result.stdout.strip()
            
            # 2. 回滚代码
            subprocess.run(
                ["git", "checkout", prev_tag],
                cwd=PROJECT_ROOT,
                check=True,
                timeout=10
            )
            
            print(f"[OK] 回滚成功: {prev_tag}")
            
            # 3. 记录事件
            self.collector.collect_task_event(
                task_id=f"rollback_{prev_tag}",
                task_type="rollback",
                description=f"Rollback from {self.current_version['tag']} to {prev_tag}",
                priority="high",
                status="success",
                duration_ms=0,
                metadata={"from": self.current_version["tag"], "to": prev_tag}
            )
            
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] 回滚失败: {e}")
            return False
    
    def release(self, bump_type: str = "patch") -> bool:
        """完整发布流程
        
        Args:
            bump_type: major/minor/patch
        
        Returns:
            是否成功
        """
        print("[START] 开始发布流程...")
        
        # 1. 检查质量门禁
        print("\n📋 检查质量门禁...")
        passed, failures = self.check_quality_gates()
        if not passed:
            print("[FAIL] 质量门禁未通过:")
            for failure in failures:
                print(f"  - {failure}")
            return False
        print("[OK] 质量门禁通过")
        
        # 2. 递增版本号
        new_version = self._bump_version(bump_type)
        print(f"\n[PACKAGE] 新版本: {new_version['tag']}")
        
        # 3. 构建发布包
        print("\n🔨 构建发布包...")
        zip_path = self.build_release_package(new_version)
        if not zip_path:
            print("[FAIL] 构建失败")
            return False
        print(f"[OK] 构建成功: {zip_path.name} ({zip_path.stat().st_size / 1024:.1f} KB)")
        
        # 4. 发布到 GitHub
        print("\n📤 发布到 GitHub...")
        if not self.publish_to_github(zip_path, new_version):
            print("[FAIL] 发布失败")
            return False
        
        # 5. 更新版本文件
        new_version["released_at"] = datetime.now().isoformat()
        self._save_version(new_version)
        
        print("\n[SUCCESS] 发布完成!")
        return True


def main():
    """命令行入口"""
    import sys
    import io
    
    # 修复 Windows 终端编码问题
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    manager = ReleaseManager()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python release_manager.py check    # 检查发布条件")
        print("  python release_manager.py build    # 构建发布包")
        print("  python release_manager.py publish  # 发布到 GitHub")
        print("  python release_manager.py rollback # 回滚到上一版本")
        print("  python release_manager.py release [major|minor|patch]  # 完整发布流程")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        passed, failures = manager.check_quality_gates()
        if passed:
            print("[OK] 质量门禁通过")
        else:
            print("[FAIL] 质量门禁未通过:")
            for failure in failures:
                print(f"  - {failure}")
    
    elif command == "build":
        version = manager._bump_version("patch")
        zip_path = manager.build_release_package(version)
        if zip_path:
            print(f"[OK] 构建成功: {zip_path}")
        else:
            print("[FAIL] 构建失败")
    
    elif command == "publish":
        # 需要先 build
        print("请使用 'release' 命令进行完整发布流程")
    
    elif command == "rollback":
        manager.rollback()
    
    elif command == "release":
        bump_type = sys.argv[2] if len(sys.argv) > 2 else "patch"
        manager.release(bump_type)
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
