#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据设备名称或型号查询小爱音箱 MIoT TTS 播报动作坐标 [siid, aiid]。

用法:
  # 已知型号（无需登录、无需安装任何依赖）:
  python3 scripts/find-tts-command.py --model xiaomi.wifispeaker.x08c

  # 只知道设备名称（需要 pip install miservice_fork 及登录凭证）:
  export MI_USER="小米ID"
  export MI_PASS="账号密码"        # 或准备好 ~/.mi.token（见 README）
  python3 scripts/find-tts-command.py 客厅音箱

原理:
  1. 设备名称 -> model: 调用 `python3 -m miservice list full` 列出账号下设备并按名称匹配;
  2. model -> [siid, aiid]: 查询 miot-spec.org 公开接口, 定位 intelligent-speaker
     服务下的 play-text 动作（与插件启动时的自动探测逻辑一致）。
"""
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request

INSTANCES_URL = "https://miot-spec.org/miot-spec-v2/instances?status=released"
INSTANCE_URL = "https://miot-spec.org/miot-spec-v2/instance?type={}"


def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "migpt-claw-find-tts/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_device_by_name(device_name):
    """调用 miservice CLI 列出设备, 按名称匹配, 返回设备 dict（含 name/model/did）。"""
    try:
        out = subprocess.run(
            [sys.executable, "-m", "miservice", "list", "full"],
            capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError:
        sys.exit("❌ 无法运行 miservice, 请先安装: pip install miservice_fork")

    stdout = out.stdout or ""
    devices = None
    try:
        devices = json.loads(stdout)
    except ValueError:
        # 输出可能混有非 JSON 行, 退化为提取最外层 JSON 数组
        m = re.search(r"\[.*\]", stdout, re.S)
        if m:
            try:
                devices = json.loads(m.group(0))
            except ValueError:
                pass
    if not isinstance(devices, list) or not devices:
        sys.exit(
            "❌ 无法获取设备列表, 请检查登录凭证（MI_USER/MI_PASS 环境变量或 ~/.mi.token）\n"
            "--- miservice 输出 ---\n" + stdout + (out.stderr or "")
        )

    def norm(s):
        return (s or "").strip().lower()

    target = norm(device_name)
    exact = [d for d in devices if norm(d.get("name")) == target]
    fuzzy = [d for d in devices if target and target in norm(d.get("name"))]
    matched = exact or fuzzy
    if not matched:
        names = "、".join(d.get("name", "?") for d in devices)
        sys.exit(f"❌ 找不到设备「{device_name}」, 账号下的设备: {names}")
    if len(matched) > 1:
        print("⚠️ 匹配到多个设备, 取第一个:", "、".join(d.get("name", "?") for d in matched))
    return matched[0]


def find_tts_command(model):
    """查询 miot-spec.org, 返回 (siid, aiid, spec_type) 或 None。"""
    data = http_get_json(INSTANCES_URL)
    insts = [i for i in data.get("instances", []) if i.get("model") == model]
    if not insts:
        sys.exit(f"❌ miot-spec.org 上找不到型号 {model} 的 spec, 请确认型号拼写")
    latest = max(insts, key=lambda i: i.get("version", 0))
    spec = http_get_json(INSTANCE_URL.format(urllib.parse.quote(latest["type"])))
    for svc in spec.get("services", []) or []:
        if ":intelligent-speaker:" in (svc.get("type") or ""):
            for act in svc.get("actions", []) or []:
                if ":play-text:" in (act.get("type") or ""):
                    return svc["iid"], act["iid"], latest["type"]
    return None


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    did = None
    if args[0] == "--model":
        if len(args) < 2:
            sys.exit("❌ 用法: --model <型号>, 例如 --model xiaomi.wifispeaker.x08c")
        model = args[1]
    else:
        device = find_device_by_name(args[0])
        model = device.get("model")
        did = device.get("did")
        print(f"✅ 设备: {device.get('name')} (did={did})")
        if not model:
            sys.exit("❌ 该设备没有 model 字段, 无法查询 spec")

    print(f"✅ 型号: {model}")
    result = find_tts_command(model)
    if not result:
        sys.exit(
            f"⚠️ 型号 {model} 的 spec 中没有 intelligent-speaker/play-text 动作。\n"
            "   该型号可能不支持 miot 方式 TTS, 请使用默认的 mina 方式"
            "（speakerControl 不填或填 \"mina\"）。"
        )
    siid, aiid, spec_type = result
    print(f"✅ spec: {spec_type}")
    print(f"\n🔊 TTS 动作: [siid, aiid] = [{siid}, {aiid}]\n")
    print("在 openclaw.json 的 channels.migpt 中配置:\n")
    print(f'  "speakerControl": "miot",')
    print(f'  "ttsCommand": [{siid}, {aiid}]\n')
    tips = f"micli {siid}-{aiid} 你好"
    if did:
        tips = f"export MI_DID={did} && " + tips
    print(f"用 micli 验证播报: {tips}")


if __name__ == "__main__":
    main()
