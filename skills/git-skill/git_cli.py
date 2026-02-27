#!/usr/bin/env python3
"""
Git CLI - Git 操作封装

使用示例：
    # 提交
    python git_cli.py commit --message "feat: 新功能"
    
    # 推送
    python git_cli.py push
    
    # 创建分支
    python git_cli.py branch --name feature/new-feature
    
    # 查看状态
    python git_cli.py status
"""

import subprocess
import argparse


def run_git(args_list):
    """运行 git 命令"""
    result = subprocess.run(
        ["git"] + args_list,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout, result.stderr, result.returncode


def git_status(args):
    """查看状态"""
    stdout, stderr, code = run_git(["status"])
    print(stdout)
    if stderr:
        print(stderr)


def git_add(args):
    """添加文件"""
    files = args.files if args.files else ["."]
    stdout, stderr, code = run_git(["add"] + files)
    if code == 0:
        print(f"✅ 已添加: {', '.join(files)}")
    else:
        print(f"❌ 添加失败: {stderr}")


def git_commit(args):
    """提交"""
    stdout, stderr, code = run_git(["commit", "-m", args.message])
    if code == 0:
        print(f"✅ 已提交: {args.message}")
    else:
        print(f"❌ 提交失败: {stderr}")


def git_push(args):
    """推送"""
    cmd = ["push"]
    if args.remote:
        cmd.append(args.remote)
    if args.branch:
        cmd.append(args.branch)
    
    stdout, stderr, code = run_git(cmd)
    if code == 0:
        print(f"✅ 已推送")
        print(stdout)
    else:
        print(f"❌ 推送失败: {stderr}")


def git_pull(args):
    """拉取"""
    stdout, stderr, code = run_git(["pull"])
    if code == 0:
        print(f"✅ 已拉取")
        print(stdout)
    else:
        print(f"❌ 拉取失败: {stderr}")


def git_branch(args):
    """分支管理"""
    if args.name:
        # 创建分支
        stdout, stderr, code = run_git(["checkout", "-b", args.name])
        if code == 0:
            print(f"✅ 已创建并切换到分支: {args.name}")
        else:
            print(f"❌ 创建分支失败: {stderr}")
    else:
        # 列出分支
        stdout, stderr, code = run_git(["branch"])
        print(stdout)


def git_log(args):
    """查看日志"""
    cmd = ["log", f"--oneline", f"-{args.limit}"]
    stdout, stderr, code = run_git(cmd)
    print(stdout)


def git_diff(args):
    """查看差异"""
    stdout, stderr, code = run_git(["diff"])
    print(stdout)


def main():
    parser = argparse.ArgumentParser(description="Git CLI")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # status
    status_parser = subparsers.add_parser("status", help="查看状态")
    
    # add
    add_parser = subparsers.add_parser("add", help="添加文件")
    add_parser.add_argument("files", nargs="*", help="文件列表")
    
    # commit
    commit_parser = subparsers.add_parser("commit", help="提交")
    commit_parser.add_argument("--message", "-m", required=True, help="提交信息")
    
    # push
    push_parser = subparsers.add_parser("push", help="推送")
    push_parser.add_argument("--remote", help="远程仓库")
    push_parser.add_argument("--branch", help="分支")
    
    # pull
    pull_parser = subparsers.add_parser("pull", help="拉取")
    
    # branch
    branch_parser = subparsers.add_parser("branch", help="分支管理")
    branch_parser.add_argument("--name", help="分支名称（创建新分支）")
    
    # log
    log_parser = subparsers.add_parser("log", help="查看日志")
    log_parser.add_argument("--limit", type=int, default=10, help="最大返回数量")
    
    # diff
    diff_parser = subparsers.add_parser("diff", help="查看差异")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "status": git_status,
        "add": git_add,
        "commit": git_commit,
        "push": git_push,
        "pull": git_pull,
        "branch": git_branch,
        "log": git_log,
        "diff": git_diff
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
