"""
Docker Skill - 容器管理工具
支持：镜像构建、容器运行、日志查看、资源监控
"""
import sys
import json
import subprocess
import argparse
from typing import Optional


def run_cmd(cmd: list, timeout: int = 60) -> dict:
    """执行 docker 命令，返回结果字典"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"超时（{timeout}s）"}
    except FileNotFoundError:
        return {"ok": False, "error": "Docker 未安装或不在 PATH 中"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_containers(all_containers: bool = False) -> None:
    """列出容器"""
    cmd = ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"]
    if all_containers:
        cmd.append("-a")
    result = run_cmd(cmd)
    if not result["ok"]:
        print(f"❌ {result.get('error', result['stderr'])}")
        return
    if not result["stdout"]:
        print("（无容器）")
        return
    print("ID\t\t名称\t\t状态\t\t镜像")
    print(result["stdout"])


def list_images() -> None:
    """列出镜像"""
    cmd = ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}"]
    result = run_cmd(cmd)
    if not result["ok"]:
        print(f"❌ {result.get('error', result['stderr'])}")
        return
    if not result["stdout"]:
        print("（无镜像）")
        return
    print("镜像\t\t\tID\t\t大小")
    print(result["stdout"])


def build_image(path: str, tag: str, timeout: int) -> None:
    """构建镜像"""
    cmd = ["docker", "build", "-t", tag, path]
    print(f"🔨 构建镜像: {tag} (from {path})")
    result = run_cmd(cmd, timeout=timeout)
    if result["ok"]:
        print(f"✅ 构建成功: {tag}")
    else:
        print(f"❌ 构建失败: {result.get('error', result['stderr'])}")


def run_container(image: str, name: Optional[str], detach: bool, ports: list, env: list, cmd_args: list) -> None:
    """运行容器"""
    cmd = ["docker", "run"]
    if detach:
        cmd.append("-d")
    if name:
        cmd.extend(["--name", name])
    for p in ports:
        cmd.extend(["-p", p])
    for e in env:
        cmd.extend(["-e", e])
    cmd.append(image)
    cmd.extend(cmd_args)

    result = run_cmd(cmd)
    if result["ok"]:
        container_id = result["stdout"][:12] if result["stdout"] else "?"
        print(f"✅ 容器已启动: {container_id}")
    else:
        print(f"❌ 启动失败: {result.get('error', result['stderr'])}")


def stop_container(container: str) -> None:
    """停止容器"""
    result = run_cmd(["docker", "stop", container])
    if result["ok"]:
        print(f"✅ 已停止: {container}")
    else:
        print(f"❌ 停止失败: {result.get('error', result['stderr'])}")


def remove_container(container: str, force: bool) -> None:
    """删除容器"""
    cmd = ["docker", "rm"]
    if force:
        cmd.append("-f")
    cmd.append(container)
    result = run_cmd(cmd)
    if result["ok"]:
        print(f"✅ 已删除: {container}")
    else:
        print(f"❌ 删除失败: {result.get('error', result['stderr'])}")


def logs(container: str, tail: int, follow: bool) -> None:
    """查看日志"""
    cmd = ["docker", "logs"]
    if tail:
        cmd.extend(["--tail", str(tail)])
    if follow:
        cmd.append("-f")
    cmd.append(container)

    if follow:
        # 实时日志，直接流式输出
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n（已停止）")
    else:
        result = run_cmd(cmd)
        if result["ok"]:
            print(result["stdout"])
        else:
            print(f"❌ {result.get('error', result['stderr'])}")


def stats(container: Optional[str]) -> None:
    """资源监控"""
    cmd = ["docker", "stats", "--no-stream", "--format", "{{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"]
    if container:
        cmd.append(container)
    result = run_cmd(cmd)
    if result["ok"]:
        print("容器\t\tCPU\t\t内存")
        print(result["stdout"])
    else:
        print(f"❌ {result.get('error', result['stderr'])}")


def main():
    parser = argparse.ArgumentParser(description="Docker 管理工具")
    sub = parser.add_subparsers(dest="cmd")

    # ps
    ps = sub.add_parser("ps", help="列出容器")
    ps.add_argument("-a", "--all", action="store_true", default=False, help="包含已停止的容器")

    # images
    sub.add_parser("images", help="列出镜像")

    # build
    build = sub.add_parser("build", help="构建镜像")
    build.add_argument("path", help="Dockerfile 路径")
    build.add_argument("-t", "--tag", required=True, help="镜像标签")
    build.add_argument("--timeout", type=int, default=300, help="超时（秒）")

    # run
    run = sub.add_parser("run", help="运行容器")
    run.add_argument("image", help="镜像名称")
    run.add_argument("--name", help="容器名称")
    run.add_argument("-d", "--detach", action="store_true", help="后台运行")
    run.add_argument("-p", "--port", action="append", default=[], help="端口映射（如 8080:80）")
    run.add_argument("-e", "--env", action="append", default=[], help="环境变量（如 KEY=VALUE）")
    run.add_argument("args", nargs="*", help="容器启动参数")

    # stop
    stop = sub.add_parser("stop", help="停止容器")
    stop.add_argument("container", help="容器 ID 或名称")

    # rm
    rm = sub.add_parser("rm", help="删除容器")
    rm.add_argument("container", help="容器 ID 或名称")
    rm.add_argument("-f", "--force", action="store_true", help="强制删除")

    # logs
    log = sub.add_parser("logs", help="查看日志")
    log.add_argument("container", help="容器 ID 或名称")
    log.add_argument("--tail", type=int, default=100, help="显示最后 N 行")
    log.add_argument("-f", "--follow", action="store_true", help="实时跟踪")

    # stats
    stat = sub.add_parser("stats", help="资源监控")
    stat.add_argument("container", nargs="?", help="容器 ID 或名称（留空显示全部）")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    if args.cmd == "ps":
        list_containers(args.all)
    elif args.cmd == "images":
        list_images()
    elif args.cmd == "build":
        build_image(args.path, args.tag, args.timeout)
    elif args.cmd == "run":
        run_container(args.image, args.name, args.detach, args.port, args.env, args.args)
    elif args.cmd == "stop":
        stop_container(args.container)
    elif args.cmd == "rm":
        remove_container(args.container, args.force)
    elif args.cmd == "logs":
        logs(args.container, args.tail, args.follow)
    elif args.cmd == "stats":
        stats(args.container)


if __name__ == "__main__":
    main()
