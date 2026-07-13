import { Http } from '../utils/http.js';

/** MIoT TTS 动作坐标：[siid, aiid] */
export type TTSCommand = [siid: number, aiid: number];

const SPEC_INSTANCES_URL = 'https://miot-spec.org/miot-spec-v2/instances';
const SPEC_INSTANCE_URL = 'https://miot-spec.org/miot-spec-v2/instance';

/**
 * 已知型号的 TTS 动作回退表（在线探测失败时使用，欢迎 PR 补充）。
 *
 * 说明：不同型号的 intelligent-speaker 服务 siid 不同，
 * 例如 x08c 在 siid=3，而部分 Redmi 型号在 siid=5。
 */
const KNOWN_TTS_COMMANDS: Record<string, TTSCommand> = {
  'xiaomi.wifispeaker.x08c': [3, 1],
};

/** 默认 TTS 动作（多数老型号为 siid=5, aiid=1） */
export const DEFAULT_TTS_COMMAND: TTSCommand = [5, 1];

/**
 * 根据设备型号自动探测 TTS 播报动作的 [siid, aiid]。
 *
 * 探测方式与 `python3 -m miservice spec <model>` 等价：
 * 1. 从 miot-spec.org 公开接口按 model 查到 spec 实例的 type URN（取最高版本）；
 * 2. 拉取完整 spec，定位 type 含 `:intelligent-speaker:` 的服务；
 * 3. 在该服务的 actions 中定位 type 含 `:play-text:` 的动作；
 * 4. 返回 [service.iid, action.iid]。
 *
 * 任一步失败则回退到 KNOWN_TTS_COMMANDS，仍未命中返回 undefined（由调用方决定默认值）。
 */
export async function detectTtsCommand(model?: string): Promise<TTSCommand | undefined> {
  if (!model) {
    return undefined;
  }
  try {
    const instancesRes: any = await Http.get(SPEC_INSTANCES_URL, { status: 'released' });
    const instances: any[] = instancesRes?.instances ?? [];
    if (instancesRes?.isError || instances.length < 1) {
      return KNOWN_TTS_COMMANDS[model];
    }

    const matched = instances.filter((i: any) => i?.model === model);
    if (matched.length < 1) {
      return KNOWN_TTS_COMMANDS[model];
    }

    // 同一型号可能有多个版本的 spec，取最高版本
    const latest = matched.sort(
      (a: any, b: any) => (b?.version ?? 0) - (a?.version ?? 0),
    )[0];

    const spec: any = await Http.get(SPEC_INSTANCE_URL, { type: latest.type });
    if (spec?.isError) {
      return KNOWN_TTS_COMMANDS[model];
    }

    const services: any[] = spec?.services ?? [];
    const speakerService = services.find(
      (s: any) => typeof s?.type === 'string' && s.type.includes(':intelligent-speaker:'),
    );
    const playText = (speakerService?.actions ?? []).find(
      (a: any) => typeof a?.type === 'string' && a.type.includes(':play-text:'),
    );

    if (speakerService?.iid != null && playText?.iid != null) {
      return [speakerService.iid, playText.iid];
    }
    return KNOWN_TTS_COMMANDS[model];
  } catch {
    return KNOWN_TTS_COMMANDS[model];
  }
}
