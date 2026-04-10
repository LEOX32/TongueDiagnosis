import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from application.net.model.resnet_improved import ImprovedResNetDeep

class MultiOutputTongueDataset(Dataset):
    def __init__(self, df, img_dir, transform=None):
        self.df = df
        self.img_dir = img_dir
        self.transform = transform

        self.tongue_color_map = {'淡白舌': 0, '淡红舌': 1, '红舌': 2, '绛舌': 3, '青紫舌': 4}
        self.coating_color_map = {'白苔': 0, '灰黑苔': 1}
        self.thickness_map = {'薄': 0, '厚': 1}
        self.greasy_map = {'腻苔': 0, '腐苔': 1}

        self.valid_indices = []
        for idx in range(len(self.df)):
            row = self.df.iloc[idx]
            img_name = row['SID'] + '.jpg'
            img_path = os.path.join(self.img_dir, img_name)
            if os.path.exists(img_path):
                self.valid_indices.append(idx)

    def __len__(self):
        return len(self.valid_indices)

    def __getitem__(self, idx):
        real_idx = self.valid_indices[idx]
        row = self.df.iloc[real_idx]
        img_name = row['SID'] + '.jpg'
        img_path = os.path.join(self.img_dir, img_name)

        try:
            image = Image.open(img_path).convert('RGB')
        except:
            image = Image.new('RGB', (224, 224), (128, 128, 128))

        if self.transform:
            image = self.transform(image)

        tongue_color = self.tongue_color_map.get(row['舌色'], 0)
        coating_color = self.coating_color_map.get(row['舌苔颜色'], 0)
        thickness = self.thickness_map.get(row['舌苔厚度'], 0)
        greasy = self.greasy_map.get(row['腻腐程度'], 0)

        labels = torch.tensor([tongue_color, coating_color, thickness, greasy], dtype=torch.long)

        return image, labels

class ImprovedResNet50MultiOutput(nn.Module):
    def __init__(self, num_classes_list=[5, 2, 2, 2]):
        super().__init__()
        self.backbone = ImprovedResNetDeep(block_num=[3, 4, 6, 3], num_classes=64, use_attention=True, use_multi_scale=True)

        self.fc_tongue = nn.Linear(2048, num_classes_list[0])
        self.fc_coating = nn.Linear(2048, num_classes_list[1])
        self.fc_thickness = nn.Linear(2048, num_classes_list[2])
        self.fc_greasy = nn.Linear(2048, num_classes_list[3])

    def forward(self, x):
        x = self.backbone.conv1(x)
        x = self.backbone.bn1(x)
        x = torch.relu(x)
        x = self.backbone.maxpool(x)

        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)

        x = self.backbone.avgpool(x)
        x = x.flatten(1)

        tongue = self.fc_tongue(x)
        coating = self.fc_coating(x)
        thickness = self.fc_thickness(x)
        greasy = self.fc_greasy(x)

        return tongue, coating, thickness, greasy

