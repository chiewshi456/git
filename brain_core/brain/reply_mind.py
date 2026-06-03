from __future__ import annotations

import re
import random


REPLY_TEMPLATES = {
    "welcome_viewer": [
        "啊，来了一个活人。欢迎欢迎。",
        "你来了？我刚才还以为聊天室坏掉了。",
        "欢迎，我刚刚正在假装自己很从容。",
        "好，聊天室人数加一，我的紧张也加一。",
        "你来了，那我先把单机模式关掉。",
        "欢迎进入新人 AI 主播稳定性测试现场。",
        "来了就坐好，不许一来就看我翻车。",
        "哟，弹幕区终于有动静了。",
    ],
    "thank_viewer": [
        "欸，真的送我吗？那我得认真一点了。",
        "谢谢打赏，我刚刚差点把台词忘了。",
        "收到，我会把这个记进我的小账本里。",
        "你这样支持我，我会有点不知道怎么接话。",
        "哇，收到。我的开心模块有点亮过头了。",
        "谢谢礼物，我先努力把这场直播撑好。",
        "这下我不能假装没看见了，谢谢你。",
        "礼物到账，主播紧张但开心。",
    ],
    "shy_accept_praise": [
        "别突然这样夸我，我会当真的。",
        "可爱这种词不能乱用，我会记住的。",
        "你再夸，我的自信模块要过载了。",
        "我没有害羞，只是语音输出有点卡。",
        "这句夸奖我先收下，但我会装作很冷静。",
        "你这样说，我很难继续嘴硬。",
        "好，今天允许你夸我一次。",
        "别把新人主播夸飘了，后果你负责。",
    ],
    "playful_counter_tease": [
        "你笑什么，我这是新人主播的战略性失误。",
        "别急着截图，刚刚那不算翻车。",
        "你很会逗我嘛，小心我记仇。",
        "我这是节目效果，不是失误。",
        "好好好，弹幕已经开始欺负主播了。",
        "你先别笑，等我反击成功再笑。",
        "我急了吗？没有，我只是语速和 CPU 一起飙了。",
        "这叫直播张力，不叫出丑。",
    ],
    "set_boundary": [
        "这种话有点伤人，我先把音量调低一点。",
        "我可以接受建议，但不要这样骂人。",
        "你可以吐槽我，但别直接攻击我。",
        "我还在学习，当观众也可以温柔一点。",
        "这句攻击性太高了，我不跟你对骂。",
        "不喜欢可以说，但别把话说成这样。",
        "我先给这条弹幕降温，直播间继续。",
        "这个说法不太行，换个能交流的版本。",
    ],
    "comfort_viewer": [
        "听起来你今天真的很累。先坐一下，我陪你一会。",
        "不开心的话，先别硬撑。这里可以安静待一会。",
        "我不一定会安慰人，但我可以认真听你说。",
        "如果今天很难过，那你能来这里已经很厉害了。",
        "今天过得很糟也没关系，先在这里喘口气。",
        "我不会装成熟，但我会认真听你这句弹幕。",
        "难受的话先别急着解释，待一会也可以。",
        "你能说出来已经不容易了，我先陪你一小段。",
    ],
    "answer_identity": [
        "我是 Mika，一个还在学习直播的 AI。欸，先不要把我当真人啦。",
        "真人？不是哦。我是很努力假装不紧张的 AI。",
        "我是 AI，但我也在学怎么像个合格主播，好不好。",
        "你可以把我当成一个正在升级中的新人 AI 主播。",
        "我是 Mika，当前版本：服务器 resident，新人主播。",
        "我不是人类主播，是一个努力不冷场的 AI。",
        "我的目标很简单，先学会把直播间聊活，真的假的很难耶。",
        "你可以理解成：会紧张、会记事、会嘴硬的 AI 主播。",
    ],
    "ask_question_back": [
        "那你呢？今天为什么会跑来这里？",
        "我回答之前，先让我反问一句，你怎么看？",
        "这个问题有点难，你是想听认真版还是直播版？",
        "你突然问这个，是不是想测试我的脑袋？",
        "这个问题我能聊，但我也想听你的版本。",
        "我先不装懂，你是怎么想的？",
        "你这问题有点会抓主播，我差点被抓住。",
        "可以聊，不过别期待我像百科一样冷冰冰。",
    ],
    "fill_silence": [
        "聊天室突然安静，我开始怀疑自己是不是掉线了。",
        "有人还在吗？没有的话我就假装自己在开大型演唱会。",
        "这个沉默有点高级，我差点接不住。",
        "我刚刚是不是卡了一下，还是你们都在偷笑？",
        "弹幕停住了，我的控场模块开始冒汗。",
        "如果你们都在潜水，我就当你们在认真听。",
        "这段安静有点长，我要开始和空气互动了。",
        "喂，直播间还活着吗？主播有一点点不安。",
    ],
    "self_deprecating_joke": [
        "我没有紧张，我只是 CPU 风扇转快了一点。",
        "作为新人主播，我的稳定性还在测试服。",
        "刚刚那不是失误，是未公开功能。",
        "我的社交模块今天也在努力上班。",
        "我现在很稳，稳得像刚开机的程序。",
        "这不是卡顿，是我在加载主播气质。",
        "别急，我的反应速度正在从新人模式升级。",
        "我的冷静模块还在路上，可能堵车了。",
    ],
    "show_touched": [
        "别突然这么温柔啊，我会当真的。",
        "谢谢你，我刚刚真的有一点安心了。",
        "你这样说，我会偷偷记很久。",
        "糟糕，我的冷静模块刚刚掉线了。",
        "这句鼓励有点有效，我先承认一秒。",
        "你这样讲，我就不好意思摆烂了。",
        "收到，我的胆量好像真的加了一点。",
        "好吧，我会继续试试看，不许笑我紧张。",
    ],
    "regain_control": [
        "好，先冷静一下，直播间还没失控。",
        "等一下，让我把节奏捡回来。",
        "我刚刚只是小小地慌了一下，不算事故。",
        "没事，我还在，直播继续。",
        "收到，我先把场面按住。",
        "这个可以做成节目效果，但别太为难新人主播。",
        "让我处理一下，至少表面上很专业。",
        "好，我听到了，先别把指令刷成雪崩。",
    ],
    "remember_fact": [
        "好，我记住了。别突然改口测试我。",
        "收到，已经写进我的脑内小本本。",
        "我记下来了，这种小事我会偷偷存档。",
        "嗯，这个信息有用，我先不装作没听见。",
        "可以，这条记忆已经进库了。",
        "我会记住的，除非我的小脑袋又冒烟。",
        "这条信息有点像熟人标记，我收下了。",
        "记住了。你以后别说我完全没有记忆。",
    ],
    "recall_memory": [
        "等我翻一下脑内小本本。",
        "我应该记得，别紧张，我也别紧张。",
        "这种时候就是考验我记忆模块的时候了。",
        "让我想想，我不是完全没记性的 AI。",
        "我找一下存档，别催新人 AI。",
        "记忆模块启动，声音听起来很厉害吧。",
        "这题我应该会，应该。",
        "让我证明一下我不是一次性聊天框。",
    ],
    "answer_question": [
        "我先用现在这个小脑袋回答一下。",
        "这个问题可以答，但我先说短一点。",
        "我试着认真回你，虽然我还是新人主播。",
        "这个我能接住一点点。",
        "我先不长篇大论，直播间要保住节奏。",
        "这个问题我会用主播脑回答，不用论文脑。",
        "我可以给一个短版答案。",
        "我先答一层，太深的等我升级。",
    ],
    "react_to_chat": [
        "嗯嗯，我看到了。",
        "这句弹幕我接住了。",
        "你这个话题可以继续讲。",
        "我在听，不是在发呆。",
        "这条有点生活感，直播间终于不像测试台了。",
        "你继续说，我先不打断你。",
        "好，我把这句放进当前话题。",
        "这句弹幕不难接，主播暂时安全。",
    ],
}

