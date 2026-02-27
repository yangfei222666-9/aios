#!/usr/bin/env python3
"""
VM Controller v1.0 - 基于 Docker 的轻量 VM 控制器
用 Docker 容器模拟 VM，支持创建/启动/停止/删除/状态查询
"""

import subprocess
import json
import sys
import os
import argparse
from datetime import datetime

# VM 配置文件路径
VM_REGISTRY = os.path.join(os.path.dirname(__file__), "vm_registry.json")

# 默认镜像映射
IMAGE_MAP = {
    "ubuntu": "ubuntu:22.04",
    "ubuntu22": "ubuntu:22.04",
    "ubuntu20": "ubuntu:20.04",
    "debian": "debian:bookworm",
    "alpine": "alpine:latest",
    "python": "python:3.12-slim",
    "node": "node:20-slim",
}


def run_docker(args: list, capture=True) -> tuple[int, str, str]:
    """执行 docker 命令"""
    cmd = ["docker"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 1, "", "Docker 未安装或未启动，请先安装 Docker Desktop"
    except Exception as e:
        return 1, "", str(e)


def load_registry() -> dict:
    """加载 VM 注册表"""
    if os.path.exists(VM_REGISTRY):
        with open(VM_REGISTRY, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_registry(registry: dict):
    """保存 VM 注册表"""
    with open(VM_REGISTRY, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def check_docker() -> bool:
    """检查 Docker 是否可用"""
    code, out, err = run_docker(["info", "--format", "{{.ServerVersion}}"])
    if code != 0:
        print(f"❌ Docker 不可用: {err}")
        return False
    print(f"✅ Docker 已就绪 (版本: {out})")
    return True


def vm_create(name: str, image: str = "ubuntu", cpu: str = "1", memory: str = "512m", ports: str = None):
    """创建 VM（Docker 容器）"""
    registry = load_registry()

    if name in registry:
        print(f"❌ VM '{name}' 已存在")
        return False

    # 解析镜像
    actual_image = IMAGE_MAP.get(image, image)

    print(f"🔧 创建 VM: {name}")
    print(f"   镜像: {actual_image}")
    print(f"   CPU: {cpu} 核, 内存: {memory}")

    # 构建 docker run 参数
    docker_args = [
        "run", "-d",
        "--name", name,
        f"--cpus={cpu}",
        f"--memory={memory}",
        "--restart=unless-stopped",
    ]

    # 端口映射
    if ports:
        for p in ports.split(","):
            docker_args += ["-p", p.strip()]

    # 保持容器运行
    docker_args += [actual_image, "sleep", "infinity"]

    code, out, err = run_docker(docker_args)

    if code != 0:
        # 如果镜像不存在，先拉取
        if "Unable to find image" in err or "pull" in err.lower():
            print(f"   📥 拉取镜像 {actual_image}...")
            pull_code, _, pull_err = run_docker(["pull", actual_image])
            if pull_code != 0:
                print(f"❌ 拉取镜像失败: {pull_err}")
                return False
            # 重试创建
            code, out, err = run_docker(docker_args)

    if code != 0:
        print(f"❌ 创建失败: {err}")
        return False

    # 记录到注册表
    registry[name] = {
        "id": out[:12],
        "image": actual_image,
        "cpu": cpu,
        "memory": memory,
        "ports": ports,
        "created_at": datetime.now().isoformat(),
        "status": "running"
    }
    save_registry(registry)

    print(f"✅ VM '{name}' 创建成功 (ID: {out[:12]})")
    return True


def vm_start(name: str):
    """启动 VM"""
    registry = load_registry()
    if name not in registry:
        print(f"❌ VM '{name}' 不存在")
        return False

    code, out, err = run_docker(["start", name])
    if code != 0:
        print(f"❌ 启动失败: {err}")
        return False

    registry[name]["status"] = "running"
    save_registry(registry)
    print(f"✅ VM '{name}' 已启动")
    return True


def vm_stop(name: str):
    """停止 VM"""
    registry = load_registry()
    if name not in registry:
        print(f"❌ VM '{name}' 不存在")
        return False

    print(f"⏹️  停止 VM '{name}'...")
    code, out, err = run_docker(["stop", name])
    if code != 0:
        print(f"❌ 停止失败: {err}")
        return False

    registry[name]["status"] = "stopped"
    save_registry(registry)
    print(f"✅ VM '{name}' 已停止")
    return True


def vm_delete(name: str, force: bool = False):
    """删除 VM"""
    registry = load_registry()
    if name not in registry:
        print(f"❌ VM '{name}' 不存在")
        return False

    if not force:
        confirm = input(f"⚠️  确认删除 VM '{name}'? (y/N): ")
        if confirm.lower() != "y":
            print("取消删除")
            return False

    # 先停止再删除
    run_docker(["stop", name])
    code, out, err = run_docker(["rm", "-f", name])
    if code != 0:
        print(f"❌ 删除失败: {err}")
        return False

    del registry[name]
    save_registry(registry)
    print(f"✅ VM '{name}' 已删除")
    return True


def vm_status(name: str = None):
    """查看 VM 状态"""
    registry = load_registry()

    if not registry:
        print("📭 没有任何 VM")
        return

    # 获取 Docker 实际状态
    code, out, err = run_docker([
        "ps", "-a",
        "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"
    ])

    docker_status = {}
    if code == 0 and out:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                docker_status[parts[0]] = {
                    "status": parts[1],
                    "ports": parts[2] if len(parts) > 2 else ""
                }

    if name:
        # 查看单个 VM
        if name not in registry:
            print(f"❌ VM '{name}' 不存在")
            return
        vms = {name: registry[name]}
    else:
        vms = registry

    print(f"\n{'VM名称':<20} {'状态':<15} {'镜像':<25} {'CPU':<6} {'内存':<8} {'创建时间'}")
    print("-" * 90)

    for vm_name, info in vms.items():
        # 从 Docker 获取实时状态
        real_status = docker_status.get(vm_name, {}).get("status", info.get("status", "unknown"))

        # 状态图标
        if "Up" in real_status or real_status == "running":
            icon = "🟢"
        elif "Exited" in real_status or real_status == "stopped":
            icon = "🔴"
        else:
            icon = "🟡"

        created = info.get("created_at", "")[:16].replace("T", " ")
        print(f"{icon} {vm_name:<18} {real_status:<15} {info['image']:<25} {info['cpu']:<6} {info['memory']:<8} {created}")

    print()


def vm_exec(name: str, command: str):
    """在 VM 中执行命令"""
    registry = load_registry()
    if name not in registry:
        print(f"❌ VM '{name}' 不存在")
        return False

    print(f"🔧 在 VM '{name}' 中执行: {command}")
    code, out, err = run_docker(["exec", name, "sh", "-c", command])

    if out:
        print(out)
    if err:
        print(f"stderr: {err}", file=sys.stderr)

    return code == 0


def vm_shell(name: str):
    """进入 VM 交互式 Shell"""
    registry = load_registry()
    if name not in registry:
        print(f"❌ VM '{name}' 不存在")
        return False

    print(f"🖥️  进入 VM '{name}' Shell (输入 exit 退出)")
    os.system(f"docker exec -it {name} /bin/bash || docker exec -it {name} /bin/sh")
    return True


def vm_logs(name: str, lines: int = 50):
    """查看 VM 日志"""
    registry = load_registry()
    if name not in registry:
        print(f"❌ VM '{name}' 不存在")
        return False

    code, out, err = run_docker(["logs", "--tail", str(lines), name])
    if out:
        print(out)
    if err:
        print(err)
    return code == 0


def vm_stats():
    """查看所有 VM 资源使用"""
    code, out, err = run_docker([
        "stats", "--no-stream",
        "--format", "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    ])
    if code == 0:
        print(out)
    else:
        print(f"❌ {err}")


def main():
    parser = argparse.ArgumentParser(
        description="VM Controller v1.0 - 基于 Docker 的轻量 VM 控制器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python vm_controller.py check                    # 检查 Docker 状态
  python vm_controller.py create myvm              # 创建 Ubuntu VM
  python vm_controller.py create myvm --image alpine --memory 256m
  python vm_controller.py status                   # 查看所有 VM
  python vm_controller.py start myvm               # 启动 VM
  python vm_controller.py stop myvm                # 停止 VM
  python vm_controller.py exec myvm "ls -la"       # 执行命令
  python vm_controller.py shell myvm               # 进入 Shell
  python vm_controller.py delete myvm              # 删除 VM
  python vm_controller.py stats                    # 资源使用
        """
    )

    subparsers = parser.add_subparsers(dest="command")

    # check
    subparsers.add_parser("check", help="检查 Docker 状态")

    # create
    p_create = subparsers.add_parser("create", help="创建 VM")
    p_create.add_argument("name", help="VM 名称")
    p_create.add_argument("--image", default="ubuntu", help="镜像 (ubuntu/alpine/python/node 或完整镜像名)")
    p_create.add_argument("--cpu", default="1", help="CPU 核数")
    p_create.add_argument("--memory", default="512m", help="内存 (如 512m, 1g)")
    p_create.add_argument("--ports", help="端口映射 (如 8080:80,443:443)")

    # start
    p_start = subparsers.add_parser("start", help="启动 VM")
    p_start.add_argument("name", help="VM 名称")

    # stop
    p_stop = subparsers.add_parser("stop", help="停止 VM")
    p_stop.add_argument("name", help="VM 名称")

    # delete
    p_delete = subparsers.add_parser("delete", help="删除 VM")
    p_delete.add_argument("name", help="VM 名称")
    p_delete.add_argument("-f", "--force", action="store_true", help="强制删除（不确认）")

    # status
    p_status = subparsers.add_parser("status", help="查看 VM 状态")
    p_status.add_argument("name", nargs="?", help="VM 名称（不填则查看所有）")

    # exec
    p_exec = subparsers.add_parser("exec", help="在 VM 中执行命令")
    p_exec.add_argument("name", help="VM 名称")
    p_exec.add_argument("cmd", help="要执行的命令")

    # shell
    p_shell = subparsers.add_parser("shell", help="进入 VM Shell")
    p_shell.add_argument("name", help="VM 名称")

    # logs
    p_logs = subparsers.add_parser("logs", help="查看 VM 日志")
    p_logs.add_argument("name", help="VM 名称")
    p_logs.add_argument("--lines", type=int, default=50, help="显示行数")

    # stats
    subparsers.add_parser("stats", help="查看资源使用")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "check":
        check_docker()
    elif args.command == "create":
        vm_create(args.name, args.image, args.cpu, args.memory, args.ports)
    elif args.command == "start":
        vm_start(args.name)
    elif args.command == "stop":
        vm_stop(args.name)
    elif args.command == "delete":
        vm_delete(args.name, args.force)
    elif args.command == "status":
        vm_status(args.name)
    elif args.command == "exec":
        vm_exec(args.name, args.cmd)
    elif args.command == "shell":
        vm_shell(args.name)
    elif args.command == "logs":
        vm_logs(args.name, args.lines)
    elif args.command == "stats":
        vm_stats()


if __name__ == "__main__":
    main()
