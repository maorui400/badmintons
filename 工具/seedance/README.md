# Seedance 本地调度工具

该工具默认离线。只有 `submit`、`status`、`download` 会访问网络，而且必须同时满足：

1. 当前对话中用户已明确批准本轮 API 操作。
2. 命令显式传入 `--approve-api-call API_CALL_CONFIRMED_FOR_THIS_RUN`。
3. 环境变量 `ARK_API_KEY` 已配置。
4. 所有本地参考素材都已经填写远程 URL 或 `asset://` URI。

## 离线命令

```powershell
工具\seedance\seedance.cmd doctor
工具\seedance\seedance.cmd validate 制作\EP01\EP01_批次清单.json
工具\seedance\seedance.cmd compile 制作\EP01\EP01_批次清单.json
```

`compile` 只生成请求预览和缺失项报告，不访问 API、不产生费用。

## 联网命令

联网命令仅作为后续执行入口保留。不得因为脚本已经存在就绕过用户确认。

```powershell
工具\seedance\seedance.cmd submit 制作\EP01\EP01_批次清单.json `
  --approve-api-call API_CALL_CONFIRMED_FOR_THIS_RUN
```

状态查询和下载同样需要一次性确认参数。密钥禁止放在命令行参数中。
