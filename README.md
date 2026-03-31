# 实时行情监控工具

加密货币实时行情监控系统，支持持仓监控、委托提醒、信号检测。

## 功能

- **持仓监控**: 实时监控持仓跌幅，超过阈值时自动通知
- **委托提醒**: 委托成交时自动发送通知
- **信号检测**: 金叉死叉检测、高点低点抬高形态识别
- **多渠道推送**: 支持企业微信、钉钉、QQ、Gmail、Telegram

## 快速开始

### 1. 安装依赖

```bash
cd /Users/mac/行情抓取
pip install -r requirements.txt
```

### 2. 配置 API

编辑 `.env` 文件，填入你的 OKX API 凭证：

```env
OKX_API_KEY=你的API_KEY
OKX_SECRET=你的SECRET_KEY
OKX_PASSPHRASE=你的密码
```

### 3. 配置通知渠道

至少配置一个通知渠道：

```env
# 企业微信机器人（推荐）
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 钉钉机器人
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx

# Gmail
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GMAIL_TO=recipient@example.com
```

### 4. 启动监控

```bash
python main.py
```

## 目录结构

```
行情抓取/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── .env                 # 环境变量（敏感信息）
├── requirements.txt     # 依赖列表
│
├── core/                # 核心模块
│   ├── okx_client.py    # OKX API 客户端
│   ├── indicators.py    # 技术指标计算
│   └── pattern_detector.py  # 形态识别
│
├── monitors/            # 监控模块
│   ├── position_monitor.py  # 持仓监控
│   ├── order_monitor.py     # 委托监控
│   └── signal_monitor.py    # 信号监控
│
├── notifiers/           # 通知模块
│   ├── wechat.py        # 企业微信
│   ├── dingtalk.py      # 钉钉
│   ├── qmsg.py          # QQ
│   ├── gmail.py         # Gmail
│   └── manager.py       # 通知管理器
│
├── data/                # 数据模块
│   └── state.py         # 状态管理
│
└── logs/                # 日志目录
    └── monitor.log
```

## 配置说明

### 监控参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| POSITION_LOSS_THRESHOLD | 0.01 | 持仓跌幅告警阈值（1%）|
| POSITION_CHECK_INTERVAL | 30 | 持仓检查间隔（秒）|
| ORDER_CHECK_INTERVAL | 10 | 委托检查间隔（秒）|
| SIGNAL_CHECK_INTERVAL | 300 | 信号检查间隔（秒）|
| EMA_FAST_PERIOD | 12 | EMA 快线周期 |
| EMA_SLOW_PERIOD | 26 | EMA 慢线周期 |

### 通知渠道配置

#### 企业微信机器人

1. 在企业微信中创建群聊
2. 群设置 → 添加机器人
3. 复制 Webhook URL

#### 钉钉机器人

1. 在钉钉中创建群聊
2. 群设置 → 智能群助手 → 添加机器人
3. 选择"自定义"，安全设置填入关键词"行情"
4. 复制 Webhook URL

#### Gmail

1. 开启 Gmail 两步验证
2. 访问 https://myaccount.google.com/apppasswords
3. 生成应用专用密码
4. 配置邮箱和密码

## 运行示例

```bash
# 前台运行
python main.py

# 后台运行（Mac/Linux）
nohup python main.py &

# Mac 防睡眠运行
caffeinate -s python main.py
```

## 注意事项

1. **API 权限**: 建议只勾选"读取"和"交易"，不勾选"提现"
2. **IP 白名单**: 确保你的 IP 已添加到 OKX 白名单
3. **安全**: 不要将 `.env` 文件提交到 Git
4. **频率限制**: 监控间隔不要太短，避免触发 API 限流