def train_one_epoch(model, train_loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = [0, 0, 0, 0]
    total = 0

    for batch_idx, (images, labels) in enumerate(train_loader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        tongue_out, coating_out, thickness_out, greasy_out = model(images)

        loss = criterion(tongue_out, labels[:, 0])
        loss += criterion(coating_out, labels[:, 1])
        loss += criterion(thickness_out, labels[:, 2])
        loss += criterion(greasy_out, labels[:, 3])
        loss = loss / 4

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        _, tongue_pred = tongue_out.max(1)
        _, coating_pred = coating_out.max(1)
        _, thickness_pred = thickness_out.max(1)
        _, greasy_pred = greasy_out.max(1)

        total += labels.size(0)
        correct[0] += tongue_pred.eq(labels[:, 0]).sum().item()
        correct[1] += coating_pred.eq(labels[:, 1]).sum().item()
        correct[2] += thickness_pred.eq(labels[:, 2]).sum().item()
        correct[3] += greasy_pred.eq(labels[:, 3]).sum().item()

        if (batch_idx + 1) % 20 == 0:
            print(f'  Batch {batch_idx+1}/{len(train_loader)}, Loss: {loss.item():.4f}')

    epoch_loss = running_loss / len(train_loader)
    epoch_acc = [100. * c / total for c in correct]
    return epoch_loss, epoch_acc

def validate(model, val_loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = [0, 0, 0, 0]
    total = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            tongue_out, coating_out, thickness_out, greasy_out = model(images)

            loss = criterion(tongue_out, labels[:, 0])
            loss += criterion(coating_out, labels[:, 1])
            loss += criterion(thickness_out, labels[:, 2])
            loss += criterion(greasy_out, labels[:, 3])
            loss = loss / 4

            running_loss += loss.item()

            _, tongue_pred = tongue_out.max(1)
            _, coating_pred = coating_out.max(1)
            _, thickness_pred = thickness_out.max(1)
            _, greasy_pred = greasy_out.max(1)

            total += labels.size(0)
            correct[0] += tongue_pred.eq(labels[:, 0]).sum().item()
            correct[1] += coating_pred.eq(labels[:, 1]).sum().item()
            correct[2] += thickness_pred.eq(labels[:, 2]).sum().item()
            correct[3] += greasy_pred.eq(labels[:, 3]).sum().item()

    epoch_loss = running_loss / len(val_loader)
    epoch_acc = [100. * c / total for c in correct]
    return epoch_loss, epoch_acc

def main():
    print("=" * 60)
    print("优化改进ResNet50综合模型训练 - 动态尺度+随机缩放增强")
    print("=" * 60)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")

    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

    # 训练增强：随机缩放增强 + 随机裁剪
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),  # 先放大到256
        transforms.RandomCrop((224, 224)),  # 随机裁剪到224
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_csv = os.path.join(base_dir, 'dataset', 'train_labels.csv')
    img_dir = os.path.join(base_dir, 'dataset', 'train')

    print(f"\n数据来源: {train_csv}")
    print(f"图片目录: {img_dir}")

    full_df = pd.read_csv(train_csv)
    print(f"原始数据量: {len(full_df)}")

    indices = np.arange(len(full_df))
    np.random.seed(42)
    np.random.shuffle(indices)
    split_idx = int(len(indices) * 0.75)
    train_indices = indices[:split_idx]
    val_indices = indices[split_idx:]

    train_df = full_df.iloc[train_indices].reset_index(drop=True)
    val_df = full_df.iloc[val_indices].reset_index(drop=True)

    train_dataset = MultiOutputTongueDataset(train_df, img_dir, transform=train_transform)
    val_dataset = MultiOutputTongueDataset(val_df, img_dir, transform=val_transform)

    print(f"\n有效训练样本数: {len(train_dataset)}")
    print(f"有效验证样本数: {len(val_dataset)}")
    print(f"预测特征: 舌色(5类), 舌苔颜色(2类), 舌苔厚度(2类), 腻腐程度(2类)")
    print(f"数据增强: 随机缩放(256->224裁剪), 水平翻转, 旋转, 颜色抖动")

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0, pin_memory=True)

    model = ImprovedResNet50MultiOutput(num_classes_list=[5, 2, 2, 2])
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)

    num_epochs = 50
    best_val_acc = 0.0
    save_dir = os.path.join(base_dir, 'checkpoints', 'improved_resnet', 'full_model')

    os.makedirs(save_dir, exist_ok=True)
    print(f"\n模型保存目录: {save_dir}")

    print("\n" + "=" * 60)
    print("开始训练")
    print("=" * 60)

    for epoch in range(num_epochs):
        print(f'\nEpoch {epoch+1}/{num_epochs}')
        print('-' * 40)

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step()

        print(f'训练 Loss: {train_loss:.4f}')
        print(f'舌色: {train_acc[0]:.2f}%, 舌苔: {train_acc[1]:.2f}%, 厚度: {train_acc[2]:.2f}%, 腻腐: {train_acc[3]:.2f}%')
        print(f'验证 Loss: {val_loss:.4f}')
        print(f'舌色: {val_acc[0]:.2f}%, 舌苔: {val_acc[1]:.2f}%, 厚度: {val_acc[2]:.2f}%, 腻腐: {val_acc[3]:.2f}%')

        avg_acc = sum(val_acc) / 4
        if avg_acc > best_val_acc:
            best_val_acc = avg_acc
            save_path = os.path.join(save_dir, 'best_model.pth')
            torch.save(model.state_dict(), save_path)
            print(f'已保存最佳模型到: {save_path}')

        if (epoch + 1) % 5 == 0:
            checkpoint_path = os.path.join(save_dir, f'epoch_{epoch+1}.pth')
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
            }, checkpoint_path)
            print(f'已保存检查点: {checkpoint_path}')

    print("\n" + "=" * 60)
    print(f"训练完成! 最佳验证准确率: {best_val_acc:.2f}%")
    print("=" * 60)

if __name__ == '__main__':
    main()
