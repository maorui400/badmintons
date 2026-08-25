# EP03 骨骼 IK 动作预演

- 工程：`EP03_骨骼IK动作预演_v001.blend`
- 生成脚本：`build_ep03_rigged_previs.py`
- 铁蛋动作：`ACT_EP03_TIEDAN_RALLY_BLOCKING_v001`
- 橙超动作：`ACT_EP03_ORANGE_RALLY_BLOCKING_v001`
- 唯一羽毛球路径：`ACT_EP03_ONLY_SHUTTLE_PATH_v001`
- 关键帧：`动作关键帧_v001/SHOT-001—006/`，每镜4张，共24张

## 骨骼控制器

- `root`：角色整体位置、朝向和身体大倾斜。
- `pelvis / spine / chest / neck / head`：重心、躯干扭转和视线。
- `hand_ik.L / hand_ik.R`：双手 IK；球拍永久绑定 `hand_ik.R`。
- `elbow_pole.L / elbow_pole.R`：肘部朝向。
- `foot_ik.L / foot_ik.R`：双脚 IK。
- `knee_pole.L / knee_pole.R`：膝部朝向。

铁蛋的闭合黑色手表只绑定 `hand_ik.R`，与右手球拍共享运动控制器；左腕没有手表对象。两名角色的球拍三维总长固定约 `0.675m`。

## 时间轴

- `24fps / 1—720帧 / 30秒`。
- 每120帧为一个镜头，帧 `1 / 121 / 241 / 361 / 481 / 601` 绑定六台摄影机，播放时直接硬切。
- 每镜使用4个阻塞关键姿态，人物骨骼关键帧插值为 `CONSTANT`，便于逐姿态审核，不代表最终动作补间。
- 羽毛球位置采用独立路径，工程中始终只有一个羽毛球控制器。

## 手动调整

选中 `TIEDAN_CHAR-001_v003_RIG` 或 `ORANGE_CHAR-002_v001_RIG`，切换到 `Pose Mode`，再移动对应 IK 控制骨。修改某个动作节点后，在当前帧选中改动骨骼并按 `I`，插入 `Location & Rotation`。当前阶段不要把人物关键帧改成平滑插值，待24个姿态全部确认后再制作动作补间。
