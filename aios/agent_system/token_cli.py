"""
Token Monitor CLI - 命令行工具

快速查询 Token 使用情况。

用法：
    python token_cli.py                    # 查看每日使用量
    python token_cli.py --period weekly    # 查看每周使用量
    python token_cli.py --period monthly   # 查看每月使用量
    python token_cli.py --report           # 生成完整报告
    python token_cli.py --log <model> <input> <output> [--type <type>] [--id <id>]  # 记录使用
"""
import argparse
from token_monitor import monitor, log_usage, check_usage, generate_report


def main():
    parser = argparse.ArgumentParser(description='Token Monitor CLI')
    
    parser.add_argument('--period', choices=['daily', 'weekly', 'monthly'], 
                        default='daily', help='时间周期')
    parser.add_argument('--report', action='store_true', help='生成完整报告')
    parser.add_argument('--log', nargs='+', help='记录使用量: model input_tokens output_tokens')
    parser.add_argument('--type', default='unknown', help='任务类型')
    parser.add_argument('--id', help='任务 ID')
    
    args = parser.parse_args()
    
    if args.log:
        # 记录使用量
        if len(args.log) < 3:
            print("错误: --log 需要至少 3 个参数 (model input_tokens output_tokens)")
            return
        
        model = args.log[0]
        input_tokens = int(args.log[1])
        output_tokens = int(args.log[2])
        
        log_usage(model, input_tokens, output_tokens, args.type, args.id)
        print(f"✅ 已记录: {model} - {input_tokens + output_tokens:,} tokens")
    
    elif args.report:
        # 生成完整报告
        report = generate_report(args.period)
        print(report)
    
    else:
        # 查看使用量
        usage = check_usage(args.period)
        
        print(f"\n{'=' * 62}")
        print(f"Token 使用量 - {args.period.upper()}")
        print(f"{'=' * 62}")
        print(f"总使用量: {usage['total_tokens']:,} tokens")
        print(f"预算上限: {usage['limit']:,} tokens")
        print(f"使用率: {usage['usage_rate']*100:.1f}%")
        print(f"剩余: {usage['remaining']:,} tokens")
        print(f"总成本: ${usage['total_cost']:.2f}")
        print(f"{'=' * 62}\n")


if __name__ == '__main__':
    main()
