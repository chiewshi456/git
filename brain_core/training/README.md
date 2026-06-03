# Training Data

`dataset.jsonl` is generated automatically while `brain_core` runs.

Each line is one training sample with:

- `user_input`
- `intent`
- `emotion`
- `topics`
- `feedback`
- `style_signal`
- `reply_intent`
- `ai_reply`
- `state`
- `memory_context`
- `growth`
- `teaching`
- empty `quality_scores` for later human rating

Safety-blocked inputs are redacted as `[blocked_safety_input]`.

Teaching commands are stored as `sample_type: "teaching"` and include a `teaching` object.

`starter_dataset.jsonl` is a small curated cold-start dataset. Training uses it by default together with `dataset.jsonl`.

Useful teaching inputs:

```text
teach: like=节奏游戏
teach: dislike=太长的回答
teach: style=direct
teach: rule=回答尽量短一点
teach: correction=刚才应该先承认不知道
```

Inspect stats:

```powershell
python training/export_dataset.py
```

Train local classifiers:

```powershell
python training/train_classifiers.py
```

This writes:

```text
training/models/intent_classifier.json
training/models/feedback_classifier.json
training/models/topic_classifier.json
training/models/training_report.json
```

Predict with trained models:

```powershell
python training/predict_classifiers.py "我今天压力大睡不着"
```

Train without starter data:

```powershell
python training/train_classifiers.py --no-starter
```
