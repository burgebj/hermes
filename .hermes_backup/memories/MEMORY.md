用户使用 interview skill 管理招聘流程。文件路径含空格需用引号。PDF 读取用 pypdf。日期用 `date "+%Y-%m-%d"` 确认。简历目录：/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/简历；候选人档案：.../候选人档案/；面试时间表：.../面试时间表.md；入职时间表：.../入职时间表.md。
§
User requires all model calls to use max thinking/reasoning effort globally. Set agent.reasoning_effort: xhigh and delegation.reasoning_effort: xhigh in config.yaml. Note: "xhigh" is the highest available effort level — "max" is not a valid config value.
§
面试管理技能已创建，包含5个核心功能：简历归档、简历摘要、面试时间表、入职时间表、候选人档案。文件路径约定：简历目录为 /mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/简历，下载目录为 /mnt/c/Users/liuch/Downloads，档案目录为 /mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/候选人档案，时间表为 .../招聘/面试时间表.md，入职表为 .../招聘/入职时间表.md。
§
在 vLLM 0.20.0 中，即使配置了 --reasoning-parser deepseek_v4，Hermes 模型也无法通过任何已知参数格式（包括 extra_body.chat_template_kwargs、reasoning_effort、extra_body.reasoning、extra_body.thinking.type）激活思考模式，所有测试均返回 reasoning: null。
§
用户要求技能库更新为类级别技能，每个技能包含丰富的SKILL.md和references/目录，而不是扁平的一会话一技能的条目列表。
§
用户确认在Hermes CLI中启用了show_reasoning: true后，看到了Reasoning内容，但该内容实际上是模型在content中输出的普通CoT（chain-of-thought），并非DeepSeek thinking mode的reasoning_content字段。API返回的response中只有'323'（2个token），没有reasoning_content字段，说明thinking mode并未真正激活。
§
技能收集的目标是构建一个类级别指令和经验知识的库，每个技能应是宽泛的伞状技能并带有标记的子部分，而不是多个狭窄的技能。
§
Hermes 的 Curator 后台进程在 2026-05-06 06:15 UTC 自动运行，将 remote-70-88 和 remote-70-66 技能吸收进 remote-deploy umbrella 技能，随后将 remote-deploy 作为过时技能删除，导致三个技能全部消失。
§
用户激活了 remote-70-88 技能，该技能用于远程操作 GPU 服务器 10.10.70.88，包括 SSH 连接、CUDA/nvcc 安装、NCCL 版本管理、编译 nccl-tests 和运行带宽测试。
§
用户要求基于 test_deepseekv4_throughput_cache.py 创建 test_deepseekv4_speculative.py，添加 --speculative_config 参数，日志名为 dsv4_speculative.log，运行参数相同，文件需创建在远程服务器 10.10.70.88 上。
§
用户调用了 interview 技能，该技能用于管理 WarpDriveAI 的面试日程、候选人、简历和入职时间线。
§
用户通过 Hermes 在远程服务器 10.10.70.88 上创建了文件 /home/jianliu/work/bandwidth_test/scripts/test_deepseekv4_speculative.py，用于测试 DeepSeek v4 推测解码，支持 --speculative-config 参数和 SpeculativeThroughputTester 类。
§
用户 jianliu 的密码是 !QAZ2wsx，对应的服务器 IP 为 10.10.70.93、10.10.70.95、10.10.70.96。
§
远程服务器 10.10.70.93 (oem93)、10.10.70.95 (oem95)、10.10.70.96 (oem96) 已配置免密码 SSH 密钥认证，用户 jianliu 可通过 ssh jianliu@<IP> 直接登录，旧密码 !QAZ2wsx 不再需要。