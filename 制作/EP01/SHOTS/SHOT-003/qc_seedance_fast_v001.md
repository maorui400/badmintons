# SHOT-003｜Seedance Fast v001 质检

- 任务 ID：`cgt-20260804141932-qw5pd`
- 状态：`GENERATED / CREATIVE-QC-FAIL / USER-REVIEW-PENDING`
- 模型：`doubao-seedance-2-0-fast-260128`
- 用量：`108900 tokens`
- Seed：`71667`
- 文件：`视频/SHOT-003_场边热身/renders/SHOT-003_seedance_fast_v001.mp4`
- 规格：`5.09s / 1280×720 / 24fps / H.264 High / AAC 44.1kHz stereo`
- 技术检查：完整解码；黑帧 `0`；>0.5秒冻结 `0`。
- 视觉初检：弓步拉伸、受控抬腿、头顶挥拍三动作均出现，身份与装备总体稳定。
- 失败原因：脚本要求在 `1.55s / 3.10s` 两次一帧硬切；自动场景检测未发现硬切，第二次动作切换附近存在明显叠影/形变过渡。
- 初评分：`87/100`，低于正式门槛；不得锁定。是否重生成须重新取得付费确认。
- SHA-256：`e8cb797dea2ad3d19c48533710748d268ebf96ac484d2777f897acc7b459518b`

