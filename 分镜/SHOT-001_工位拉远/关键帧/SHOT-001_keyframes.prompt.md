# SHOT-001 关键帧生成提示词

- 用例：`illustration-story`
- 状态：`KEYFRAME-CANDIDATE`
- 生成方式：内置 `imagegen`
- 统一参考：`人物/CHAR-001_铁蛋/三视图/CHAR-001_turnaround_v003_COST-B_001.png`
- 统一比例：`16:9`

## 输出文件

- `SHOT-001_KF01_v001.png`：0.00s，电脑屏幕摄像头位置 45° 俯拍。
- `SHOT-001_KF02_v001.png`：1.60s，同轴后移升高，出现一组工位。
- `SHOT-001_KF03_v001.png`：3.30s，同轴超远景，铁蛋缩为工位网格中的一点。
- 三帧状态：`CANDIDATE / NOT LOCKED`
- 视频状态：`NOT GENERATED`

## 统一身份与风格前缀

```text
NEON-SHUTTLE-CATS, STYLE-v002. Original sharp 2D comic-animation keyframe,
hard-edge cel shading, strong clean silhouette, varied dark navy line weight,
graphic color blocks, restrained cyan screen rim light, harsh cool-white office
fluorescent lighting. Preserve CHAR-001 Tiedan v003 exactly from the supplied
locked turnaround: anthropomorphic male American Shorthair cat, compact agile
seven-head build, silver classic tabby and white fur, fixed three-stripe M on
forehead, three cheek arcs on each side, green-gray almond eyes, pink nose,
white muzzle/chin/chest/lower forearms, ringed tail with dark tip. Matte-black
watch on the RIGHT wrist with a closed black strap wrapping the full wrist.
Temporary scene wardrobe COST-OFFICE-A DRAFT: plain white long-sleeve office
shirt, charcoal straight-leg trousers, existing white-black athletic shoes.
No racket or badminton equipment.
```

## KF01

```text
Close medium office keyframe from a camera mounted at the top-center edge of
Tiedan's computer monitor, elevated and pitched downward about 45 degrees.
The monitor top edge is a thin extreme foreground strip at the bottom. Tiedan
sits slightly hunched and types with both hands, looking at the screen with a
restrained focused, mildly tired E1 expression. Face, forehead M marking,
hands, keyboard, and right-wrist black watch are crisp. A few anonymous
feline-furry office silhouettes and desks dissolve into strong background
depth blur. Cool white overhead light plus subtle cyan screen light. 16:9,
no text, no logo, no watermark.
```

## KF02

```text
Same office, same spatial axis and same workstation after a hard cut. Camera
has moved backward and upward while keeping a 45-degree downward view. Wide
shot showing six to ten cubicles. Tiedan remains seated at the same desk and
types continuously, about 18 percent of frame height and the only relatively
sharp character. All coworkers are low-detail anthropomorphic feline
silhouettes with shallow depth blur and mild motion smearing; their faces and
screens are unreadable. Repeating desk lines begin to overpower the character.
16:9, no text, no logo, no watermark.
```

## KF03

```text
Same office, same axis and same workstation after a second hard cut. Very high,
very distant wide master shot, 55-to-65-degree downward angle. Dozens of
repeating cubicles form a dense geometric grid and strong converging lines.
Tiedan is no more than 5 percent of frame height, still traceable by silver-white
fur, ringed tail, white shirt, right-wrist black watch, and a small cyan screen
glow, but visually reduced to one worker among many. Everyone else remains
anonymous blurred feline-furry silhouettes; no individual coworker steals
focus. The mood is quiet, cold, repetitive, and existential. 16:9, no text,
no logo, no watermark.
```

## 通用负面约束

```text
No humans, no human faces, no quadruped pet cats, no duplicate Tiedan, no extra
ears or tails, no extra limbs or fingers, no altered tabby markings, no watch
on left wrist, no open or partial watch strap, no sports court, no badminton
gear, no readable UI, no random text, no logos, no photorealism, no realistic
fur rendering, no 3D plastic render, no full-frame neon glow, no comedy
distortion.
```
