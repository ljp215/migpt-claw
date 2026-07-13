# migpt-claw

小米小爱音箱 OpenClaw Channel 插件，让小爱音箱成为你的 🦞龙虾 语音助手。

## 功能特性

- 🎤 **语音对话** - 对小爱音箱说话，🦞 语音回复
- 📦 **流式输出** - 长文本分块播放，降低延迟
- 🎯 **智能分流** - 长内容/代码/多媒体自动引导至其他渠道
- 🔔 **状态提示** - 支持启动播报和收到消息提示音

## 快速开始

### 1. 安装插件

```bash
# 本地安装
openclaw plugins install ./migpt-claw-1.0.0.tgz
```

### 2. 配置账号

编辑 `~/.openclaw/openclaw.json` 配置文件：

**推荐配置（密码 + passToken）**：

```json
{
  "channels": {
    "migpt": {
      "enabled": true,
      "userId": "123456789",
      "password": "your_password",
      "passToken": "your_pass_token",
      "devices": ["客厅音箱"],
      "announceOnStart": true,
      "startupMessage": "您的小龙虾已上线，随时为您服务",
      "acknowledgeOnReceive": true,
      "receiveMessage": "收到，处理中"
    }
  }
}
```

**配置说明**：
- `userId`：小米 ID（数字，在小米账号「个人信息」-「小米 ID」查看）
- `password`：小米账号密码
- `passToken`：登录辅助凭证，避免验证码（推荐配置）
- `devices`：小爱音箱设备名称列表
- `announceOnStart`：启动时是否播报上线文案
- `startupMessage`：上线播报文案
- `acknowledgeOnReceive`：收到消息时是否回复提示
- `receiveMessage`：收到消息回复文案
- `speakerControl`：音箱控制方式（`mina` 或 `miot`，默认 `mina`）
- `ttsCommand`：MIoT TTS 播报动作坐标 `[siid, aiid]`（仅 `miot` 方式生效；不配置时自动探测，见下文）

### 音箱控制方式说明

**`speakerControl`**：指定与小爱音箱通信的控制方式

- **`mina`**（默认）：使用 MiNA API，适用于大多数小爱音箱型号
- **`miot`**：使用 MIoT API，适用于部分需要特殊控制的型号

**已知需要 `miot` 的型号**：
- LX04（小爱音箱 Pro）
- X10A（小爱音箱 X10）
- L05B / L05C（小爱音箱 Play 增强版）

**如何判断该用哪种**：没有字段能直接判断，按此顺序试即可——
1. 先用默认 `mina`，让音箱播报一条消息
2. 若无声或报错，切换 `"speakerControl": "miot"`，并用下文脚本查出 `ttsCommand`
3. 若脚本提示该型号 spec 中没有 `play-text` 动作，说明 miot 方式播不了 TTS，只能用 `mina`

