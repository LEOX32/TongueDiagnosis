import torch
import torch.nn as nn
from torchvision import transforms
import concurrent.futures


class BottleNeckDeep(nn.Module):

    def __init__(self, in_channels: int, out_channels: int, stride: int = 1, momentum: int = 0.1,
                 if_downsample: int = False, se_block=None):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=1, stride=1, bias=False)
        self.bn1 = nn.BatchNorm2d(num_features=out_channels, momentum=momentum)
        self.conv2 = nn.Conv2d(in_channels=out_channels, out_channels=out_channels, kernel_size=3, stride=stride,
                               padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(num_features=out_channels, momentum=momentum)
        self.conv3 = nn.Conv2d(in_channels=out_channels, out_channels=out_channels * 4, kernel_size=1, stride=1,
                               bias=False)
        self.bn3 = nn.BatchNorm2d(num_features=out_channels * 4, momentum=momentum)

        if if_downsample:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_channels=in_channels, out_channels=out_channels * 4, kernel_size=1, stride=stride,
                          bias=False),
                nn.BatchNorm2d(num_features=out_channels * 4)
            )
        else:
            self.downsample = None

        self.seNet = None
        if se_block is not None:
            self.seNet = se_block(out_channels * 4)

    def forward(self, x):
        y = self.conv1(x)
        y = self.bn1(y)
        y = torch.relu(y)
        y = self.conv2(y)
        y = self.bn2(y)
        y = torch.relu(y)
        y = self.conv3(y)
        y = self.bn3(y)
        if self.seNet is not None:
            y = torch.relu(y)
            y = self.seNet(y)
        if self.downsample:
            x = self.downsample(x)
        y += x
        y = torch.relu(y)
        return y


class ResNetDeep(nn.Module):

    def __init__(self, block_num: list, num_classes=2, se_block=None):
        super().__init__()

        self.conv1 = nn.Conv2d(in_channels=3, out_channels=64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(num_features=64, momentum=0.1)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(in_channels=64, out_channels=64, blocks=block_num[0], stride=1,
                                       se_block=se_block)
        self.layer2 = self._make_layer(in_channels=256, out_channels=128, blocks=block_num[1], stride=2,
                                       se_block=se_block)
        self.layer3 = self._make_layer(in_channels=512, out_channels=256, blocks=block_num[1], stride=2,
                                       se_block=se_block)
        self.layer4 = self._make_layer(in_channels=1024, out_channels=512, blocks=block_num[1], stride=2,
                                       se_block=se_block)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(2048, num_classes)

    def _make_layer(self, in_channels, out_channels, blocks, stride=1, se_block=None):
        layers = []
        layers.append(BottleNeckDeep(in_channels, out_channels, stride=stride, if_downsample=True, se_block=se_block))
        for _ in range(1, blocks):
            layers.append(BottleNeckDeep(out_channels * 4, out_channels, se_block=se_block))
        return nn.Sequential(*layers)

    def forward(self, x: torch.tensor):
        x = self.conv1(x)
        x = self.bn1(x)
        x = torch.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.flatten(1)
        x = self.fc(x)

        return x


class SeNet(nn.Module):
    def __init__(self, in_channels: int, r: int = 16):

        super().__init__()
        self.AvagePool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc1 = nn.Linear(in_channels, in_channels // r)
        self.fc2 = nn.Linear(in_channels // r, in_channels)

    def forward(self, x: torch.Tensor):
        y = self.AvagePool(x)
        y = y.view(y.size(0), -1)
        y = torch.relu(self.fc1(y))
        y = torch.sigmoid(self.fc2(y))
        y = y.view(y.size(0), y.size(1), 1, 1)
        return x * y


def ResNet50(num_classes=2, if_se=False):
    if if_se:
        return ResNetDeep(block_num=[3, 4, 6, 3], num_classes=num_classes, se_block=SeNet)
    return ResNetDeep(block_num=[3, 4, 6, 3], num_classes=num_classes)


class ResNetPredictor:
    def __init__(self, path: list, device='cpu', tasks: list = [5, 3, 2, 2], use_fp16=False):
        self.device = device
        self.use_fp16 = use_fp16 and device.type == 'cuda'
        self.nets = []
        self.transform = transforms.Compose(
            [transforms.ToTensor(), transforms.Normalize(mean=[0.29, 0.22, 0.23], std=[0.34, 0.27, 0.28])])
        for p in range(len(path)):
            net = ResNet50(tasks[p], True).to(self.device)
            net.load_state_dict(torch.load(path[p], map_location=self.device, weights_only=False))
            if self.use_fp16:
                net.half()
            net.eval()
            self.nets.append(net)

    def predict(self, img, use_parallel=True):
        """预测方法，支持并行计算"""
        if use_parallel and len(self.nets) > 1:
            return self.parallel_predict(img)
        else:
            return self.serial_predict(img)
    
    def serial_predict(self, img):
        """串行预测方法"""
        img = self.transform(img)
        img = img.unsqueeze(0).to(self.device)
        if self.use_fp16:
            img = img.half()

        result = []
        for net in self.nets:
            with torch.no_grad():
                pred = net(img)
                pred = torch.softmax(pred, dim=1)
                pred = torch.argmax(pred, dim=1).cpu().item()
                result.append(pred)
        return result
    
    def parallel_predict(self, img):
        """并行预测方法"""
        img = self.transform(img)
        img = img.unsqueeze(0).to(self.device)
        if self.use_fp16:
            img = img.half()

        result = []
        # 使用线程池并行预测
        max_workers = min(4, len(self.nets))  # 最多4个线程
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有预测任务
            future_to_net = {executor.submit(self._predict_single, net, img): i for i, net in enumerate(self.nets)}
            
            # 收集结果，保持原始顺序
            predictions = [None] * len(self.nets)
            for future in concurrent.futures.as_completed(future_to_net):
                net_idx = future_to_net[future]
                try:
                    pred = future.result()
                    predictions[net_idx] = pred
                except Exception as e:
                    print(f"模型预测失败: {e}")
                    predictions[net_idx] = 0  # 默认值
            
            result = predictions
        
        return result
    
    def _predict_single(self, net, img):
        """单个模型的预测"""
        with torch.no_grad():
            pred = net(img)
            pred = torch.softmax(pred, dim=1)
            pred = torch.argmax(pred, dim=1).cpu().item()
        return pred