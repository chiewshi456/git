# 游戏project 连动入口

这个工作区现在有一个最小可跑的连动链路：

```text
城里人游戏 (/game/)
  -> POST /api/messages
  -> ai-vtuber-mvp dashboard
  -> Mika Brain v3 bridge
  -> brain_core/data/mika_v3_memory.json
```

## 一键启动

```powershell
cd "C:\Users\User\Documents\游戏project"
.\start-linked-project.ps1
```

启动后打开：

- Dashboard: http://localhost:3000
- 城里人游戏: http://localhost:3000/game/

在游戏里产生的城市日志会推送到 dashboard 的最近弹幕。dashboard 会把消息交给 `brain_core` 的 Mika v3，Mika v3 会读写自己的本地长期记忆。

## 相关组件

- `index.html` / `game.js` / `style.css`：城里人游戏原型。
- `ai-vtuber-mvp`：Web dashboard、弹幕选择、安全过滤、记忆日志。
- `brain_core`：Mika v3 本体和 `mika_v3_memory.json` 长期记忆。
- `Horizon`：信息收集系统，目前保留为独立运行入口。
- `MIKA/knowledge_system`：Mika 知识库迭代资料。

## 切换 Mika v3 的 LLM

当前 `ai-vtuber-mvp/config/localModel.json` 使用 Mika v3 的离线快脑：

```json
{
  "provider": "mika_brain_v3",
  "mikaBrainV3": {
    "llm": "off",
    "model": "qwen2.5:3b"
  }
}
```

如果本机 Ollama 和模型已准备好，可以把 `llm` 改成 `ollama`，Mika v3 会在开放聊天时调用本地模型。