**注意**：
- 不同型号的小爱音箱对 `mina` 和 `miot` 的支持情况可能不同
- 如果默认 `mina` 方式无法正常工作，请尝试切换为 `miot`
- 完整兼容性列表参考：[MiGPT 兼容性文档](https://github.com/idootop/mi-gpt/blob/main/docs/compatibility.md)
- 建议自行编译测试以确定您的设备最佳配置

### TTS 动作（siid/aiid）配置与自动探测

`miot` 方式通过 MIoT 的 `intelligent-speaker` 服务发送 TTS 播报，但**不同型号该服务的 siid 不同**（例如多数老型号在 `siid=5`，而 `xiaomi.wifispeaker.x08c` 在 `siid=3`，其 `siid=5` 是麦克风服务）。发错 siid 时云端会静默拒绝（错误码如 `-704040005`），表现为"日志发送成功但音箱无声"。

插件按以下优先级确定 TTS 动作：

1. **显式配置** `ttsCommand: [siid, aiid]`（最高优先级）
2. **按型号自动探测**：启动时查询 [miot-spec.org](https://miot-spec.org) 的设备 spec，定位 `intelligent-speaker` 服务下的 `play-text` 动作（插件内置实现，无需安装 Python/MiService；查询结果与 `python3 -m miservice spec <model>` 等价。设备型号由插件登录后自动获取，无需配置）
3. **默认值** `[5, 1]`

**配置示例**（x08c）：

```json
{
  "channels": {
    "migpt": {
      "speakerControl": "miot",
      "ttsCommand": [3, 1]
    }
  }
}
```

**一键查询脚本（推荐）**：仓库自带 [scripts/find-tts-command.py](scripts/find-tts-command.py)，运行完直接得到 `[siid, aiid]` 和可粘贴的配置片段：

```bash
# 已知型号：无需登录、无需安装任何依赖
python3 scripts/find-tts-command.py --model xiaomi.wifispeaker.x08c

# 只知道设备名称：脚本先查 model 再查 spec
# （需 pip install miservice，及 MI_USER/MI_PASS 环境变量或 ~/.mi.token）
python3 scripts/find-tts-command.py 客厅音箱
```

输出示例：

```
✅ 型号: xiaomi.wifispeaker.x08c
✅ spec: urn:miot-spec-v2:device:speaker:0000A015:xiaomi-x08c:2

🔊 TTS 动作: [siid, aiid] = [3, 1]

在 openclaw.json 的 channels.migpt 中配置:

  "speakerControl": "miot",
  "ttsCommand": [3, 1]
```

若该型号的 spec 中没有 `play-text` 动作，脚本会提示改用 `mina` 方式。

**手动查询（脚本不可用时）**：

```bash
pip install miservice
python3 -m miservice spec xiaomi.wifispeaker.x08c
# 在输出中找 intelligent-speaker 服务的 iid（即 siid），
# 及其下 play-text 动作的 iid（即 aiid）
```

**特别说明**：当前项目未对所有小爱音箱型号进行全面测试，以上型号支持情况仅供参考。由于小爱音箱型号众多，不同型号可能存在差异，建议用户根据自身设备型号自行编译测试。

**配置示例**：

```json
{
  "channels": {
    "migpt": {
      "userId": "123456789",
      "password": "your_password",
      "passToken": "your_pass_token",
      "devices": ["客厅音箱"],
      "speakerControl": "miot"
    }
  }
}
```

### 3. 启动服务

```bash
openclaw gateway restart
```


## 设备名称

设备名称必须与米家 App 中设置的名称**完全一致**（包括大小写和空格）。

如果不确定设备名称，可以：
1. 开启 `debug: true` 配置
2. 启动服务查看设备列表
3. 日志中会打印所有可用设备

## 使用技能

### 播报规范

插件内置智能播报规范，AI 会自动判断内容是否适合语音播报：

- ✅ **适合播报**：简短回复、确认信息、简单问答
- ❌ **不适合播报**：代码、长文、数据、多媒体内容

对于不适合播报的内容，AI 会告知用户已通过其他渠道（如微信、邮件等）发送。

## 使用 MiService 调试测试

排查「日志显示发送成功但音箱无声」「不确定某型号 TTS 动作的 siid/aiid」等问题时，直接用 [MiService](https://github.com/yihong0618/MiService) 的 `micli` 命令单独测试小米云端接口，比反复重启网关快得多，也能与上文的 `ttsCommand` 相互印证。

### 安装

```bash
pip install miservice   # 安装后提供 micli 命令
```

> `micli spec <model>` 与前文 TTS 小节里的 `python3 -m miservice spec <model>` 等价，都是查询设备 spec。

### 方式一：账密登录（可能触发验证码）

```bash
export MI_USER="小米ID或手机号"
export MI_PASS="小米账号密码"
micli list                     # 列出账号下的设备（含 did / model）
```

首次登录会把登录态写入 token 文件（默认 `~/.mi.token`，可用 `MI_TOKEN` 环境变量指定路径）。如果账号开启了二次验证/异地登录保护，这一步可能反复要求验证码而无法完成——此时改用方式二。

### 方式二：手工构造 .mi.token 绕过账密登录

如果本插件已经登录成功过，工作目录下会生成 `.mi.json` 缓存；从中取出三个字段构造一个**最小** `.mi.token`，MiService 即可跳过账密登录（不触发验证码）：

```json
{
  "deviceId": "<.mi.json 中的 deviceId>",
  "userId": <你的小米数字ID>,
  "passToken": "<.mi.json 中 pass.passToken 的完整值>"
}
```

保存为 `~/.mi.token`（或用 `MI_TOKEN` 指定路径）后直接使用：

```bash
export MI_TOKEN="$HOME/.mi.token"
micli list
```

**原理**：首次请求时 MiService 发现缺少对应服务的凭证，会带着 `passToken` cookie 调 `serviceLogin?sid=xxx`——passToken 有效则直接换到 `ssecurity`/`serviceToken`（跳过密码步骤，因此无验证码），并自动回写到 `.mi.token` 的 `xiaomiio`（MIoT）、`micoapi`（MiNA）字段。这两个字段是自动生成的缓存，**无需手工填写**。

**注意**：
- `deviceId` 请用 `.mi.json` 里的原值（passToken 与签发时的设备标识关联，随意生成可能校验失败）
- 若 passToken 已过期，此法失效，只能回方式一重新登录

### 查询设备型号（model）

自动探测和 `micli spec` 都以设备型号（形如 `xiaomi.wifispeaker.x08c`）为入参，但米家 App 里不容易直接看到。两种查法：

**方法一：插件 debug 日志（无需 Python）**

配置 `"debug": true` 后重启网关，启动日志会打印设备信息，其中 `model` 即型号：

```
🐛 设备信息： {
  "name": "小爱万能音箱",
  "model": "xiaomi.wifispeaker.x08c",
  ...
}
```

**方法二：MiService 列出全部设备**

```bash
python3 -m miservice list full | grep -E '"(name|model|did)"'
```

在输出中按 `name` 找到自己的设备，同一段里的 `model` 即型号（`did` 供后面 `MI_DID` 使用）：

```json
"did": "<你的设备did>",
"name": "小爱万能音箱",
"model": "xiaomi.wifispeaker.x08c",
```

> ⚠️ `list full` 的完整输出还包含设备 token、MAC 地址、内外网 IP 等敏感信息，请勿截图或公开分享。

### 测试 TTS 动作（验证 siid/aiid）

拿到设备的 `did` 后，就能直接调用某个 siid 下的 play-text 动作让音箱说话，用来确认该型号正确的 siid：

```bash
export MI_DID="你的设备did"              # 也可直接用设备名
micli spec xiaomi.wifispeaker.x08c      # 查看该型号全部服务/动作，找 intelligent-speaker → play-text
micli 3-1 你好                          # 调用 siid=3, aiid=1 的动作播报（x08c 的 intelligent-speaker 在 siid=3）
micli 5-1 你好                          # 多数老型号在 siid=5
```

- `micli <siid>-<aiid> <文本>` 与插件内部的 `MiOT.doAction(siid, aiid, [text])` 等价，可交叉验证
- 哪个 siid 能让音箱正常出声，就把它填进插件配置的 `ttsCommand: [siid, aiid]`

> ⚠️ `.mi.token` 与 `.mi.json` 都含有你的登录凭证（passToken、serviceToken 等），请勿提交到仓库或分享给他人——项目 `.gitignore` 已默认忽略这两个文件。

## 故障排查

### 登录失败

**错误**: `❌ 本次登录需要验证码，请使用 passToken 重新登录`

**解决**: 使用 passToken 替代密码登录，或尝试多次登录直到不需要验证码

### 设备未找到

**错误**: `❌ 找不到设备：客厅音箱`

**解决**:
1. 检查设备名称是否与米家 App 中完全一致
2. 开启 `debug: true` 查看可用设备列表
3. 注意错别字，如「音响」vs「音箱」

### 消息轮询失败

**错误**: `❌ getConversations failed`

**解决**:
1. 检查网络连接
2. 检查 serviceToken 是否过期
3. 删除 `.mi.json` 缓存文件重新登录

## 项目结构

```
migpt-claw/
├── index.ts                 # 插件入口
├── src/
│   ├── channel.ts          # Channel 核心
│   ├── service.ts          # 认证服务
│   ├── message.ts          # 消息轮询
│   ├── speaker.ts          # TTS 播放
│   ├── config.ts           # 配置解析
│   ├── types.ts            # 类型定义
│   ├── outbound.ts         # 消息发送
│   ├── onboarding.ts       # 安装向导
│   ├── runtime.ts          # 运行时管理
│   ├── mi/                 # 小米服务
│   │   ├── mina.ts        # MiNA API
│   │   ├── miot.ts        # MIoT API
│   │   ├── account.ts     # 账号认证
│   │   ├── common.ts      # 通用工具
│   │   ├── spec.ts        # TTS 动作(siid/aiid)探测
│   │   └── typing.ts      # 类型定义
│   └── utils/              # 工具函数
│       ├── http.ts        # HTTP 请求
│       ├── codec.ts       # 编解码
│       ├── hash.ts        # 哈希工具
│       ├── io.ts          # 文件 IO
│       └── parse.ts       # 解析工具
└── skills/
    └── migpt-volume/       # 音量控制技能
        ├── index.ts
        └── SKILL.md
```

## 开发

```bash
# 安装依赖
npm install

# 构建
npm run build

```

## AI 辅助开发

本项目由 **Qwen Code** + **Qwen3.5-Plus** 大模型开发实现。

- **[Qwen Code](https://qwenlm.github.io/qwen-code-docs/zh/users/overview/)** - 阿里巴巴通义实验室推出的终端 AI 编程助手（CLI 工具）
- **[Qwen3.5-Plus](https://github.com/QwenLM/Qwen)** - 通义千问 3.5 增强版大模型，提供强大的代码理解和生成能力

感谢 AI 助手在代码编写、问题排查和文档撰写过程中提供的智能辅助！🤖

## 相关项目

本项目受到以下优秀项目的启发和帮助：

- **[MiGPT Next](https://github.com/idootop/migpt-next)** - 让小爱音箱接入 AI 大模型，实现智能对话
- **[MiService](https://github.com/yihong0618/MiService)** - 小米账号认证和米家设备控制基础库

向以上项目的作者致敬！🙏

## 开源协议

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 免责声明

本项目仅供学习和研究使用，不得用于任何商业用途或非法目的。

- 使用本项目时，请遵守当地法律法规和小米公司的相关服务条款
- 本项目与小米公司无任何关联，不构成任何官方支持或背书
- 使用本项目可能导致小米账号异常，请谨慎使用并自行承担风险
- 建议仅使用测试账号或非主要账号进行体验
- 如因使用本项目造成的任何损失（包括但不限于账号封禁、数据丢失等），本项目作者不承担任何责任
- 本项目按「原样」提供，不提供任何明示或暗示的保证

如将本项目用于生产环境或其他重要场景，请务必：
1. 仔细阅读并遵守小米开放平台的相关规范
2. 通过官方渠道获取合法的 API 调用权限
3. 评估潜在的法律和技术风险
