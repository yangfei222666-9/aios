"""
MNIST v1 训练脚本
使用 PyTorch CNN 在 MNIST 数据集上训练手写数字分类模型
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "batch_size": 128,
    "epochs": 10,
    "learning_rate": 0.001,
    "num_workers": 2,
    "seed": 42,
}

# 路径
WORKSPACE = r"C:\Users\A\.openclaw\workspace"
MODEL_PATH = os.path.join(WORKSPACE, "models", "mnist_v1.pth")
LOG_PATH = os.path.join(WORKSPACE, "experiments", "mnist", "train.log")
REPORT_PATH = os.path.join(WORKSPACE, "experiments", "mnist", "mnist_v1_report.md")
DATA_DIR = os.path.join(WORKSPACE, "data", "mnist")

# ============================================================
# 日志设置
# ============================================================
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logger = logging.getLogger("mnist_trainer")
logger.setLevel(logging.INFO)
# 文件 handler
fh = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(fh)
# 控制台 handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(ch)


# ============================================================
# CNN 模型定义
# ============================================================
class MNISTNet(nn.Module):
    """
    简单 CNN：
      Conv2d(1,32,3) -> ReLU -> Conv2d(32,64,3) -> ReLU -> MaxPool
      -> Conv2d(64,64,3) -> ReLU -> MaxPool -> Flatten
      -> FC(576,128) -> ReLU -> Dropout -> FC(128,10)
    """
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),   # 28x28 -> 28x28
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # 28x28 -> 28x28
            nn.ReLU(),
            nn.MaxPool2d(2),                               # 28x28 -> 14x14
            nn.Conv2d(64, 64, kernel_size=3, padding=1),  # 14x14 -> 14x14
            nn.ReLU(),
            nn.MaxPool2d(2),                               # 14x14 -> 7x7
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.25),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


def count_parameters(model):
    """统计模型可训练参数量"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# ============================================================
