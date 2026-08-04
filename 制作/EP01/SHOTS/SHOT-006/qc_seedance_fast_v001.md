# SHOT-006｜Seedance Fast v001 质检

- 任务 ID：`cgt-20260804142254-vrzbt`
- 状态：`GENERATED / CREATIVE-QC-FAIL / USER-REVIEW-PENDING`
- 模型：`doubao-seedance-2-0-fast-260128`
- 用量：`108900 tokens`
- Seed：`73482`
- 文件：`视频/SHOT-006_杀球钉地/renders/SHOT-006_seedance_fast_v001.mp4`
- 规格：`5.09s / 1280×720 / 24fps / H.264 High / AAC 44.1kHz stereo`
- 技术检查：完整解码；黑帧 `0`；>0.5秒冻结 `0`。
- 视觉初检：羽毛球软木球头落地、铁蛋错愕进入、E4大眼与左右汗珠、回弹均生成；身份锚点稳定。
- 失败原因：脚本要求 `0.75s` 一帧硬切到脸部，实际场景切换约在 `1.833s`，地板段明显过长，压缩了错愕表演时间。
- 初评分：`88/100`，低于正式门槛；不得锁定。是否重生成须重新取得付费确认。
- SHA-256：`2efb798a67727f85a413f405a037bc74291ce7b55ce29e78fadd16d6d2131b8f`

