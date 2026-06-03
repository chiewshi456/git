# neuro_like_ai_brain

`neuro_like_ai_brain` 是一个 Neuro-sama-like AI Streamer Brain 命令行原型。

它不是普通聊天机器人，而是一个面向直播互动的“AI 主播大脑”：有 persona、状态、记忆、情绪、欲望系统、自主发言和 provider 抽象。v0.1 不接真实 LLM API，全部用规则、模板和状态机模拟低延迟直播反应。

## 如何运行

需要 Python 3.10+，不需要额外第三方库。

```powershell
cd neuro_like_ai_brain
python main.py
```

启动后：

- 输入 `quit` 退出
- 直接按 Enter 表示聊天室安静，会触发自主发言
- 每次回复后会显示 debug，方便观察 intent、emotion、state 和 memory

## 当前版本

v0.1 默认使用 `fake_provider`：

- 不调用 OpenAI
- 不调用 Ollama
- 不联网
- 不做真实 TTS、Live2D、OBS 控制
- 使用 Fast Brain 模板快速回复高频直播事件

## Fast Brain 和 Slow Brain

直播互动需要低延迟。高频事件，比如问候、鼓励、打赏、夸奖、调侃、辱骂、聊天室安静，不应该每次都等待 LLM 推理。

因此架构分成两层：

- Fast Brain：规则、关键词、状态机、模板回复，负责秒回
- Slow Brain：以后接入 OpenAI、Ollama、OpenRouter 等 LLM，处理复杂问题、长上下文和更深的思考

当前版本只实现 Fast Brain，并在 `providers/` 中保留 Slow Brain 接口。

## Provider 切换预留

主程序通过 `NEURO_BRAIN_PROVIDER` 选择 provider：

```powershell
$env:NEURO_BRAIN_PROVIDER="fake"
python main.py
```

未来可以切换：

```powershell
$env:NEURO_BRAIN_PROVIDER="ollama"
python main.py
```

```powershell
$env:OPENAI_API_KEY="你的 key"
$env:NEURO_BRAIN_PROVIDER="openai"
python main.py
```

当前 `ollama_provider.py` 和 `openai_provider.py` 只保留结构和 TODO，不会真的发起网络请求。

## 未来接入方向

TTS：

- 在 `NeuroLikeBrain.process_input()` 返回 `reply` 后，把文本发送给 TTS provider
- 可增加 `providers/tts_provider.py`
- 输出音频文件路径或实时音频流

Live2D：

- 使用 `emotion` 映射表情
- 使用 `state` 映射动作强度，比如 stress 高时更紧张，playfulness 高时更调皮
- 可增加 `live2d/adapter.py`，把情绪事件转成 Live2D 参数

OBS：

- 在每次回复后发送字幕、场景切换或事件提示
- 可增加 `obs/adapter.py`
- 后续接 OBS WebSocket

## 下一步开发计划

1. 增加 viewer_id 输入或接入真实弹幕来源，让 `known_viewers` 记住不同观众。
2. 给 Fast Brain 增加更细的 intent，例如感谢、道歉、催促、点歌。
3. 增加 Slow Brain 路由：普通高频事件走模板，复杂问题才走 LLM。
4. 给 provider 加 timeout、fallback 和缓存，避免直播卡住。
5. 接入 TTS，把回复转成语音。
6. 接入 Live2D，用 emotion 和 state 驱动表情。
7. 接入 OBS，用回复和事件驱动字幕、场景和直播提示。