# 训练 & 测试函数
# ============================================================
def train_epoch(model, loader, criterion, optimizer, device):
    """训练一个 epoch，返回平均 loss 和准确率"""
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    for batch_idx, (data, target) in enumerate(loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * data.size(0)
        pred = output.argmax(dim=1)
        correct += pred.eq(target).sum().item()
        total += data.size(0)
    return total_loss / total, correct / total


def evaluate(model, loader, device):
    """在测试集上评估，返回 loss、准确率、混淆矩阵"""
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss, correct, total = 0.0, 0, 0
    # 混淆矩阵 10x10
    confusion = torch.zeros(10, 10, dtype=torch.long)
    with torch.no_grad():
        for data, target in loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            total_loss += loss.item() * data.size(0)
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()
            total += data.size(0)
            for t, p in zip(target.cpu(), pred.cpu()):
                confusion[t.long(), p.long()] += 1
    return total_loss / total, correct / total, confusion


# ============================================================
# 报告生成
# ============================================================
def generate_report(config, history, test_acc, test_loss, confusion, param_count,
                    train_time, device_name, gpu_util_info):
    """生成 Markdown 实验报告"""
    lines = []
    lines.append("# MNIST v1 实验报告")
    lines.append(f"\n> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 数据集信息
    lines.append("## 1. 数据集信息")
    lines.append("| 项目 | 值 |")
    lines.append("|------|-----|")
    lines.append("| 数据集 | MNIST |")
    lines.append("| 训练样本数 | 60,000 |")
    lines.append("| 测试样本数 | 10,000 |")
    lines.append("| 类别数 | 10 (0-9) |")
    lines.append("| 图像尺寸 | 28×28 灰度 |")

    # 模型架构
    lines.append("\n## 2. 模型架构")
    lines.append("```")
    lines.append("Conv2d(1→32, 3×3, pad=1) → ReLU")
    lines.append("Conv2d(32→64, 3×3, pad=1) → ReLU → MaxPool2d(2)")
    lines.append("Conv2d(64→64, 3×3, pad=1) → ReLU → MaxPool2d(2)")
    lines.append("Flatten → Linear(3136→128) → ReLU → Dropout(0.25)")
    lines.append("Linear(128→10)")
    lines.append("```")
    lines.append(f"- 总参数量: **{param_count:,}**")
    lines.append(f"- 卷积层: 3 层")
    lines.append(f"- 全连接层: 2 层")

    # 训练配置
    lines.append("\n## 3. 训练配置")
    lines.append("| 参数 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 学习率 | {config['learning_rate']} |")
    lines.append(f"| Batch Size | {config['batch_size']} |")
    lines.append(f"| Epochs | {config['epochs']} |")
    lines.append(f"| 优化器 | Adam |")
    lines.append(f"| 损失函数 | CrossEntropyLoss |")
    lines.append(f"| 设备 | {device_name} |")

    # 训练曲线
    lines.append("\n## 4. 训练曲线")
    lines.append("| Epoch | Train Loss | Train Acc | Test Loss | Test Acc |")
    lines.append("|-------|-----------|-----------|-----------|----------|")
    for h in history:
        lines.append(f"| {h['epoch']} | {h['train_loss']:.4f} | {h['train_acc']:.2%} | {h['test_loss']:.4f} | {h['test_acc']:.2%} |")

    # 测试结果
    lines.append(f"\n## 5. 测试结果")
    lines.append(f"- **测试准确率: {test_acc:.2%}**")
    lines.append(f"- 测试 Loss: {test_loss:.4f}")
    lines.append("\n### 混淆矩阵")
    lines.append("```")
    header = "     " + "".join(f"{i:>6}" for i in range(10))
    lines.append(header)
    for i in range(10):
        row = f"  {i}  " + "".join(f"{confusion[i][j].item():>6}" for j in range(10))
        lines.append(row)
    lines.append("```")

    # 训练时间和 GPU
    lines.append(f"\n## 6. 训练时间和 GPU 利用率")
    lines.append(f"- 总训练时间: **{train_time:.1f} 秒**")
    lines.append(f"- 平均每 epoch: {train_time / config['epochs']:.1f} 秒")
    lines.append(f"- {gpu_util_info}")

    lines.append(f"\n## 7. 模型保存")
    lines.append(f"- 路径: `models/mnist_v1.pth`")
    lines.append(f"- 格式: PyTorch state_dict")

    return "\n".join(lines)


# ============================================================
# 主训练流程
# ============================================================
def main():
    logger.info("=" * 60)
    logger.info("MNIST v1 训练开始")
    logger.info("=" * 60)

    # 设置随机种子
    torch.manual_seed(CONFIG["seed"])

    # 设备选择
    if torch.cuda.is_available():
        device = torch.device("cuda")
        device_name = torch.cuda.get_device_name(0)
        logger.info(f"使用 GPU: {device_name}")
    else:
        device = torch.device("cpu")
        device_name = "CPU"
        logger.info("CUDA 不可用，使用 CPU 训练")

    # 数据预处理
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),  # MNIST 均值和标准差
    ])

    # 加载数据集
    logger.info("加载 MNIST 数据集...")
    train_dataset = datasets.MNIST(DATA_DIR, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(DATA_DIR, train=False, download=True, transform=transform)
    logger.info(f"训练集: {len(train_dataset)} 样本, 测试集: {len(test_dataset)} 样本")

    train_loader = DataLoader(train_dataset, batch_size=CONFIG["batch_size"],
                              shuffle=True, num_workers=CONFIG["num_workers"], pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=CONFIG["batch_size"],
                             shuffle=False, num_workers=CONFIG["num_workers"], pin_memory=True)

    # 创建模型
    model = MNISTNet().to(device)
    param_count = count_parameters(model)
    logger.info(f"模型参数量: {param_count:,}")

    # 优化器和损失函数
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=CONFIG["learning_rate"])

    # 训练循环
    history = []
    start_time = time.time()

    for epoch in range(1, CONFIG["epochs"] + 1):
        epoch_start = time.time()

        # 训练
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)

        # 测试
        test_loss, test_acc, _ = evaluate(model, test_loader, device)

        epoch_time = time.time() - epoch_start
        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "test_loss": test_loss,
            "test_acc": test_acc,
        })

        logger.info(
            f"Epoch {epoch:>2}/{CONFIG['epochs']} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.2%} | "
            f"Test Loss: {test_loss:.4f} Acc: {test_acc:.2%} | "
            f"Time: {epoch_time:.1f}s"
        )

    total_time = time.time() - start_time
    logger.info(f"训练完成，总耗时: {total_time:.1f}s")

    # 最终评估
    final_test_loss, final_test_acc, confusion = evaluate(model, test_loader, device)
    logger.info(f"最终测试准确率: {final_test_acc:.2%}")

    if final_test_acc > 0.95:
        logger.info("✅ 准确率 > 95%，达标！")
    else:
        logger.warning("⚠️ 准确率未达 95%")

    # 保存模型
    torch.save(model.state_dict(), MODEL_PATH)
    logger.info(f"模型已保存: {MODEL_PATH}")

    # GPU 利用率信息
    if torch.cuda.is_available():
        mem_allocated = torch.cuda.max_memory_allocated(0) / 1024**2
        mem_reserved = torch.cuda.max_memory_reserved(0) / 1024**2
        gpu_util_info = (
            f"GPU 显存使用: 峰值分配 {mem_allocated:.0f} MB / 峰值保留 {mem_reserved:.0f} MB"
        )
    else:
        gpu_util_info = "未使用 GPU"
    logger.info(gpu_util_info)

    # 生成报告
    report = generate_report(
        CONFIG, history, final_test_acc, final_test_loss,
        confusion, param_count, total_time, device_name, gpu_util_info
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"实验报告已保存: {REPORT_PATH}")

    logger.info("=" * 60)
    logger.info("MNIST v1 训练项目完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
