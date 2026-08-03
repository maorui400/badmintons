# Seedance 制作入口

- 主流程版本：`SEEDANCE-PIPELINE-v001`
- 默认视频生成器：火山方舟 Seedance
- 默认后期：FFmpeg
- HyperFrames：仅用于字幕、片头、信息图和可复用图形包装，不再承担运动漫画主体生成
- 网络策略：`OFFLINE-BY-DEFAULT`

## 快速流程

1. 在 `制作/<集数>/` 一次规划完整剧情与全部镜头。
2. 每个镜头建立 `shot.json`、`prompt.md`、`assets.json`。
3. 批量生成并审核所有关键帧。
4. 运行本地验证和请求预编译；此阶段不访问 API。
5. 用户明确确认“调用 API”后，才允许提交批次。
6. 独立镜头并行；依赖上一段尾帧的镜头按依赖链顺序提交。
7. 下载结果后抽取首、中、尾帧，执行角色、动作、画风和技术质检。
8. 只重新生成失败镜头，最终使用 FFmpeg 拼接。

## 跨设备与新对话恢复

1. 先读取 `风格/当前创作清单.md`。
2. 再读取当前集的 `制作/<集数>/当前执行状态.md`。
3. 检查本机是否配置 `ARK_API_KEY`、`TOS_ACCESS_KEY`、`TOS_SECRET_KEY`；仓库不会同步密钥。
4. 安装 `tos==2.9.2`，运行素材上传工具刷新私有签名链接。
5. 运行 `validate` 和 `compile`；确认 `network_ready_shots` 等于计划提交的镜头数。
6. 只有用户针对本轮明确确认付费调用后，才执行 `submit`。

运行时签名链接、请求预览、任务状态和下载中间文件位于每集的 `runtime/` 或 `_build/`，
均不作为跨设备事实来源。可恢复事实必须写入 `当前执行状态.md`、批次 JSON 和 TOS 对象清单。

## 状态机

`PLANNED → KEYFRAME-APPROVED → PROMPT-READY → API-APPROVED → SUBMITTED → GENERATED → QC-PASS → LOCKED`

其中：

- `API-APPROVED` 只对当次明确确认有效，不写成永久授权。
- `GENERATED` 不等于正式素材；必须通过 `QC-PASS`。
- 低于 90 分或触发否决项的镜头不得进入 `LOCKED`。

## API 安全规则

- 密钥只从环境变量 `ARK_API_KEY` 读取，禁止写入仓库、日志、Prompt 或任务 JSON。
- 本地素材必须先获得可供火山方舟读取的远程 URL 或 `asset://` URI。
- `compile`、`validate`、`doctor` 永不访问网络。
- `submit`、`status`、`download` 属于联网动作，执行前必须再次征得用户确认。
- 提交命令必须显式携带一次性确认参数，防止误触和重复计费。
- 相同请求使用负载哈希去重；已有任务 ID 时默认不重复提交。

## 目录约定

```text
制作/
├── README.md
├── SEEDANCE-PIPELINE-v001.md
├── _模板/
│   ├── episode_batch.template.json
│   ├── shot.template.json
│   ├── assets.template.json
│   └── qc.template.json
└── EP01/
    ├── EP01_导演脚本.md
    ├── EP01_连续性地图.md
    ├── EP01_批次清单.json
    ├── 当前执行状态.md
    ├── tos_storage.json
    ├── runtime/               # 临时签名 URL，不进入 Git
    └── SHOTS/
        └── SHOT-001/
            ├── shot.json
            ├── prompt.md
            └── assets.json
```

生成记录、请求预览和任务结果默认写入每集的 `_build/`，不得覆盖分镜、角色或风格源文件。