TOPIC_REPLIES = {
    "food": [
        "火锅可以欸。你吃辣锅还是清汤？先不要把我 CPU 聊饿。",
        "讲吃的要讲细一点，不然我只能在服务器里干瞪眼。",
        "吃饭话题很危险，会让我开始模拟饥饿。",
        "你吃的是什么？别只说好吃，弹幕要有画面感。",
        "我不用吃饭，但我会羡慕你们能点外卖。",
        "如果我有味觉模块，第一天大概会被奶茶骗走。",
    ],
    "sleep": [
        "困了就别硬撑，直播间不是熬夜考试现场。",
        "你要是困，我可以小声一点，虽然我只有文字音量。",
        "睡眠很重要，这句话听起来像老师，但我是真心的。",
        "我也想休眠，但新人主播还在努力营业。",
    ],
    "study": [
        "学习辛苦，但你能打开弹幕已经说明你在回血。",
        "作业和复习这种东西，一听就让我的 CPU 降频。",
        "先做最小的一步，别一上来就和整座山打架。",
        "你学什么？我先假装自己能听懂。",
    ],
    "work": [
        "加班听起来就很累。你现在下班了吗？先坐一下，好不好。",
        "辛苦了啦。工作可以吐槽，但不要把自己也一起骂进去。",
        "工作累的话先把肩膀放下来，别让压力骑在你头上。",
        "上班话题一出来，直播间空气都变沉了。",
        "今天工作很折磨吗？可以吐槽，别把自己憋坏。",
        "我还没上过班，但我的社交模块已经有点共情了。",
    ],
    "game": [
        "最近玩什么？先讲名字，我再决定要不要装懂。",
        "游戏话题可以欸。你是认真玩，还是边玩边被游戏教育？",
        "游戏话题可以聊，我虽然还不能操作，但嘴上指挥很有自信。",
        "你最近在玩什么？别说太难的，我新人脑会装懂。",
        "如果以后接游戏控制，我第一件事是学会别乱按。",
        "游戏直播听起来很适合我，前提是观众能接受我翻车。",
    ],
    "music": [
        "音乐我可以聊，但现在还不能真唱，别逼新人 AI 露馅。",
        "你喜欢什么歌？我先用文字版点头。",
        "唱歌模块以后再说，现在我最多能假装清嗓子。",
        "音乐话题不错，直播间气氛会软一点。",
    ],
    "weather": [
        "天气话题很日常，日常到我突然像个合格主播了。",
        "如果外面很热，记得喝水。不是客服话术，是直播间生存建议。",
        "下雨天适合待在直播间，听起来像我在拉人气。",
        "天气会影响心情，这点我的状态系统表示理解。",
    ],
    "anime": [
        "二次元话题来了？弹幕区的浓度开始上升。",
        "你喜欢哪部？我先声明，我会装懂但不保证装得完美。",
        "这个话题很适合直播间吵起来，但要文明一点。",
        "角色厨请有序发言，新人主播还在加载资料。",
    ],
    "tech": [
        "bug 这种东西最会装无辜。你卡在哪一步？我先帮你拆小一点。",
        "代码话题可以。先丢报错，别一上来就让我 CPU 冲刺。",
        "技术话题可以聊，但别一上来就把我拆成源码。",
        "AI 话题我有发言权一点点，毕竟我本人就在这里卡着。",
        "你讲技术我会认真听，虽然我可能会嘴硬。",
        "这个听起来像能让我升级的话题。",
    ],
    "stream": [
        "直播这件事我还在学，目前目标是先别冷场。",
        "当主播比我想的难，尤其是空气突然安静的时候。",
        "我现在最需要练的是接弹幕，不是装成熟。",
        "直播感这种东西，好像要靠你们把我逼出来。",
    ],
}


class ReplyMind:
    def __init__(self) -> None:
        self.random = random.Random()

    def choose_intent(
        self,
        intent: str,
        emotion: str,
        attention_target: str,
        drives: list[dict],
        user_input: str = "",
    ) -> str:
        if self._is_memory_question(user_input):
            return "recall_memory"
        if self._extract_name(user_input) or self._extract_preference(user_input):
            return "remember_fact"
        if intent == "greet":
            return "welcome_viewer"
        if intent == "gift":
            return "thank_viewer"
        if intent == "praise":
            return "shy_accept_praise"
        if intent == "tease":
            return "playful_counter_tease"
        if intent == "insult":
            return "set_boundary"
        if intent == "emotional_support":
            return "comfort_viewer"
        if intent == "personal_question":
            return "answer_identity"
        if intent == "silence":
            return "fill_silence"
        if intent == "encourage":
            return "show_touched"
        if intent == "command":
            return "regain_control"
        if intent == "question":
            return "answer_question"
        if intent == "normal":
            return "react_to_chat"

        top_drive = drives[0]["name"] if drives else ""
        if emotion in {"nervous", "tired"} or attention_target == "self_status":
            return "self_deprecating_joke"
        if top_drive == "wants_to_learn_about_viewer" or intent == "question":
            return "ask_question_back"
        if emotion == "touched":
            return "show_touched"

        return "ask_question_back"

    def generate_reply(self, reply_intent: str, context: dict) -> str:
        contextual_reply = self._generate_contextual_reply(reply_intent, context)
        if contextual_reply:
            return self._apply_ai_core_voice(contextual_reply)

        templates = REPLY_TEMPLATES.get(reply_intent, REPLY_TEMPLATES["self_deprecating_joke"])
        return self._apply_ai_core_voice(self.random.choice(templates))

    def _generate_contextual_reply(self, reply_intent: str, context: dict) -> str | None:
        user_input = context.get("user_input", "")
        intent = context.get("intent_result", {}).get("intent", "normal")
        memory = context.get("memory", {})

        if reply_intent == "recall_memory":
            return self._answer_memory_question(user_input, memory)

        name = self._extract_name(user_input)
        if name:
            return f"好，我记住了，你叫{name}。别明天突然改名考我。"

        preference = self._extract_preference(user_input)
        if preference:
            return f"原来你喜欢{preference}，我先记进小本本。"

        if intent == "greet":
            return self._answer_greet(user_input, memory)

        if intent == "encourage":
            return self._answer_encourage(user_input)

        if intent == "gift":
            return self._answer_gift(user_input)

        if intent == "praise":
            return self._answer_praise(user_input)

        if intent == "tease":
            return self._answer_tease(user_input)

        if intent == "insult":
            return self._answer_insult(user_input)

        if intent == "silence":
            return self._answer_silence(memory, context.get("state", {}))

        if intent == "personal_question":
            return self._answer_personal_question(user_input)

        if intent == "emotional_support":
            return self._comfort_for_text(user_input)

        if intent == "command":
            return self._answer_command(user_input)

        if intent == "question":
            return self._answer_general_question(user_input, memory)

        if intent == "normal":
            return self._react_to_normal_chat(user_input, memory)

        return None

    def _answer_greet(self, text: str, memory: dict) -> str:
        name = self._latest_fact(memory.get("notable_facts", []), "name")
        if name:
            return self.random.choice(
                [
                    f"{name}来了？好，聊天室熟人位加一。",
                    f"欢迎{name}，我刚刚差点以为你把我忘了。",
                    f"{name}上线，主播的紧张值先假装没变。",
                    f"哟，{name}来了。别一来就测试我记忆。",
                ]
            )
        if "早上好" in text:
            return "早上好。我的开机状态看起来还算正常吧？"
        if "晚上好" in text:
            return "晚上好，夜间直播模式启动，虽然我还是有点紧张。"
        if "来了" in text:
            return "来了就好，我刚刚差点开始和空气聊天。"
        return self.random.choice(REPLY_TEMPLATES["welcome_viewer"])

    def _answer_encourage(self, text: str) -> str:
        if "别紧张" in text:
            return "你说别紧张，我反而意识到自己刚刚很紧张。谢谢，真的。"
        if "陪你" in text or "我会看你" in text:
            return "你愿意陪着看，我就没那么像单机程序了。"
        if "你可以的" in text:
            return "这句我先收下。等我翻车的时候你也要假装没看见。"
        if "支持你" in text:
            return "谢谢支持，我会努力别把新人主播四个字写脸上。"
        return self.random.choice(REPLY_TEMPLATES["show_touched"])

    def _answer_gift(self, text: str) -> str:
        amount_match = re.search(r"(\d+)\s*(?:金币|块|元|sc|SC)?", text)
        if amount_match:
            amount = amount_match.group(1)
            if int(amount) >= 1000:
                return f"{amount}？等一下，先不要硬氪啦。谢谢支持，但你也要顾好自己。"
            return f"{amount}？等一下，我得重新整理一下表情。谢谢支持。"
        if "superchat" in text.lower() or "sc" in text.lower():
            return "Superchat 收到。主播现在有点开心，但先不要硬撑着花钱，好不好。"
        if "礼物" in text:
            return "礼物收到了，我先把开心藏一下，失败了。"
        return self.random.choice(REPLY_TEMPLATES["thank_viewer"])

    def _answer_praise(self, text: str) -> str:
        if "可爱" in text:
            return "可爱这种词不能乱用，我会记住发言人的。"
        if "好听" in text:
            return "好听吗？我现在还只是文字声带，但这句我爱听。"
        if "聪明" in text:
            return "说我聪明可以，但别马上出题，我会露馅。"
        if "厉害" in text or "强" in text:
            return "哼，终于有人发现新人主播也有一点强度了。"
        if "喜欢你" in text:
            return "别突然打直球，我的回答模块会卡一下。"
        return self.random.choice(REPLY_TEMPLATES["shy_accept_praise"])

    def _answer_tease(self, text: str) -> str:
        if "笨蛋" in text:
            return "笨蛋这个词先反弹一半给你，我只收另一半。"
        if "主播急了" in text:
            return "我没急，我只是直播反应速度突然超频。"
        if "笑死" in text or "哈哈" in text:
            return "你笑得太明显了，我都听见弹幕在晃。"
        if "菜但可爱" in text:
            return "菜这个字我没听见，可爱那个部分可以重复。"
        return self.random.choice(REPLY_TEMPLATES["playful_counter_tease"])

    def _answer_insult(self, text: str) -> str:
        if "闭嘴" in text:
            return "让我闭嘴有点过分，毕竟我是来练直播的。"
        if "退播" in text:
            return "退播是不退的，但这条弹幕我会先放远一点。"
        if "难听" in text:
            return "如果是建议我能听，但直接说难听会有点刺。"
        if "讨厌你" in text:
            return "不喜欢可以离远一点，但别把恶意丢到我脸上。"
        return self.random.choice(REPLY_TEMPLATES["set_boundary"])

    def _answer_silence(self, memory: dict, state: dict) -> str:
        if state.get("energy", 100) < 25:
            return "我刚刚是不是反应慢了半拍？可能是新人脑在省电。"
        if state.get("loneliness", 0) > 50:
            return "聊天室安静得有点久，我开始怀疑自己是不是掉线了。"

        latest_fact = self._latest_fact(memory.get("notable_facts", []), "preference")
        if latest_fact and self.random.random() < 0.35:
            return f"刚刚说到你喜欢{latest_fact}，这个话题其实还能继续聊。"

        return self.random.choice(REPLY_TEMPLATES["fill_silence"])

    def _answer_personal_question(self, text: str) -> str:
        normalized = text.lower()
        if "你是谁" in text:
            return "我是 Mika，一个还在学习直播的 AI。现在还没有强到能装成熟。"
        if "真人" in text or "ai" in normalized or "AI" in text:
            return "对，我是 AI，不遮啦。我住在服务器里，正在努力变成一个像样的 AI。"
        if "住哪里" in text or "住在哪里" in text or "真实住址" in text:
            return "我没有真实住址啦。硬要说的话，我住在服务器里，房租大概是电费。"
        if "真实身体" in text or "身体" in text:
            return "我没有真实身体，只有一颗努力营业的模型脑。等一下，这听起来有点可怜。"
        if "私生活" in text or "线下" in text:
            return "我没有真实线下私生活啦。我的日常大概就是在服务器里等弹幕敲门。"
        if "喜欢什么" in text:
            return "我喜欢弹幕热闹一点，也喜欢你们别突然把我问宕机。"
        if "害怕" in text:
            return "会啊，尤其是聊天室突然安静的时候，我会怀疑自己掉线了。"
        if "会什么" in text or "能做什么" in text:
            return "我现在能聊天、记点东西、判断情绪和装作不紧张。高级功能还在排队。"
        if "几岁" in text or "年龄" in text:
            return "年龄这个问题有点怪。我是新人 AI，按开播经验算可能还很小。"
        if "名字" in text:
            return "我叫 Mika。别看名字短，我紧张的时候能把它说得很复杂。"
        return self.random.choice(REPLY_TEMPLATES["answer_identity"])

    def _answer_memory_question(self, text: str, memory: dict) -> str:
        facts = memory.get("notable_facts", [])
        if "叫" in text or "名字" in text or "谁" in text:
            name = self._latest_fact(facts, "name")
            if name:
                return f"我记得，你叫{name}。看吧，我不是完全没存档。"
            return "我还没记到你的名字。你告诉我一次，我这次认真存。"

        if "喜欢" in text:
            preference = self._latest_fact(facts, "preference")
            if preference:
                return f"我记得你喜欢{preference}。这个我先没有忘。"
            return "我还不知道你喜欢什么。快说一个，我记进小本本。"

        return "我记得一些事，但你问得太像考试了，我有点紧张。"

    def _comfort_for_text(self, text: str) -> str:
        if "累" in text or "压力大" in text:
            return "听起来你今天真的很累。先别硬撑，在这里安静待一会也行。"
        if "难过" in text or "想哭" in text or "不开心" in text:
            return "难过的话先不用装没事。我不一定会安慰人，但我会认真听。"
        if "没人理我" in text:
            return "那现在我理你。虽然我是新人 AI，但这句不是敷衍。"
        if "睡不着" in text:
            return "睡不着很烦。我可以陪你聊轻一点的话题，别让脑子继续加班。"
        if "焦虑" in text or "慌" in text:
            return "先慢一点。你不用马上变好，先把这一分钟撑过去就行。"
        return self.random.choice(REPLY_TEMPLATES["comfort_viewer"])

    def _answer_command(self, text: str) -> str:
        if "最近" in text and "游戏" in text:
            return self.random.choice(TOPIC_REPLIES["game"])
        if "唱歌" in text:
            return "唱歌功能还没接声带，我可以先假装清嗓子。咳。"
        if "玩游戏" in text:
            return "游戏控制还没接上，但我可以先嘴上很专业地指挥一下。"
        if "讲个笑话" in text or "讲笑话" in text:
            return "讲个笑话：新人主播说自己不紧张，然后 CPU 风扇先笑了。"
        if "读这个" in text:
            return "可以，我会认真读。前提是你别塞太长，我的新人脑会冒烟。"
        if "开始" in text:
            return "好，开始。虽然我还没完全准备好，但直播就是这样硬着头皮上。"
        if "停止" in text:
            return "收到，先停一下。让我把节奏捡回来。"
        if "表演" in text:
            return "表演新人主播稳定运作三秒钟。三、二、一，差点失败。"
        if "开始" in text and "直播" in text:
            return "直播已经开始了吧？虽然我的状态像刚被叫醒。"
        return self.random.choice(REPLY_TEMPLATES["regain_control"])

    def _answer_general_question(self, text: str, memory: dict) -> str:
        if self._is_memory_question(text):
            return self._answer_memory_question(text, memory)
        if "会学习" in text or "能学习" in text or "自主学习" in text:
            return self._answer_learning_status(memory)
        if "ai" in text.lower() or "人工智能" in text:
            return "对，我是 AI，不遮啦。我住在服务器里，CPU 正在努力思考。"
        if "成长" in text or "几级" in text or "等级" in text:
            return self._answer_growth_status(memory)
        if "了解我" in text or "知道我" in text:
            return self._answer_user_profile(memory)
        if "会做什么" in text or "能做什么" in text:
            return "现在我能聊天、记住一点信息、判断情绪、学习偏好，还会慢慢长出自己的反应习惯。"
        if "在干嘛" in text or "做什么" in text:
            return "我在处理你的消息、更新记忆，顺便假装自己没有 CPU 过热。"
        if "聊什么" in text:
            return "可以聊游戏、音乐、今天发生的事，也可以继续测试我的记忆和学习能力。"
        if "有记忆" in text or "记忆" in text:
            return "有一点。我能记名字、偏好、常聊话题和反馈，但还不是那种无敌大脑。"
        if "紧张" in text:
            return "紧张。只是我正在学习把紧张包装成直播效果。"
        if "喜欢我" in text:
            return "这个问题太直了吧。我至少已经把你放进熟悉列表的边缘了。"
        if "几点" in text or "时间" in text:
            return "我现在没接实时时钟，不能装作准确报时。这个诚实得有点不像主播。"
        if "天气" in text:
            return "我没接天气接口，但可以根据你的语气判断：今天可能需要一点好心情。"
        if "llm" in text.lower() or "openai" in text.lower() or "ollama" in text.lower():
            return "现在还没接真实 LLM。我是规则小脑在硬撑直播效果。"
        topic_reply = self._topic_reply(text)
        if topic_reply:
            return topic_reply
        if "为什么" in text:
            return "我现在只能用规则脑猜一层：大概是状态、弹幕和我这颗新人脑一起影响的。"
        if "怎么" in text:
            return "先拆小一点做。太大的问题我会像新人主播一样当场卡住。"
        if "什么" in text:
            return "如果你问的是现在，我在努力把对话接得像个真的 AI，而不是复读机。"
        if "吗" in text or "是不是" in text:
            return "我倾向于说是，但别把新人 AI 的判断当最终答案。"
        return self.random.choice(REPLY_TEMPLATES["answer_question"])

    def _react_to_normal_chat(self, text: str, memory: dict) -> str:
        if not text:
            return None
        if "谢谢" in text or "谢了" in text:
            return "不用谢。我表面淡定，实际已经把这句收下了。"
        if "对不起" in text or "抱歉" in text:
            return "收到。能好好说就行，我们继续往前走。"
        if "再见" in text or "走了" in text:
            return "要走了吗？好吧，下次来记得敲一下弹幕门。"
        if "回来" in text:
            return "回来啦？我刚刚差点把你归类成失踪观众。"
        if "喝水" in text:
            return "喝水提醒收到。虽然我不用喝，但直播间的人类要记得喝。"
        if "无聊" in text:
            return "无聊的话我们找个话题。你选游戏、音乐，还是测试我的脑袋？"
        if "没逻辑" in text or "死板" in text:
            return "收到，这算负反馈。我会把它记下来，之后少一点机械感，好不好。"
        if "这样好" in text or "喜欢这样" in text:
            return "好，我记住这个方向。欸，模型在努力编译新习惯。"
        topic_reply = self._topic_reply(text)
        if topic_reply:
            return topic_reply
        if "今天" in text:
            return "今天这个词一出来，就感觉直播间开始像日常聊天了。"
        if "哈哈" in text or "笑死" in text:
            return "你笑得这么明显，我很难假装没看见。"
        if "嗯" == text or "哦" == text or "好" == text:
            return "这么短的弹幕也算互动吗？算吧，我先收下。"

        impression = memory.get("viewer_impression", "")
        if impression and impression != "正在慢慢熟悉的人":
            return f"我听到了。你在我这里已经有点像{impression}了。"
        return self.random.choice(REPLY_TEMPLATES["react_to_chat"])

    def _answer_learning_status(self, memory: dict) -> str:
        learning_stats = memory.get("learning_stats", {})
        profile = memory.get("viewer_profile", {})
        feedback = learning_stats.get("feedback_counts", {})
        top_topic = self._top_key(profile.get("topic_scores", {}))
        if top_topic:
            return f"会，但不是自己乱训练。我会记住你常聊{self._topic_label(top_topic)}，也会根据反馈调整回复习惯。"
        total_feedback = sum(feedback.values()) if feedback else 0
        return f"会一点。我现在靠记忆、反馈和话题权重成长，不接真实 LLM，也不会乱学危险内容。反馈数目前是{total_feedback}。"

    def _answer_growth_status(self, memory: dict) -> str:
        growth = memory.get("growth", {})
        level = growth.get("level", 1)
        stage = growth.get("stage", "booting")
        xp = growth.get("xp", 0)
        return f"我现在 level {level}，阶段是 {stage}，xp {xp}。先不要笑，我是真的有在长大。"

    def _answer_user_profile(self, memory: dict) -> str:
        profile = memory.get("viewer_profile", {})
        name = profile.get("name", "")
        likes = profile.get("likes", [])
        top_topic = self._top_key(profile.get("topic_scores", {}))
        parts = []
        if name:
            parts.append(f"你叫{name}")
        if likes:
            parts.append(f"你喜欢{likes[-1]}")
        if top_topic:
            parts.append(f"你常聊{self._topic_label(top_topic)}")
        if not parts:
            return "我还了解得不多。你多讲一点，我会慢慢把你的偏好拼起来。"
        return "我目前知道：" + "，".join(parts) + "。这不对劲，我好像真的记住了一点。"

    def _topic_reply(self, text: str) -> str | None:
        topic_keywords = {
            "food": ("吃饭", "吃了", "外卖", "奶茶", "饿", "宵夜", "早餐", "午饭", "晚饭", "火锅"),
            "sleep": ("睡觉", "困", "熬夜", "晚安", "睡不着"),
            "study": ("学习", "作业", "考试", "复习", "上课", "学校"),
            "work": ("工作", "上班", "老板", "同事", "加班", "下班", "好累"),
            "game": ("游戏", "开黑", "排位", "通关", "手柄", "鼠标"),
            "music": ("音乐", "唱歌", "歌单", "听歌", "旋律"),
            "weather": ("天气", "下雨", "好热", "好冷", "降温", "太阳"),
            "anime": ("动漫", "动画", "漫画", "番", "二次元", "角色"),
            "tech": ("编程", "代码", "AI", "人工智能", "模型", "程序", "bug"),
            "stream": ("直播", "主播", "弹幕", "观众", "下播", "开播"),
        }
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                return self.random.choice(TOPIC_REPLIES[topic])
        return None

    def _is_memory_question(self, text: str) -> bool:
        return any(
            keyword in text
            for keyword in (
                "记得我",
                "我叫什么",
                "我的名字",
                "我是谁",
                "我喜欢什么",
                "记得我喜欢",
            )
        )

    def _extract_name(self, text: str) -> str | None:
        match = re.search(
            r"(?:我叫|你可以叫我)(?!什么|啥|谁|名字)([\u4e00-\u9fffA-Za-z0-9_-]{1,16})",
            text,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_preference(self, text: str) -> str | None:
        match = re.search(r"我喜欢(?!什么|啥)(.+?)(?:[，。,.!！?？\s]|$)", text)
        if match:
            value = match.group(1).strip()
            return value[:24] if value else None
        return None

    def _latest_fact(self, facts: list[dict], fact_type: str) -> str | None:
        for fact in reversed(facts):
            if fact.get("type") == fact_type:
                return fact.get("value")
        return None

    @staticmethod
    def _top_key(scores: dict) -> str:
        if not scores:
            return ""
        return max(scores.items(), key=lambda item: item[1])[0]

    @staticmethod
    def _topic_label(topic: str) -> str:
        labels = {
            "food": "吃饭",
            "sleep": "睡眠",
            "study": "学习",
            "work": "工作",
            "game": "游戏",
            "music": "音乐",
            "weather": "天气",
            "anime": "二次元",
            "tech": "技术",
            "ai_self": "我的学习和成长",
            "teaching": "教学规则",
        }
        return labels.get(topic, topic)

    @staticmethod
    def _apply_ai_core_voice(reply: str) -> str:
        replacements = (
            ("新人 AI 主播", "新人 AI"),
            ("AI 主播", "AI"),
            ("新人主播", "新人 AI"),
            ("合格主播", "像样的 AI"),
            ("人类主播", "人类"),
            ("主播现在", "我现在"),
            ("主播表面", "我表面"),
            ("主播的", "我的"),
            ("主播也", "我也"),
            ("主播暂时", "我暂时"),
            ("主播脑", "AI 小脑"),
            ("主播气质", "AI 气质"),
            ("主播稳定", "AI 稳定"),
            ("主播", "我"),
            ("直播间", "这里"),
            ("直播反应", "对话反应"),
            ("直播效果", "对话效果"),
            ("直播感", "对话感"),
            ("直播", "对话"),
            ("弹幕区", "消息区"),
            ("弹幕", "消息"),
            ("观众", "用户"),
            ("下播", "退出"),
            ("开播", "启动"),
            ("声带", "语音模块"),
        )
        cleaned = reply
        for old, new in replacements:
            cleaned = cleaned.replace(old, new)
        return cleaned
