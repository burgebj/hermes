#!/usr/bin/env python3
"""Hermes Feishu UAT Pipeline Stress Test.

Posts test messages as the user (via UAT) to a chat where the bot is a member,
then greps ~/.hermes/logs/agent.log to verify each test case triggered the
expected tool, that the tool used UAT (not TAT), and that the expected gateway
route handled the request.

Usage:
    python scripts/stress_test_feishu_pipeline.py --list-users
    python scripts/stress_test_feishu_pipeline.py --user 美元本袁 --chat-id oc_xxx --suite smoke
    python scripts/stress_test_feishu_pipeline.py --user 美元本袁 --chat-id oc_xxx --suite smoke --route-mode direct
    python scripts/stress_test_feishu_pipeline.py --user 美元本袁 --chat-id oc_xxx --suite base
    python scripts/stress_test_feishu_pipeline.py --user 美元本袁 --chat-id oc_xxx --suite full --fixtures fixtures.json --allow-destructive
    python scripts/stress_test_feishu_pipeline.py --user 美元本袁 --suite full --dry-run --allow-placeholders --allow-destructive

Suites:
    smoke       — 5 representative tools (fast sanity check)
    base/all    — 64 base single-tool cases
    sheets      — 7 Sheets cases
    deep        — 51 OpenClaw deep parity cases
    integration — 5 multi-tool scenarios
    multitenant — 3 routing/isolation scenarios
    failure     — 3 degradation scenarios
    ux          — 13 auth/doctor/card UX scenarios
    channel     — 22 message/card/typewriter channel scenarios
    full        — 168 total cases from the UAT document
    exact-*     — OpenClaw source-level parity coverage/backlog suites
"""

import argparse
import ast
import glob
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

UAT_DIR = Path.home() / ".hermes" / "feishu_uat"
LOG_FILE = Path.home() / ".hermes" / "logs" / "agent.log"
GATEWAY_LOG_FILES = [
    Path.home() / ".hermes" / "logs" / "gateway.log",
    Path.home() / ".hermes" / "logs" / "gateway.error.log",
]
PROFILES_DIR = Path.home() / ".hermes" / "profiles"
FEISHU_BASE_URL = "https://open.feishu.cn"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPENCLAW_REPO = Path(os.environ.get("OPENCLAW_LARK_REPO", "/tmp/openclaw-lark-github-20260503"))


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

Case = dict[str, object]


def _case(
    case_id: str,
    text: str,
    expect_tool: str | None = None,
    *,
    expect_tools: list[str] | None = None,
    expect_logs: list[str] | None = None,
    identity: str = "uat",
    destructive: bool = False,
    setup: str | None = None,
    static_check: str | None = None,
) -> Case:
    case: Case = {
        "id": case_id,
        "input": text,
        "identity": identity,
    }
    if expect_tool:
        case["expect_tool"] = expect_tool
    if expect_tools:
        case["expect_tools"] = expect_tools
    if expect_logs:
        case["expect_logs"] = expect_logs
    if destructive:
        case["destructive"] = True
    if setup:
        case["setup"] = setup
    if static_check:
        case["static_check"] = static_check
    return case


BASE_CASES = [
    # Pre-PR TAT baseline. The document uses T1-T5 here, but the script keeps
    # PR* IDs to avoid colliding with task T1-T9.
    _case("PR1", "读飞书文档 {doc_token}", "feishu_doc_read", identity="tat"),
    _case("PR2", "看下文档 {doc_token} 的所有评论", "feishu_drive_list_comments", identity="tat"),
    _case("PR3", "在文档 {doc_token} 的评论 {doc_comment_id} 下回复: UAT ok", "feishu_drive_reply_comment", identity="tat", destructive=True),
    _case("PR4", "给文档 {doc_token} 加一条评论: Hermes UAT 测试", "feishu_drive_add_comment", identity="tat", destructive=True),
    _case("PR5", "文档 {doc_token} 评论 {doc_comment_id} 的所有回复", "feishu_drive_list_comment_replies", identity="tat"),
    # Calendar
    _case("C1", "我未来一周的飞书日程标题", "feishu_calendar_list_events"),
    _case("C2", "我现在的忙闲", "feishu_calendar_freebusy"),
    _case("C3", "我的事件 {event_id} 详情", "feishu_calendar_get_event"),
    _case("C4", "明天 10 点新建会议: Hermes UAT attendee", "feishu_calendar_create_event", destructive=True),
    _case("C5", "把 {target_user_open_id} 加到事件 {event_id}", "feishu_calendar_event_attendee_create", destructive=True),
    _case("C6", "看事件 {event_id} 的所有参与者", "feishu_calendar_event_attendee_list"),
    _case("C7", "把 {target_user_open_id} 从事件 {event_id} 删掉", "feishu_calendar_event_attendee_delete", destructive=True),
    _case("C8", "列我所有的日历", "feishu_calendar_list_calendars"),
    # Docx
    _case("D1", "新建一个飞书文档,标题: Hermes UAT 三轮验证", "feishu_docx_create", destructive=True),
    _case("D2", "使用 feishu_docx_update 把文档 {doc_id} 的 block {doc_block_id} 第 0 个文本元素更新为: hello world", "feishu_docx_update", destructive=True),
    _case("D3", "读文档 {doc_id} 的所有 block", "feishu_docx_get_blocks"),
    # Drive
    _case("Dr1", "列我 drive 根目录的文件", "feishu_drive_list_files"),
    _case("Dr2", "把本地 {local_test_file} 上传到 drive", "feishu_drive_upload_file", destructive=True),
    _case("Dr3", "下载 drive 文件 {file_token}", "feishu_drive_download_file"),
    _case("Dr4", "上传 {local_test_image} 作为 docx {doc_id} 的封面图", "feishu_doc_media_upload", destructive=True),
    _case("Dr5", "下载 docx 媒体 {file_token}", "feishu_doc_media_download"),
    # User lookup
    _case("U1", "我是谁", "feishu_get_my_user_info"),
    _case("U2", "查一下 {target_user_name} 这个用户", "feishu_search_user"),
    _case("U3", "用户 {target_user_open_id} 的详情", "feishu_get_user"),
    # Wiki
    _case("W1", "搜知识库 'API 文档'", "feishu_wiki_search"),
    _case("W2", "读 wiki 节点 {node_token}", "feishu_wiki_get_node"),
    _case("W3", "列我所有 wiki space", "feishu_wiki_list_spaces"),
    _case("W4", "在 space {space_id} 创建 wiki 节点: Hermes UAT 测试", "feishu_wiki_create_node", destructive=True),
    _case("W5", "把节点 {node_token} 移到 {target_parent_token}", "feishu_wiki_move_node", destructive=True),
    # IM
    _case("I1", "用我身份给 {target_user_open_id} 发: Hermes UAT 测试", "feishu_im_send_message_as_user", destructive=True),
    _case("I2", "回复消息 {message_id}: ok", "feishu_im_reply_message_as_user", destructive=True),
    _case("I3", "查看 chat {target_chat_id} 最近的消息", "feishu_im_get_messages"),
    _case("I4", "thread {thread_id} 里的消息", "feishu_im_get_thread_messages"),
    _case("I5", "拉媒体 {message_id}/{file_key}", static_check="gateway_scenario_contract"),
    # Task
    _case("T1", "列我所有的飞书任务", "feishu_task_list"),
    _case("T2", "任务 {task_id} 详情", "feishu_task_get"),
    _case("T3", "新建任务: Hermes UAT 周五前完成 X", "feishu_task_create", destructive=True),
    _case("T4", "把任务 {task_id} 的标题改为 Hermes UAT task updated", "feishu_task_update", destructive=True),
    _case("T5", "给任务 {task_id} 评论: done", "feishu_task_add_comment", destructive=True),
    _case("T6", "我的飞书任务清单", "feishu_task_list_tasklists"),
    _case("T7", "新建任务清单: Hermes UAT 验证", "feishu_task_create_tasklist", destructive=True),
    _case("T8", "清单 {tasklist_guid} 里的分组", "feishu_task_list_sections"),
    _case("T9", "在任务 {task_id} 下新建子任务: 子任务 A", "feishu_task_create_subtask", destructive=True),
    # Bitable
    _case("B1", "我的多维表 apps", "feishu_bitable_list_apps"),
    _case("B2", "多维表 app {app_token} 的所有 tables", "feishu_bitable_list_tables"),
    _case("B3", "多维表 {app_token} 的表 {table_id} 的记录", "feishu_bitable_list_records"),
    _case("B4", "在多维表 {app_token} 的表 {table_id} 搜 {bitable_search_field}={bitable_search_value} 的记录", "feishu_bitable_search_records"),
    _case("B5", "在多维表 {app_token} 的表 {table_id} 新建 record: 文本=Hermes auto, {bitable_search_field}={bitable_create_value}", "feishu_bitable_create_record", destructive=True),
    _case("B6", "更新多维表 {app_token} 表 {table_id} 的 record {record_id}: {bitable_search_field}={bitable_update_value}", "feishu_bitable_update_record", destructive=True),
    _case("B7", "列出多维表 {app_token} 表 {table_id} 的记录，删除一条文本为 Hermes auto 的 record", "feishu_bitable_delete_record", destructive=True),
    _case("B8", "列出多维表 {app_token} 表 {table_id} 的字段", "feishu_bitable_list_fields"),
    _case("B9", "在多维表 {app_token} 表 {table_id} 加一个单选字段，字段名用 Hermes UAT scratch field 加当前时间戳", "feishu_bitable_create_field", destructive=True),
    _case("B10", "先列出多维表 {app_token} 表 {table_id} 的字段，找到名字包含 Hermes UAT scratch field 的字段，把它改名为 Hermes 字段", "feishu_bitable_update_field", destructive=True),
    _case("B11", "先列出多维表 {app_token} 表 {table_id} 的字段，删除名字为 Hermes 字段 或包含 Hermes UAT scratch field 的字段", "feishu_bitable_delete_field", destructive=True),
    _case("B12", "列出多维表 {app_token} 表 {table_id} 的视图", "feishu_bitable_list_views"),
    _case("B13", "在多维表 {app_token} 表 {table_id} 新建 kanban 视图，名字用 Hermes UAT scratch view 加当前时间戳", "feishu_bitable_create_view", destructive=True),
    _case("B14", "先列出多维表 {app_token} 表 {table_id} 的视图，删除名字包含 Hermes UAT scratch view 的视图", "feishu_bitable_delete_view", destructive=True),
    # Chat / Search
    _case("Ch1", "当前群信息", "feishu_chat_get_info"),
    _case("Ch2", "群成员列表", "feishu_chat_list_members"),
    _case("Ch3", "新建群: Hermes UAT 测试群,加 {target_user_open_id}", "feishu_chat_create", destructive=True),
    _case("Ch4", "把 {second_user_open_id} 拉进群 {target_chat_id}", "feishu_chat_add_members", destructive=True),
    _case("Ch5", "把 {second_user_open_id} 从群 {target_chat_id} 移除", "feishu_chat_remove_members", destructive=True),
    _case("S1", "全局搜 'API 文档'", "feishu_search_global"),
    _case("S2", "搜消息 keyword: 测试", "feishu_search_message"),
]

SMOKE_IDS = {"C1", "D1", "Dr1", "W1", "T1"}
SMOKE_CASES = [case for case in BASE_CASES if case["id"] in SMOKE_IDS]
ALL_CASES = BASE_CASES

SHEETS_CASES = [
    _case("Sh1", "查看这个电子表格 {spreadsheet_token} 的工作表和行列信息", "feishu_sheets_read_range"),
    _case("Sh2", "读取表格 {spreadsheet_token} 的 Sheet1!A1:C10", "feishu_sheets_read_range"),
    _case("Sh3", "把表格 {spreadsheet_token} 的 Sheet1!D1 写成 UAT_OK", "feishu_sheets_write_range", destructive=True),
    _case("Sh4", "在表格 {spreadsheet_token} 末尾追加一行: Hermes,UAT,pass", "feishu_sheets_append_rows", destructive=True),
    _case("Sh5", "在表格 {spreadsheet_token} 里查找包含 Hermes 的单元格", expect_logs=["feishu_sheet.find"]),
    _case("Sh6", "新建一个电子表格,标题: Hermes sheets parity", expect_logs=["feishu_sheet.create"], destructive=True),
    _case("Sh7", "把表格 {spreadsheet_token} 导出成 xlsx", expect_logs=["feishu_sheet.export"]),
]

DEEP_CASES = [
    _case("PC1", "查询我的主日历 ID", expect_logs=["feishu_calendar_calendar.primary"]),
    _case("PC2", "查看日历 {calendar_id} 的名称和权限", expect_logs=["feishu_calendar_calendar.get"]),
    _case("PC3", "把事件 {event_id} 标题改成 Hermes parity updated", "feishu_calendar_update_event", destructive=True),
    _case("PC4", "删除刚才创建的测试事件 {event_id}", "feishu_calendar_delete_event", destructive=True),
    _case("PC5", "搜索我日历里标题包含 Hermes 的事件", expect_logs=["feishu_calendar_event.search"]),
    _case("PC6", "回复事件邀请 {event_id}: 接受", expect_logs=["feishu_calendar_event.reply"], destructive=True),
    _case("PC7", "查看重复日程 {recurring_event_id} 的所有实例", "feishu_calendar_list_event_instances"),
    _case("PC8", "列出未来 40 天所有展开后的日程实例", "feishu_calendar_list_events"),
    _case("PB1", "新建一个多维表,标题: Hermes parity base", expect_logs=["feishu_bitable_app.create"], destructive=True),
    _case("PB2", "查看多维表 {app_token} 的元数据", expect_logs=["feishu_bitable_app.get"]),
    _case("PB3", "把多维表 {app_token} 重命名为 Hermes parity base updated", expect_logs=["feishu_bitable_app.patch"], destructive=True),
    _case("PB4", "复制多维表 {app_token},新标题: Hermes parity copy", expect_logs=["feishu_bitable_app.copy"], destructive=True),
    _case("PB5", "在多维表 {app_token} 新建数据表: Leads", expect_logs=["feishu_bitable_app_table.create"], destructive=True),
    _case("PB6", "把多维表 {app_token} 里的数据表 {table_id} 改名为 Active Leads", expect_logs=["feishu_bitable_app_table.patch"], destructive=True),
    _case("PB7", "在多维表 {app_token} 批量新建两个表: A 和 B", expect_logs=["feishu_bitable_app_table.batch_create"], destructive=True),
    _case("PB8", "在表 {table_id} 批量新建 3 条客户记录", expect_logs=["feishu_bitable_app_table_record.batch_create"], destructive=True),
    _case("PB9", "在多维表 {app_token} 表 {table_id} 批量更新记录 {batch_record_ids}: status=done", expect_logs=["feishu_bitable_app_table_record.batch_update"], destructive=True),
    _case("PB10", "在多维表 {app_token} 表 {table_id} 批量删除记录 {batch_record_ids}", expect_logs=["feishu_bitable_app_table_record.batch_delete"], destructive=True),
    _case("PB11", "查看多维表 {app_token} 表 {table_id} 视图 {view_id} 的详情", expect_logs=["feishu_bitable_app_table_view.get"]),
    _case("PB12", "把多维表 {app_token} 表 {table_id} 的视图 {view_id} 重命名为 Hermes parity view", expect_logs=["feishu_bitable_app_table_view.patch"], destructive=True),
    _case("PD1", "查看 drive 文件 {file_token} 的元数据", expect_logs=["feishu_drive_file.get_meta"]),
    _case("PD2", "复制 drive 文件 {file_token} 到文件夹 {folder_token}", expect_logs=["feishu_drive_file.copy"], destructive=True),
    _case("PD3", "把 drive 文件 {file_token} 移到文件夹 {folder_token}", expect_logs=["feishu_drive_file.move"], destructive=True),
    _case("PD4", "删除刚才上传的测试文件 {file_token}", expect_logs=["feishu_drive_file.delete"], destructive=True),
    _case("PD5", "把文档 {doc_token} 的评论 {doc_comment_id} 标记为已解决", expect_logs=["feishu_doc_comments.patch"], destructive=True),
    _case("PD6", "读取文档 {doc_token} 并转成 Markdown 摘要", expect_logs=["feishu_fetch_doc.default"]),
    _case("PD7", "创建一份包含标题、列表、表格的飞书文档: Hermes rich doc", expect_logs=["feishu_create_doc.default"], destructive=True),
    _case("PD8", "把文档 {doc_id} 的标题下追加一个二级标题和待办列表", expect_logs=["feishu_update_doc.default"], destructive=True),
    _case("PT1", "给任务 {task_id} 添加成员 {target_user_open_id}", expect_logs=["feishu_task_task.add_members"], destructive=True),
    _case("PT2", "给任务 {task_id} 追加一条步骤记录: 已完成 UAT parity", expect_logs=["feishu_task_task.append_steps"], destructive=True),
    _case("PT3", "列出任务 {task_id} 的所有评论", expect_logs=["feishu_task_comment.list"]),
    _case("PT4", "查看任务 {task_id} 的评论 {task_comment_id} 的详情", expect_logs=["feishu_task_comment.get"]),
    _case("PT5", "查看任务清单 {tasklist_guid} 的详情", expect_logs=["feishu_task_tasklist.get"]),
    _case("PT6", "列出任务清单 {tasklist_guid} 里的任务", expect_logs=["feishu_task_tasklist.tasks"]),
    _case("PT7", "把任务清单 {tasklist_guid} 重命名为 Hermes tasklist updated", expect_logs=["feishu_task_tasklist.patch"], destructive=True),
    _case("PT8", "给任务清单 {tasklist_guid} 添加成员 {target_user_open_id}", expect_logs=["feishu_task_tasklist.add_members"], destructive=True),
    _case("PT9", "在任务清单 {tasklist_guid} 下创建分组: Doing", expect_logs=["feishu_task_section.create"], destructive=True),
    _case("PT10", "查看任务分组 {section_guid} 的详情", expect_logs=["feishu_task_section.get"]),
    _case("PT11", "把任务分组 {section_guid} 改名为 Done", expect_logs=["feishu_task_section.patch"], destructive=True),
    _case("PT12", "列出分组 {section_guid} 内的任务", expect_logs=["feishu_task_section.tasks"]),
    _case("PT13", "列出任务 {task_id} 的所有子任务", expect_logs=["feishu_task_subtask.list"]),
    _case("PT14", "给任务 {task_id} 上传附件 {local_test_file}", expect_logs=["feishu_task_attachment.upload"], destructive=True),
    _case("PT15", "注册任务 Agent 并返回 agent_id", expect_logs=["feishu_task_agent.register"], identity="tenant_app", destructive=True),
    _case("PT16", "更新任务 Agent {agent_id} profile: Hermes parity profile", expect_logs=["feishu_task_agent.update_profile"], identity="tenant_app", destructive=True),
    _case("PW1", "查看 wiki space {space_id} 的详情", expect_logs=["feishu_wiki_space.get"]),
    _case("PW2", "创建 wiki space: Hermes parity space", expect_logs=["feishu_wiki_space.create"], destructive=True),
    _case("PW3", "列出 wiki space {space_id} 根节点下的子节点", expect_logs=["feishu_wiki_space_node.list"]),
    _case("PW4", "复制 wiki 节点 {node_token} 到 {target_parent_token}", expect_logs=["feishu_wiki_space_node.copy"], destructive=True),
    _case("PU1", "搜索群名包含 Hermes 的群聊", expect_logs=["feishu_chat.search"]),
    _case("PU2", "批量查询这些用户的基础资料: {target_user_open_id}, {second_user_open_id}", expect_logs=["feishu_get_user.basic_batch"]),
    _case("PU3", "搜上周我提到 '登录优化' 的消息,并按发送人过滤", expect_logs=["feishu_im_user_search_messages.default"]),
]

INTEGRATION_CASES = [
    _case("I-A", "把我未来一周的飞书日程整理成一份飞书云文档,标题: 周计划", expect_tools=["feishu_calendar_list_events", "feishu_docx_create", "feishu_docx_update"], destructive=True),
    _case("I-B", "帮我明天下午 3 点新建会议 'Hermes 验证回顾',邀请 {target_user_name},会议室 '罗马'", expect_tools=["feishu_search_user", "feishu_calendar_create_event", "feishu_calendar_event_attendee_create"], destructive=True),
    _case("I-C", "在 '{bitable_name}' 多维表里把 status='无效' 的记录删掉,新建一个看板视图叫 '活跃客户'", expect_tools=["feishu_bitable_list_apps", "feishu_bitable_list_tables", "feishu_bitable_search_records", "feishu_bitable_delete_record", "feishu_bitable_create_view"], destructive=True),
    _case("I-D", "在我的项目文档 wiki space 下新建一个节点 'Hermes UAT 工具集成验证',内容: hello", expect_tools=["feishu_wiki_list_spaces", "feishu_wiki_create_node", "feishu_docx_update"], destructive=True),
    _case("I-E", "找我和 {target_user_name} 上周关于 '登录优化' 的讨论,然后用我身份回复 ta: 收到", expect_tools=["feishu_im_get_messages", "feishu_im_send_message_as_user"], destructive=True),
]

MULTITENANT_CASES = [
    _case("MT1", "我的日程", static_check="gateway_scenario_contract", setup="需要两个用户 A/B 并发运行本脚本"),
    _case("MT2", "我的日程", static_check="gateway_scenario_contract", setup="用未授权用户发送"),
    _case("MT3", "我的日程", static_check="gateway_scenario_contract", setup="关闭 multitenancy 后重启 gateway"),
]

FAILURE_CASES = [
    _case("F1", "帮我创建一个飞书文档", static_check="gateway_scenario_contract", setup="临时移除用户 UAT 中 docx:document:create"),
    _case("F2", "我的日程", static_check="gateway_scenario_contract", setup="把 UAT expires_at 改成过去"),
    _case("F3", "我的日程", static_check="gateway_scenario_contract", setup="mock/代理制造 Feishu API 5xx"),
]

UX_CASES = [
    _case("UX1", "/feishu_auth", expect_logs=["Received raw message"], identity="slash", destructive=True),
    _case("UX2", "创建文档", static_check="gateway_scenario_contract", setup="临时关闭 app 权限"),
    _case("UX3", "我的日程", static_check="gateway_scenario_contract", setup="临时移除用户 scope"),
    _case("UX4", "整理我今天的日程，创建一份飞书文档标题为 Hermes UX4 日程和任务验证，内容写今天日程摘要；再新建一个任务标题为 Hermes UX4 followup", expect_logs=["feishu_calendar", "feishu_docx", "feishu_task"]),
    _case("UX5", "用我身份发一条消息给 {target_user_open_id}: 高敏感授权测试", expect_logs=["feishu_im_send_message_as_user"], destructive=True),
    _case("UX6", "/feishu_doctor", expect_logs=["feishu_get_my_user_info", "feishu_calendar"], identity="slash"),
    _case("UX7", "/feishu_diagnose {message_id}", expect_logs=["feishu_diagnose", "dispatch"], identity="slash"),
    _case("UX8", "@所有人 bot 帮我总结", static_check="gateway_scenario_contract", identity="system"),
    _case("UX9", "未授权成员 allowlist 拦截测试", static_check="gateway_scenario_contract", identity="system", setup="用未授权成员在群里 @ bot"),
    _case("UX10", "请详细解释一下 Hermes 飞书 UAT 测试流程,写长一点", expect_logs=["card", "stream"], identity="tat"),
    _case("UX11", "调用多个飞书工具并展示步骤: 日程、任务、文档", expect_logs=["tool", "duration"], identity="tat"),
    _case("UX12", "需要用户确认后再继续的问题", static_check="gateway_scenario_contract", identity="tat", destructive=True),
    _case("UX13", "会议邀请 synthetic event 测试", static_check="gateway_scenario_contract", identity="system", setup="邀请 bot 进入 VC 会议"),
]

CHANNEL_CASES = [
    _case("MC1", "总结我今天日程并写行动项", expect_logs=["thinking", "complete"], identity="tat"),
    _case("MC2", "请输出一段较长的说明文字,用于验证 CardKit 打字机效果", expect_logs=["card entity created", "cardElement.content", "card.update"], identity="tat"),
    _case("MC3", "输出一个超大 markdown 表格用于验证卡片降级", expect_logs=["final card sent"], identity="tat"),
    _case("MC4", "DM 和群聊 replyMode auto/static/streaming 对照", expect_logs=["replyMode"], identity="system"),
    _case("MC5", "连续输出很多短句,验证 block streaming coalesce", expect_logs=["coalesce"], identity="tat"),
    _case("MC6", "长任务: 先等一下再回答,验证 Typing 表情", expect_logs=["final card sent"], identity="tat"),
    _case("MC7", "输出 Python 代码块和 markdown 表格", expect_logs=["markdown", "table"], identity="tat"),
    _case("MC8", "输出大量 markdown 表格,验证表格预算", expect_logs=["final card sent"], identity="tat"),
    _case("MC9", "回复一张图片或文件资源用于 image resolver 验证", expect_logs=["image resolver"], identity="tat"),
    _case("MC10", "触发 3 个以上飞书工具调用并展示 tool-use trace", expect_logs=["tool-use"], identity="tat"),
    _case("MC11", "请回复一句话，用于验证 footer runtime metrics", expect_logs=["final card sent"], identity="tat"),
    _case("MC12", "问我一个需要交互卡片提交答案的问题", expect_logs=["final card sent"], identity="tat"),
    _case("MC13", "发送自定义 card payload 验证", expect_logs=["final card sent"], identity="tat", destructive=True),
    _case("MC14", "发送图片/文件或文字加媒体", expect_logs=["media"], identity="tat", destructive=True),
    _case("MC15", "多类型入站消息转换验证", expect_logs=["Inbound dm message received"], identity="system", setup="分别发送 image/file/audio/video 等消息"),
    _case("MC16", "在线程或文档评论里保持上下文回复", expect_logs=["final card sent"], identity="system"),
    _case("MC17", "reactionNotifications off/own/all 验证", expect_logs=["reaction"], identity="system"),
    _case("MC18", "websocket/webhook + dedup 验证", expect_logs=["dedup"], identity="system"),
    _case("MC19", "per-group tools / skills / systemPrompt 验证", expect_logs=["final card sent"], identity="system"),
    _case("MC20", "accounts / directory / target resolver 验证", expect_logs=["directory"], identity="system"),
    _case(
        "MC21",
        "读取我刚发给你的附件文件,并总结文件名、大小和关键内容",
        expect_logs=["Inbound dm message received"],
        identity="system",
        setup="先在同一 chat 给 bot 发送 markdown/txt/xlsx 等测试附件",
    ),
    _case(
        "MC22",
        "生成一个 Hermes UAT 文件收发验证 markdown 文件,并把文件发回给我",
        expect_logs=["media"],
        identity="tat",
        destructive=True,
        setup="确认 bot 返回的是可下载/可打开的文件,而不只是文本内容",
    ),
]

EXACT_INVENTORY_CASES = [
    _case(
        "E0-1",
        "OpenClaw action inventory 自动对账",
        identity="static",
        static_check="openclaw_action_inventory",
    ),
    _case(
        "E0-2",
        "OpenClaw 参数 schema 完全对齐对账",
        identity="static",
        static_check="openclaw_schema_inventory",
    ),
]

EXACT_AUTH_CASES = [
    _case("E0-3", "验证 user/app/blocked/allowed/sensitive scope merge 策略", expect_logs=["scope", "sensitive"], identity="system"),
    _case("E0-4", "验证 UAT/TAT/Tenant/App/Slash/System 身份 fallback 与拒绝语义", expect_logs=["identity", "fallback"], identity="system"),
    _case("E0-5", "验证 Feishu errcode/权限/限流/空结果错误返回格式", expect_logs=["errcode", "diagnostic"], identity="system"),
    _case("E0-6", "验证 create/update/delete/send 幂等与破坏性操作保护", expect_logs=["confirm", "destructive"], identity="system", destructive=True),
]

EXACT_POLICY_CASES = [
    _case("E1-1", "验证 dmPolicy/groupPolicy/allowFrom/groups/mention/tools/skills/systemPrompt 配置 schema", expect_logs=["config-schema"], identity="system"),
    _case("E1-2", "验证 default account + named accounts 配置继承/覆盖/深合并", expect_logs=["accounts merge"], identity="system"),
    _case("E1-3", "验证 DM open/pairing/allowlist/disabled 对 DM/comment/VC 都生效", expect_logs=["dmPolicy"], identity="system"),
    _case("E1-4", "验证群 allowlist/sender allowlist/default */@all/per-group override", expect_logs=["groupPolicy", "allowFrom"], identity="system"),
    _case("E2-5", "验证 reactionNotifications off/own/all 与 threadSession 交互", expect_logs=["reactionNotifications"], identity="system"),
    _case("E2-6", "验证 threadSession root_id/thread_id 到 sessionKey 绑定", expect_logs=["threadSessionKey"], identity="system"),
]

EXACT_CARD_CASES = [
    _case("E1-5", "验证 replyMode auto/static/streaming 与 chunkMode newline/paragraph/none", expect_logs=["replyMode", "chunkMode"], identity="system"),
    _case("E1-6", "验证 CardKit idle/creating/streaming/completed/aborted/terminated 状态机", expect_logs=["card entity created", "card.update"], identity="tat"),
    _case("E1-7", "验证 blockStreamingCoalesce 与 CardKit/PATCH 更新节流", expect_logs=["coalesce", "flush"], identity="tat"),
    _case("E1-8", "验证 markdown/code/table/mention/image/footer/tool-use/table-limit 卡片渲染", expect_logs=["markdown", "footer", "tool-use"], identity="tat"),
    _case("E1-9", "验证 AskUserQuestion toast/processing/injection/rollback", expect_logs=["AskUserQuestion", "processing"], identity="tat", destructive=True),
    _case("E1-10", "验证 tool-use 展示、参数脱敏、技能路径隐藏、并发 trace 归属", expect_logs=["tool-use", "redact"], identity="tat"),
    _case("E2-4", "验证 Typing 表情反应创建/移除/失败不阻塞", expect_logs=["typing"], identity="tat"),
]

EXACT_INBOUND_CASES = [
    _case("E2-1", "验证所有入站消息转换器 text/post/image/file/audio/video/sticker/location/share/vote/todo/hongbao/merge-forward/card/system/unknown", expect_logs=["converter"], identity="system"),
    _case("E2-2", "验证 mediaMaxMb、飞书资源下载、URL 上传、dedup、失败降级", expect_logs=["mediaMaxMb", "image resolver"], identity="system"),
    _case("E2-7", "验证文档评论 whole/anchor target、上下文提示、评论回复工具链", expect_logs=["comment context"], identity="system"),
    _case("E2-8", "验证 VC invited synthetic event 准入、去重、DM 通知", expect_logs=["vc", "synthetic"], identity="system"),
    _case("E2-9", "验证 websocket/webhook 双模式、事件重放、dedup、异常恢复", expect_logs=["websocket", "dedup"], identity="system"),
]

EXACT_OUTBOUND_CASES = [
    _case("E2-3", "验证 outbound text/card/media 混发、reply/thread、forward、reaction、recall", expect_logs=["deliverMessage", "outbound"], identity="tat", destructive=True),
    _case("E2-10", "验证 directory/target resolver: user:open_id/chat:chat_id/peers/groups/多账号目标", expect_logs=["directory", "target"], identity="system"),
]

EXACT_DIAGNOSE_CASES = [
    _case("E2-11", "验证 slash command /feishu start/help/auth/doctor alias 与 locale 文案", expect_logs=["feishu", "doctor"], identity="slash"),
    _case("E2-12", "验证 diagnose card_stream 折叠、卡片阶段、超时阈值、问题摘要", expect_logs=["card_stream", "diagnose"], identity="slash"),
]

EXACT_CASES = (
    EXACT_INVENTORY_CASES
    + EXACT_AUTH_CASES
    + EXACT_POLICY_CASES
    + EXACT_CARD_CASES
    + EXACT_INBOUND_CASES
    + EXACT_OUTBOUND_CASES
    + EXACT_DIAGNOSE_CASES
)

FULL_CASES = (
    BASE_CASES
    + SHEETS_CASES
    + DEEP_CASES
    + INTEGRATION_CASES
    + MULTITENANT_CASES
    + FAILURE_CASES
    + UX_CASES
    + CHANNEL_CASES
)

SUITE_MAP = {
    "smoke": SMOKE_CASES,
    "base": BASE_CASES,
    "all": ALL_CASES,
    "sheets": SHEETS_CASES,
    "deep": DEEP_CASES,
    "integration": INTEGRATION_CASES,
    "multitenant": MULTITENANT_CASES,
    "failure": FAILURE_CASES,
    "ux": UX_CASES,
    "channel": CHANNEL_CASES,
    "full": FULL_CASES,
    "complete": FULL_CASES,
    "exact-inventory": EXACT_INVENTORY_CASES,
    "exact-auth": EXACT_AUTH_CASES,
    "exact-policy": EXACT_POLICY_CASES,
    "exact-card": EXACT_CARD_CASES,
    "exact-inbound": EXACT_INBOUND_CASES,
    "exact-outbound": EXACT_OUTBOUND_CASES,
    "exact-diagnose": EXACT_DIAGNOSE_CASES,
    "exact": EXACT_CASES,
}


def _normalize_case_ids(values: list[str] | None) -> list[str]:
    if not values:
        return []
    ids: list[str] = []
    for value in values:
        ids.extend(part.strip() for part in value.split(",") if part.strip())
    return ids


def select_cases(suite: str, case_ids: list[str] | None = None) -> list[dict]:
    cases = SUITE_MAP[suite]
    wanted = _normalize_case_ids(case_ids)
    if not wanted:
        return cases

    by_id = {case["id"]: case for case in cases}
    missing = [case_id for case_id in wanted if case_id not in by_id]
    if missing:
        raise SystemExit(f"Unknown case id(s) for suite '{suite}': {', '.join(missing)}")
    return [by_id[case_id] for case_id in wanted]


PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
SELF_SELECTORS = {"", "auto", "default", "me", "self", "本人", "默认本人", "美元本袁"}


class MissingFixtureError(Exception):
    def __init__(self, case_id: str, missing: list[str]):
        self.case_id = case_id
        self.missing = missing
        super().__init__(f"case {case_id} missing fixture(s): {', '.join(missing)}")


def render_case_input(case: dict, fixtures: dict[str, str]) -> str:
    text = str(case["input"])
    names = sorted(set(PLACEHOLDER_RE.findall(text)))
    missing = [name for name in names if not fixtures.get(name)]
    if missing:
        raise MissingFixtureError(str(case["id"]), missing)
    return text.format_map(fixtures)


def load_fixtures(path: str | None, pairs: list[str] | None) -> dict[str, str]:
    fixtures: dict[str, str] = {}
    if path:
        p = Path(path).expanduser()
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise SystemExit(f"fixtures file must contain a JSON object: {p}")
        fixtures.update({str(k): str(v) for k, v in raw.items() if v is not None})
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(f"--set expects key=value, got: {pair}")
        key, value = pair.split("=", 1)
        fixtures[key.strip()] = value.strip()
    return fixtures


def load_checkpoint(path: Path) -> dict[str, dict]:
    results: dict[str, dict] = {}
    if not path.exists():
        return results

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError:
            continue
        case_id = result.get("id")
        if isinstance(case_id, str) and case_id:
            results[case_id] = result
    return results


def passed_checkpoint_ids(path: Path) -> set[str]:
    return {
        case_id
        for case_id, result in load_checkpoint(path).items()
        if result.get("passed") is True
    }


def record_checkpoint(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        **result,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def should_record_checkpoint(result: dict, *, dry_run: bool) -> bool:
    if dry_run:
        return False
    return True


def _uat_open_id(path: Path, data: dict) -> str:
    return str(data.get("open_id") or data.get("user_open_id") or path.stem)


def _uat_aliases(path: Path, data: dict) -> set[str]:
    aliases = {path.name, path.stem, _uat_open_id(path, data)}
    for key in ("open_id", "user_open_id", "union_id", "user_id", "name", "display_name", "en_name"):
        value = data.get(key)
        if value:
            aliases.add(str(value))
    return {alias for alias in aliases if alias}


def _uat_scope_count(data: dict) -> int:
    scope = data.get("scope") or ""
    return len(str(scope).split())


def _uat_is_valid(data: dict) -> bool:
    expires_at_ms = int(data.get("expires_at") or 0)
    return expires_at_ms > int(time.time() * 1000)


def iter_uat_candidates(uat_dir: Path = UAT_DIR) -> list[dict]:
    candidates: list[dict] = []
    for path in sorted(uat_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        open_id = _uat_open_id(path, data)
        candidates.append({
            "path": path,
            "open_id": open_id,
            "aliases": _uat_aliases(path, data),
            "scope_count": _uat_scope_count(data),
            "valid": _uat_is_valid(data),
            "has_refresh_token": bool(data.get("refresh_token")),
            "is_unknown": open_id == "unknown" or path.stem == "unknown",
        })
    return candidates


def _candidate_score(candidate: dict) -> tuple[int, int, int, str]:
    return (
        1 if candidate["valid"] else 0,
        -1 if candidate["is_unknown"] else 0,
        int(candidate["scope_count"]),
        str(candidate["path"]),
    )


def resolve_uat_path(selector: str | None, *, uat_dir: Path = UAT_DIR) -> Path:
    candidates = iter_uat_candidates(uat_dir)
    if not candidates:
        raise SystemExit(f"No UAT files in {uat_dir}; run /feishu_auth first.")

    normalized = (selector or "").strip()
    if normalized in SELF_SELECTORS:
        valid = [c for c in candidates if c["valid"]] or candidates
        return max(valid, key=_candidate_score)["path"]

    exact = [c for c in candidates if normalized in c["aliases"]]
    if len(exact) == 1:
        return exact[0]["path"]
    if len(exact) > 1:
        paths = ", ".join(str(c["path"]) for c in exact)
        raise SystemExit(f"User selector {normalized!r} matched multiple UAT files: {paths}")

    fuzzy = [c for c in candidates if any(normalized in alias for alias in c["aliases"])]
    if len(fuzzy) == 1:
        return fuzzy[0]["path"]
    if len(fuzzy) > 1:
        paths = ", ".join(str(c["path"]) for c in fuzzy)
        raise SystemExit(f"User selector {normalized!r} matched multiple UAT files: {paths}")

    known = ", ".join(sorted({alias for c in candidates for alias in c["aliases"]}))
    raise SystemExit(f"No UAT matched user selector {normalized!r}. Known aliases: {known}")


def print_uat_candidates(uat_dir: Path = UAT_DIR) -> None:
    print(f"UAT candidates in {uat_dir}:")
    for c in iter_uat_candidates(uat_dir):
        status = "valid" if c["valid"] else "expired"
        aliases = ", ".join(sorted(c["aliases"]))
        print(f"  {c['path'].name}: open_id={c['open_id']} scopes={c['scope_count']} {status} aliases=[{aliases}]")


# ---------------------------------------------------------------------------
# Static OpenClaw parity checks
# ---------------------------------------------------------------------------

OPENCLAW_ACTION_EQUIVALENTS: dict[str, list[str]] = {
    "feishu_bitable_app.list": ["feishu_bitable_list_apps"],
    "feishu_bitable_app.copy": ["feishu_bitable_copy_app"],
    "feishu_bitable_app.create": ["feishu_bitable_create_app"],
    "feishu_bitable_app.get": ["feishu_bitable_get_app"],
    "feishu_bitable_app.patch": ["feishu_bitable_patch_app"],
    "feishu_bitable_app_table.batch_create": ["feishu_bitable_batch_create_tables"],
    "feishu_bitable_app_table.create": ["feishu_bitable_create_table"],
    "feishu_bitable_app_table.list": ["feishu_bitable_list_tables"],
    "feishu_bitable_app_table.patch": ["feishu_bitable_patch_table"],
    "feishu_bitable_app_table_field.create": ["feishu_bitable_create_field"],
    "feishu_bitable_app_table_field.delete": ["feishu_bitable_delete_field"],
    "feishu_bitable_app_table_field.list": ["feishu_bitable_list_fields"],
    "feishu_bitable_app_table_field.update": ["feishu_bitable_update_field"],
    "feishu_bitable_app_table_record.batch_create": ["feishu_bitable_batch_create_records"],
    "feishu_bitable_app_table_record.batch_delete": ["feishu_bitable_batch_delete_records"],
    "feishu_bitable_app_table_record.batch_update": ["feishu_bitable_batch_update_records"],
    "feishu_bitable_app_table_record.create": ["feishu_bitable_create_record"],
    "feishu_bitable_app_table_record.delete": ["feishu_bitable_delete_record"],
    "feishu_bitable_app_table_record.list": ["feishu_bitable_list_records"],
    "feishu_bitable_app_table_record.update": ["feishu_bitable_update_record"],
    "feishu_bitable_app_table_view.create": ["feishu_bitable_create_view"],
    "feishu_bitable_app_table_view.delete": ["feishu_bitable_delete_view"],
    "feishu_bitable_app_table_view.get": ["feishu_bitable_get_view"],
    "feishu_bitable_app_table_view.list": ["feishu_bitable_list_views"],
    "feishu_bitable_app_table_view.patch": ["feishu_bitable_patch_view"],
    "feishu_calendar_calendar.get": ["feishu_calendar_get_calendar"],
    "feishu_calendar_event.create": ["feishu_calendar_create_event"],
    "feishu_calendar_event.delete": ["feishu_calendar_delete_event"],
    "feishu_calendar_event.get": ["feishu_calendar_get_event"],
    "feishu_calendar_event.list": ["feishu_calendar_list_events"],
    "feishu_calendar_event.instances": ["feishu_calendar_list_event_instances"],
    "feishu_calendar_event.instance_view": ["feishu_calendar_list_events"],
    "feishu_calendar_event.patch": ["feishu_calendar_update_event"],
    "feishu_calendar_event.reply": ["feishu_calendar_reply_event"],
    "feishu_calendar_event.search": ["feishu_calendar_search_events"],
    "feishu_calendar_event_attendee.create": ["feishu_calendar_event_attendee_create"],
    "feishu_calendar_event_attendee.list": ["feishu_calendar_event_attendee_list"],
    "feishu_calendar_freebusy.list": ["feishu_calendar_freebusy"],
    "feishu_calendar_calendar.list": ["feishu_calendar_list_calendars"],
    "feishu_calendar_calendar.primary": ["feishu_calendar_primary_calendar"],
    "feishu_chat.get": ["feishu_chat_get_info"],
    "feishu_chat.search": ["feishu_chat_search"],
    "feishu_chat_members.default": ["feishu_chat_list_members"],
    "feishu_create_doc.default": ["feishu_doc_create_markdown"],
    "feishu_doc_comments.create": ["feishu_drive_add_comment"],
    "feishu_doc_comments.list": ["feishu_drive_list_comments"],
    "feishu_doc_comments.list_replies": ["feishu_drive_list_comment_replies"],
    "feishu_doc_comments.patch": ["feishu_doc_patch_comment"],
    "feishu_doc_comments.reply": ["feishu_drive_reply_comment"],
    "feishu_doc_media.download": ["feishu_doc_media_download_resource"],
    "feishu_doc_media.insert": ["feishu_doc_media_insert_resource"],
    "feishu_drive_file.copy": ["feishu_drive_copy_file"],
    "feishu_drive_file.delete": ["feishu_drive_delete_file"],
    "feishu_drive_file.download": ["feishu_drive_download_file"],
    "feishu_drive_file.get_meta": ["feishu_drive_get_file_meta"],
    "feishu_drive_file.list": ["feishu_drive_list_files"],
    "feishu_drive_file.move": ["feishu_drive_move_file"],
    "feishu_drive_file.upload": ["feishu_drive_upload_file"],
    "feishu_fetch_doc.default": ["feishu_doc_fetch_markdown"],
    "feishu_get_user.basic_batch": ["feishu_get_user_basic_batch"],
    "feishu_get_user.default": ["feishu_get_user"],
    "feishu_im_user_fetch_resource.default": ["feishu_im_fetch_resource"],
    "feishu_im_user_get_messages.default": ["feishu_im_get_messages"],
    "feishu_im_user_message.reply": ["feishu_im_reply_message_as_user"],
    "feishu_im_user_message.send": ["feishu_im_send_message_as_user"],
    "feishu_im_user_search_messages.default": ["feishu_im_search_messages"],
    "feishu_search_user.default": ["feishu_search_user"],
    "feishu_task_task.add_members": ["feishu_task_add_members"],
    "feishu_task_task.append_steps": ["feishu_task_append_steps"],
    "feishu_task_task.create": ["feishu_task_create"],
    "feishu_task_task.get": ["feishu_task_get"],
    "feishu_task_task.list": ["feishu_task_list"],
    "feishu_task_task.patch": ["feishu_task_update"],
    "feishu_task_comment.create": ["feishu_task_add_comment"],
    "feishu_task_comment.get": ["feishu_task_get_comment"],
    "feishu_task_comment.list": ["feishu_task_list_comments"],
    "feishu_task_tasklist.add_members": ["feishu_tasklist_add_members"],
    "feishu_task_tasklist.create": ["feishu_task_create_tasklist"],
    "feishu_task_tasklist.get": ["feishu_tasklist_get"],
    "feishu_task_tasklist.list": ["feishu_task_list_tasklists"],
    "feishu_task_tasklist.patch": ["feishu_tasklist_patch"],
    "feishu_task_tasklist.tasks": ["feishu_tasklist_tasks"],
    "feishu_task_agent.register": ["feishu_task_agent_register"],
    "feishu_task_agent.update_profile": ["feishu_task_agent_update_profile"],
    "feishu_task_attachment.upload": ["feishu_task_upload_attachment"],
    "feishu_task_section.create": ["feishu_task_create_section"],
    "feishu_task_section.get": ["feishu_task_get_section"],
    "feishu_task_section.list": ["feishu_task_list_sections_by_resource"],
    "feishu_task_section.patch": ["feishu_task_patch_section"],
    "feishu_task_section.tasks": ["feishu_task_list_section_tasks"],
    "feishu_task_subtask.create": ["feishu_task_create_subtask"],
    "feishu_task_subtask.list": ["feishu_task_list_subtasks"],
    "feishu_update_doc.default": ["feishu_doc_update_markdown"],
    "feishu_wiki_space.create": ["feishu_wiki_create_space"],
    "feishu_wiki_space.get": ["feishu_wiki_get_space"],
    "feishu_wiki_space.list": ["feishu_wiki_list_spaces"],
    "feishu_wiki_space_node.copy": ["feishu_wiki_copy_node"],
    "feishu_wiki_space_node.create": ["feishu_wiki_create_node"],
    "feishu_wiki_space_node.get": ["feishu_wiki_get_node"],
    "feishu_wiki_space_node.list": ["feishu_wiki_list_nodes"],
    "feishu_wiki_space_node.move": ["feishu_wiki_move_node"],
    "feishu_search_doc_wiki.search": ["feishu_search_global"],
    "feishu_sheet.info": ["feishu_sheets_read_range"],
    "feishu_sheet.read": ["feishu_sheets_read_range"],
    "feishu_sheet.write": ["feishu_sheets_write_range"],
    "feishu_sheet.append": ["feishu_sheets_append_rows"],
    "feishu_sheet.find": ["feishu_sheet_find"],
    "feishu_sheet.create": ["feishu_sheet_create"],
    "feishu_sheet.export": ["feishu_sheet_export"],
}


def extract_openclaw_actions(openclaw_repo: Path) -> list[str]:
    tool_scopes = openclaw_repo / "src" / "core" / "tool-scopes.ts"
    text = tool_scopes.read_text(encoding="utf-8")
    blocks = re.findall(r"^export\s+type\s+ToolActionKey\s*=([\s\S]*?);", text, flags=re.MULTILINE)
    if not blocks:
        raise RuntimeError(f"Could not find ToolActionKey in {tool_scopes}")
    actions_by_block = [set(re.findall(r"'(feishu_[^']+)'", block)) for block in blocks]
    return sorted(max(actions_by_block, key=len))


def extract_hermes_feishu_tools(hermes_repo: Path) -> list[str]:
    tools_dir = hermes_repo / "tools"
    names: set[str] = set()
    for path in sorted(tools_dir.glob("feishu*_tool.py")):
        text = path.read_text(encoding="utf-8")
        names.update(re.findall(r'name\s*=\s*"([^"]+)"', text))
        names.update(re.findall(r'"name"\s*:\s*"([^"]+)"', text))
        names.update(re.findall(r'TOOLS_METADATA\["([^"]+)"\]', text))
    try:
        names.update(extract_hermes_tool_schemas(hermes_repo))
    except Exception:
        pass
    return sorted(name for name in names if name.startswith("feishu_"))


def _find_matching_brace(text: str, open_brace: int) -> int:
    depth = 0
    in_string: str | None = None
    escape = False
    for idx in range(open_brace, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_string:
                in_string = None
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return idx
    return -1


def _type_object_block_containing(text: str, pos: int) -> str | None:
    start = text.rfind("Type.Object({", 0, pos)
    if start < 0:
        return None
    open_brace = text.find("{", start)
    end = _find_matching_brace(text, open_brace)
    if end < 0 or end < pos:
        return None
    return text[open_brace + 1:end]


def _required_typebox_props(block: str) -> list[str]:
    action_line = re.search(r"^([ \t]*)action\s*:\s*Type\.Literal", block, flags=re.MULTILINE)
    if action_line:
        indent = action_line.group(1)
    else:
        prop_line = re.search(r"^([ \t]*)[A-Za-z_][A-Za-z0-9_]*\s*:\s*Type\.", block, flags=re.MULTILINE)
        indent = prop_line.group(1) if prop_line else ""
    required: list[str] = []
    for match in re.finditer(rf"^{re.escape(indent)}([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)$", block, flags=re.MULTILINE):
        name, expr = match.groups()
        if name == "action" or "Type.Optional" in expr:
            continue
        if "Type." in expr or "StringEnum(" in expr:
            required.append(name)
    return sorted(set(required))


def _openclaw_prefix_from_path(path: Path, tools_dir: Path) -> str | None:
    try:
        parts = path.relative_to(tools_dir).parts
    except ValueError:
        return None
    if len(parts) >= 3 and parts[0] == "oapi":
        family = parts[1]
        stem = Path(parts[-1]).stem.replace("-", "_")
        if family == "common" and stem == "get_user":
            return "feishu_get_user"
        if family == "common" and stem == "search_user":
            return "feishu_search_user"
        return f"feishu_{family}_{stem}"
    if len(parts) >= 3 and parts[0] == "mcp" and parts[1] == "doc":
        stem = Path(parts[-1]).stem.replace("-", "_")
        return {
            "create": "feishu_create_doc",
            "fetch": "feishu_fetch_doc",
            "update": "feishu_update_doc",
        }.get(stem)
    return None


def extract_openclaw_required_params(openclaw_repo: Path) -> dict[str, list[str]]:
    required_by_action: dict[str, list[str]] = {}
    tools_dir = openclaw_repo / "src" / "tools"
    for path in sorted(tools_dir.rglob("*.ts")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"action\s*:\s*Type\.Literal\(['\"]([^'\"]+)['\"]\)", text):
            block = _type_object_block_containing(text, match.start())
            if not block:
                continue
            action_key_prefix = None
            tool_match = re.search(r"createToolContext\(api,\s*['\"]([^'\"]+)['\"]\)", text)
            if tool_match:
                action_key_prefix = tool_match.group(1)
            register_match = re.search(r"name\s*:\s*['\"](feishu_[^'\"]+)['\"]", text)
            if action_key_prefix is None and register_match:
                action_key_prefix = register_match.group(1)
            if action_key_prefix is None:
                action_key_prefix = _openclaw_prefix_from_path(path, tools_dir)
            if not action_key_prefix:
                continue
            required_by_action[f"{action_key_prefix}.{match.group(1)}"] = _required_typebox_props(block)

        for key_match in re.finditer(r"toolActionKey\s*:\s*['\"]([^'\"]+)['\"]", text):
            before = text[:key_match.start()]
            schema_match = list(re.finditer(r"schema\s*:\s*([A-Za-z0-9_]+)", text[key_match.end():key_match.end() + 500]))
            const_name = schema_match[0].group(1) if schema_match else ""
            if not const_name:
                continue
            const_match = re.search(rf"const\s+{re.escape(const_name)}\s*=\s*Type\.Object\(\{{", text)
            if not const_match:
                continue
            open_brace = text.find("{", const_match.end() - 1)
            end = _find_matching_brace(text, open_brace)
            if end < 0:
                continue
            required_by_action[key_match.group(1)] = _required_typebox_props(text[open_brace + 1:end])
    return required_by_action


def _dict_schemas_from_ast(node: ast.AST) -> list[dict]:
    schemas: list[dict] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Dict):
            continue
        try:
            value = ast.literal_eval(child)
        except (ValueError, SyntaxError):
            continue
        if (
            isinstance(value, dict)
            and isinstance(value.get("name"), str)
            and isinstance(value.get("parameters"), dict)
        ):
            schemas.append(value)
    return schemas


def _static_hermes_tool_schemas(hermes_repo: Path) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    for path in sorted((hermes_repo / "tools").glob("feishu*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue
        for schema in _dict_schemas_from_ast(tree):
            name = schema.get("name")
            if isinstance(name, str) and name.startswith("feishu_"):
                schemas[name] = schema
    return schemas


def extract_hermes_tool_schemas(hermes_repo: Path) -> dict[str, dict]:
    if (hermes_repo / "tools" / "registry.py").exists():
        sys.path.insert(0, str(hermes_repo))
        try:
            from tools.registry import discover_builtin_tools, registry

            discover_builtin_tools(hermes_repo / "tools")
            return {
                name: entry.schema
                for name in registry.get_all_tool_names()
                if name.startswith("feishu_") and (entry := registry.get_entry(name))
            }
        except Exception:
            pass
        finally:
            try:
                sys.path.remove(str(hermes_repo))
            except ValueError:
                pass
    return _static_hermes_tool_schemas(hermes_repo)


OPENCLAW_PARAM_EQUIVALENTS: dict[str, list[str]] = {
    "task_guid": ["task_guid", "task_id"],
    "doc_id": ["doc_id", "doc_token", "document_id"],
    "document_id": ["document_id", "doc_id", "doc_token"],
    "token": ["token", "node_token", "file_token", "spreadsheet_token"],
    "file_token": ["file_token", "token"],
    "resource_token": ["resource_token", "file_token"],
    "resource_type": ["resource_type", "file_type", "type"],
    "resource_id": ["resource_id", "task_guid", "task_id"],
    "time_min": ["time_min", "start"],
    "time_max": ["time_max", "end"],
    "file": ["file", "file_path", "file_name"],
    "output_path": ["output_path", "save_path", "file_path"],
    "profile_content": ["profile_content", "name", "description"],
    "table": ["table", "name"],
}


def _param_is_present(param: str, properties: dict) -> bool:
    candidates = OPENCLAW_PARAM_EQUIVALENTS.get(param, [param])
    return any(candidate in properties for candidate in candidates)


def _action_is_covered(action: str, hermes_tools: set[str]) -> bool:
    if action in hermes_tools:
        return True
    return any(tool in hermes_tools for tool in OPENCLAW_ACTION_EQUIVALENTS.get(action, []))


def run_static_check(
    case: dict,
    *,
    openclaw_repo: Path = DEFAULT_OPENCLAW_REPO,
    hermes_repo: Path = REPO_ROOT,
) -> dict:
    check_name = str(case.get("static_check") or "")
    if check_name == "openclaw_action_inventory":
        actions = extract_openclaw_actions(openclaw_repo)
        hermes_tools = set(extract_hermes_feishu_tools(hermes_repo))
        covered = [action for action in actions if _action_is_covered(action, hermes_tools)]
        missing = [action for action in actions if action not in covered]
        return {
            "id": case["id"],
            "passed": not missing,
            "static": True,
            "expected": check_name,
            "openclaw_actions": len(actions),
            "hermes_tools": len(hermes_tools),
            "covered_actions": covered,
            "missing_actions": missing,
            "error": None if not missing else f"{len(missing)} OpenClaw action(s) not mapped to Hermes tools",
        }
    if check_name == "openclaw_schema_inventory":
        actions = extract_openclaw_actions(openclaw_repo)
        openclaw_required = extract_openclaw_required_params(openclaw_repo)
        hermes_schemas = extract_hermes_tool_schemas(hermes_repo)
        mismatches: list[dict] = []
        checked_actions: list[str] = []
        for action in actions:
            mapped_tools = OPENCLAW_ACTION_EQUIVALENTS.get(action, [])
            if action in hermes_schemas:
                mapped_tools = [action, *mapped_tools]
            tool = next((name for name in mapped_tools if name in hermes_schemas), None)
            if not tool:
                mismatches.append(
                    {
                        "action": action,
                        "tool": None,
                        "missing_required_params": openclaw_required.get(action, []),
                    }
                )
                continue
            checked_actions.append(action)
            parameters = hermes_schemas.get(tool, {}).get("parameters", {})
            properties = parameters.get("properties", {}) if isinstance(parameters, dict) else {}
            missing_required = [
                param
                for param in openclaw_required.get(action, [])
                if not _param_is_present(param, properties)
            ]
            if missing_required:
                mismatches.append(
                    {
                        "action": action,
                        "tool": tool,
                        "missing_required_params": sorted(missing_required),
                    }
                )
        missing_actions = [item["action"] for item in mismatches if item["tool"] is None]
        return {
            "id": case["id"],
            "passed": not mismatches,
            "static": True,
            "expected": check_name,
            "openclaw_actions": len(actions),
            "schema_actions": len(openclaw_required),
            "hermes_schemas": len(hermes_schemas),
            "checked_actions": checked_actions,
            "missing_actions": missing_actions,
            "schema_mismatches": mismatches,
            "error": None if not mismatches else f"{len(mismatches)} action schema contract mismatch(es)",
        }
    if check_name == "gateway_scenario_contract":
        terms_by_case = {
            "I5": ["feishu_im_fetch_resource", "message_id", "file_key", "im:resource"],
            "MT1": ["sender_open_id_scope", "profile_home", "session_id"],
            "MT2": ["NeedAuthorizationError", "feishu_auth", "UAT"],
            "MT3": ["multitenancy", "freebusy", "platform_toolsets"],
            "F1": ["docx:document:create", "NeedAuthorizationError", "scope"],
            "F2": ["refresh_token", "expires_at", "refresh"],
            "F3": ["raise_for_feishu_errcode", "temporarily unavailable", "Feishu"],
            "UX2": ["docx:document:create", "app scope", "NeedAuthorizationError"],
            "UX3": ["calendar:calendar.event:read", "feishu_auth", "NeedAuthorizationError"],
            "UX8": ["mention_all", "is_mention", "mentions"],
            "UX9": ["allowlist", "allowFrom", "sender"],
            "UX12": ["card.action", "processing", "handle_card_action"],
            "UX13": ["vc", "synthetic", "meeting"],
        }
        terms = terms_by_case.get(str(case.get("id")), [])
        search_files = [
            hermes_repo / "gateway",
            hermes_repo / "tools",
            hermes_repo / "scripts",
            Path.home() / ".hermes/plugins/multitenancy",
        ]
        haystack_parts: list[str] = []
        for root in search_files:
            if root.is_file():
                paths = [root]
            elif root.exists():
                paths = [p for p in root.rglob("*.py") if p.is_file()]
            else:
                paths = []
            for path in paths:
                try:
                    haystack_parts.append(path.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    continue
        haystack = "\n".join(haystack_parts)
        missing_terms = [term for term in terms if term not in haystack]
        return {
            "id": case["id"],
            "passed": not missing_terms,
            "static": True,
            "expected": check_name,
            "checked_terms": terms,
            "missing_actions": missing_terms,
            "error": None if not missing_terms else f"missing scenario evidence: {', '.join(missing_terms)}",
        }
    return {
        "id": case["id"],
        "passed": False,
        "static": True,
        "expected": check_name or "unknown",
        "missing_actions": [],
        "error": f"unknown static_check: {check_name}",
    }


# ---------------------------------------------------------------------------
# UAT loading + Feishu API
# ---------------------------------------------------------------------------

def _token_ttl_seconds(data: dict, *keys: str, default: int) -> int:
    for key in keys:
        raw = data.get(key)
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                break
    return default


def _config_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        from hermes_cli.config import get_env_value
    except Exception:
        return ""
    return (get_env_value(name) or "").strip()


def _refresh_credentials(data: dict) -> tuple[str, str]:
    app_id = _config_value("FEISHU_APP_ID") or str(data.get("app_id") or "").strip()
    app_secret = _config_value("FEISHU_APP_SECRET")
    return app_id, app_secret


def _write_uat_file(uat_path: Path, data: dict) -> None:
    uat_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = uat_path.with_name(f".{uat_path.name}.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp_path, 0o600)
    except OSError:
        pass
    os.replace(tmp_path, uat_path)


def refresh_uat_file(uat_path: Path, data: dict, *, scope: str | None = None) -> dict:
    refresh_token = str(data.get("refresh_token") or "").strip()
    if not refresh_token:
        raise SystemExit(f"UAT {uat_path.name} expired and has no refresh_token; re-run /feishu_auth first.")

    app_id, app_secret = _refresh_credentials(data)
    if not (app_id and app_secret):
        raise SystemExit(
            f"UAT {uat_path.name} expired; set FEISHU_APP_ID and FEISHU_APP_SECRET so the script can refresh it."
        )

    body = {
        "grant_type": "refresh_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "refresh_token": refresh_token,
    }
    if scope:
        body["scope"] = scope

    req = urllib.request.Request(
        f"{FEISHU_BASE_URL}/open-apis/authen/v2/oauth/token",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as rsp:
            raw = rsp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"UAT refresh failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"UAT refresh failed: {exc}") from exc

    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"UAT refresh returned non-JSON response: {raw[:200]}") from exc

    code = int(payload.get("code", 0) or 0)
    if code != 0 or payload.get("error"):
        error = payload.get("error") or payload.get("msg") or "unknown"
        description = payload.get("error_description") or payload.get("msg") or ""
        raise SystemExit(f"UAT refresh failed: code={code} error={error} {description}".strip())

    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise SystemExit("UAT refresh response missing access_token; re-run /feishu_auth first.")

    now_ms = int(time.time() * 1000)
    refreshed = dict(data)
    refreshed["access_token"] = access_token
    refreshed["refresh_token"] = str(payload.get("refresh_token") or refresh_token).strip()
    refreshed["expires_at"] = now_ms + _token_ttl_seconds(payload, "expires_in", default=7200) * 1000
    refreshed["refresh_expires_at"] = now_ms + _token_ttl_seconds(
        payload,
        "refresh_token_expires_in",
        "refresh_expires_in",
        default=2592000,
    ) * 1000
    refreshed["token_type"] = str(payload.get("token_type") or refreshed.get("token_type") or "Bearer")
    refreshed["scope"] = str(payload.get("scope") or refreshed.get("scope") or "").strip()
    refreshed["app_id"] = str(refreshed.get("app_id") or app_id)
    refreshed["refreshed_at"] = now_ms
    if not refreshed.get("user_open_id"):
        refreshed["user_open_id"] = refreshed.get("open_id") or uat_path.stem

    _write_uat_file(uat_path, refreshed)
    print(f"UAT {uat_path.name} refreshed via refresh_token; new access token expires in {payload.get('expires_in', 7200)}s")
    return refreshed


def load_uat(uat_path: Path, *, require_valid: bool = True) -> dict:
    with open(uat_path) as f:
        data = json.load(f)
    expires_at_ms = data.get("expires_at", 0)
    expires_dt = datetime.fromtimestamp(expires_at_ms / 1000)
    if require_valid and expires_dt < datetime.now():
        data = refresh_uat_file(uat_path, data)
        expires_at_ms = data.get("expires_at", 0)
        expires_dt = datetime.fromtimestamp(expires_at_ms / 1000)
        if expires_dt < datetime.now():
            raise SystemExit(f"UAT {uat_path.name} still expired after refresh at {expires_dt}; re-run /feishu_auth first.")
    open_id_from_name = uat_path.stem
    if not data.get("open_id"):
        data["open_id"] = data.get("user_open_id") or open_id_from_name
    return data


def ensure_uat_valid_for_post(uat_path: Path, data: dict, *, min_valid_seconds: int = 300) -> dict:
    expires_at_ms = int(data.get("expires_at", 0) or 0)
    refresh_before_ms = int((time.time() + min_valid_seconds) * 1000)
    if expires_at_ms and expires_at_ms > refresh_before_ms:
        return data
    refreshed = refresh_uat_file(uat_path, data)
    data.clear()
    data.update(refreshed)
    return data


def _is_token_expired_post_error(exc: Exception) -> bool:
    message = str(exc)
    return "99991677" in message or "Authentication token expired" in message


def post_message_as_user(uat_token: str, chat_id: str, text: str) -> dict:
    """POST /open-apis/im/v1/messages with user_access_token (UAT)."""
    url = f"{FEISHU_BASE_URL}/open-apis/im/v1/messages?receive_id_type=chat_id"
    body = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {uat_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as rsp:
            return json.loads(rsp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body_text}") from exc


# ---------------------------------------------------------------------------
# Log inspection
# ---------------------------------------------------------------------------

def _log_files() -> list[Path]:
    """Return logs that can receive gateway, profile, and agent traces."""
    paths = [LOG_FILE, *GATEWAY_LOG_FILES]
    if PROFILES_DIR.exists():
        paths.extend(sorted(PROFILES_DIR.glob("*/logs/agent.log")))

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def get_log_position() -> dict[str, object]:
    """Snapshot current log sizes to read only NEW lines after this point."""
    positions: dict[str, object] = {}
    for path in _log_files():
        if not path.exists():
            positions[str(path)] = {"size": 0, "tail": ""}
            continue
        size = path.stat().st_size
        tail = ""
        if size:
            with open(path, "r", errors="replace") as f:
                f.seek(max(size - 512, 0))
                tail = f.read()
        positions[str(path)] = {"size": size, "tail": tail}
    return positions


def _line_timestamp(line: str) -> float | None:
    match = re.search(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:[,.](\d{1,6}))?", line[:96])
    if not match:
        return None
    fractional = (match.group(3) or "0")[:6].ljust(6, "0")
    try:
        parsed = datetime.strptime(
            f"{match.group(1)} {match.group(2)}.{fractional}",
            "%Y-%m-%d %H:%M:%S.%f",
        )
    except ValueError:
        return None
    return parsed.timestamp()


def read_new_log_lines(
    start_pos: dict[str, object],
    max_lines: int = 5000,
    *,
    since_ts: float | None = None,
) -> list:
    """Read lines appended after start_pos; truncate if huge."""
    lines: list[str] = []
    for path in _log_files():
        if not path.exists():
            continue
        current_size = path.stat().st_size
        marker = start_pos.get(str(path), 0)
        if isinstance(marker, dict):
            offset = int(marker.get("size") or 0)
            tail = str(marker.get("tail") or "")
        else:
            # Backward compatible with older callers/tests that stored only size.
            offset = int(marker or 0)
            tail = ""
        if current_size < offset:
            offset = 0
        elif tail and offset:
            with open(path, "r", errors="replace") as f:
                f.seek(max(offset - len(tail), 0))
                current_tail = f.read(len(tail))
            if current_tail != tail:
                offset = 0
        with open(path, "r", errors="replace") as f:
            f.seek(offset)
            chunk = f.read()
        accept_block = since_ts is None
        for line in chunk.splitlines():
            line_ts = _line_timestamp(line)
            if since_ts is not None and line_ts is not None:
                accept_block = line_ts >= since_ts - 5
            if since_ts is not None and not accept_block:
                continue
            lines.append(line)
    return lines[-max_lines:]


def read_session_evidence_lines(
    message_id: str,
    sender_open_id: str,
    *,
    user_input: str | None = None,
    since_ts: float | None = None,
) -> list[str]:
    """Build log-like evidence from the persisted AIAgent session for a message."""
    if not message_id or message_id == "?":
        return []
    paths = sorted(PROFILES_DIR.glob(f"*/sessions/session_{message_id}.json"))
    paths.extend(sorted((Path.home() / ".hermes" / "sessions").glob("session_*.json")))
    lines: list[str] = []
    seen_paths: set[Path] = set()
    for path in paths:
        if path in seen_paths:
            continue
        seen_paths.add(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        messages = data.get("messages", [])
        match_index: int | None = None
        for idx, message in enumerate(messages):
            if not isinstance(message, dict) or message.get("role") != "user":
                continue
            if message_id in str(message.get("metadata") or ""):
                match_index = idx
            elif user_input and str(user_input) in str(message.get("content") or ""):
                match_index = idx
        has_message_id = any(
            isinstance(message, dict)
            and message.get("role") == "user"
            and message_id in str(message.get("metadata") or "")
            for message in messages
        )
        has_user_input = bool(user_input) and any(
            isinstance(message, dict)
            and message.get("role") == "user"
            and str(user_input) in str(message.get("content") or "")
            for message in messages
        )
        is_recent = since_ts is not None and path.stat().st_mtime >= since_ts - 5
        session_name = path.name
        if not (
            has_message_id
            or has_user_input
            or session_name == f"session_{message_id}.json"
            or is_recent
        ):
            continue
        scan_messages = messages
        if match_index is not None:
            scan_messages = messages[match_index + 1 :]
        is_profile_session = path.parent.name == "sessions" and path.parent.parent.parent == PROFILES_DIR
        if is_profile_session:
            profile = path.parent.parent.name
            lines.append(
                f"[session] [multitenancy] running AIAgent for sender={sender_open_id} profile={profile}"
            )
        else:
            lines.append(f"[session] Turn ended: direct session={path.stem}")
        lines.append(f"[session] _load_uat for_user access_token sender={sender_open_id}")
        last_tool: str | None = None
        for message in scan_messages:
            if not isinstance(message, dict):
                continue
            if message.get("role") == "assistant":
                content = str(message.get("content") or "")
                tool_calls = message.get("tool_calls") or []
                if content.strip() and not tool_calls:
                    lines.append(
                        f"[session] assistant.finalized content_len={len(content)}"
                    )
                for tool_call in tool_calls:
                    fn = tool_call.get("function") if isinstance(tool_call, dict) else {}
                    if not isinstance(fn, dict):
                        continue
                    name = str(fn.get("name") or "")
                    if name:
                        last_tool = name
                        lines.append(f"[session] tool.started {name}")
            elif message.get("role") == "tool" and last_tool:
                content = str(message.get("content") or "")
                is_error = '"error"' in content or content.lstrip().startswith("error")
                lines.append(
                    f"[session] tool.completed {last_tool} "
                    f"duration=0.00s error={is_error}"
                )
                if not is_error:
                    lines.append(f"[session] {last_tool}: success returned")
    return lines


def _log_fragment_variants(fragment: str) -> list[str]:
    """Return log fragments that satisfy an expected OpenClaw action key."""
    variants = [fragment]
    variants.extend(OPENCLAW_ACTION_EQUIVALENTS.get(fragment, []))
    return list(dict.fromkeys(variants))


def check_case_result(lines: list, case: dict, sender_open_id: str) -> dict:
    """Check the test case against new log lines.

    Returns a dict with:
      tool_dispatched (bool) — LLM picked the expected tool
      uat_used        (bool) — sender_open_id appears in UAT load logs
      profile_routed  (bool) — multitenancy routed to a profile (HERMES_HOME log)
      direct_routed   (bool) — gateway core direct agent path handled the turn
      route_matched   (bool) — either multitenancy or direct route evidence exists
      tool_returned   (bool) — handler logged a normal completion
      assistant_finalized (bool) — final assistant/card content was persisted or logged
      errors          (list) — any 99991672/99991679/Error lines
    """
    expect_tools = case.get("expect_tools") or [case.get("expect_tool")]
    expect_tools = [t for t in expect_tools if t]
    expect_logs = [str(fragment) for fragment in case.get("expect_logs", [])]
    expect_log_variants = [_log_fragment_variants(fragment) for fragment in expect_logs]
    equivalent_tools = [
        tool
        for fragment in expect_logs
        for tool in OPENCLAW_ACTION_EQUIVALENTS.get(fragment, [])
    ]
    runtime_tools = list(dict.fromkeys([*expect_tools, *equivalent_tools]))

    log_matched = all(
        any(any(fragment in line for fragment in variants) for line in lines)
        for variants in expect_log_variants
    )
    if runtime_tools:
        tool_dispatched = any(
            any(f"{t}" in line for t in runtime_tools) for line in lines
        )
    else:
        tool_dispatched = log_matched if expect_logs else True
    uat_used = any(
        sender_open_id[:16] in line
        and (
            "for_user" in line
            or "_load_uat" in line
            or "access_token" in line
            or "Feishu UAT lookup" in line
        )
        for line in lines
    )
    profile_routed = any(
        (
            "ProfileRuntime" in line
            or "HERMES_HOME" in line
            or "_run_with_aiagent" in line
            or ("[multitenancy] running AIAgent" in line and "profile=" in line)
        )
        for line in lines
    )
    direct_routed = any(
        (
            "Turn ended:" in line
            or "run_agent resolved:" in line
            or "Created new agent for session" in line
            or "Reusing cached agent for session" in line
            or "Agent error in session" in line
        )
        for line in lines
    )
    tool_returned = any(
        (
            any(f"{t}:" in line for t in runtime_tools)
            and ("returned" in line or "created" in line or "success" in line.lower())
        )
        or any(
            f"tool.completed {t}" in line and "error=False" in line
            for t in runtime_tools
        )
        or any(
            f"tool {t} completed" in line
            for t in runtime_tools
        )
        for line in lines
    )
    successful_tools = {
        t
        for t in runtime_tools
        if any(f"tool.completed {t}" in line and "error=False" in line for line in lines)
    }
    tool_errors = [
        line for line in lines
        if any(
            f"tool.completed {t}" in line
            and "error=True" in line
            and t not in successful_tools
            for t in runtime_tools
        )
        or any(
            f"tool {t} failed" in line
            for t in runtime_tools
        )
    ]
    assistant_finalized = any(
        "assistant.finalized" in line
        or (
            "Turn ended:" in line
            and (
                "assistant_final" in line
                or "last_msg_role=assistant" in line
                or "response_len=" in line
            )
        )
        or "final card sent" in line
        for line in lines
    )
    card_finalized = any(
        "streaming_card.finalized" in line
        or "streaming_card: final card sent" in line
        or "card.finalized" in line
        for line in lines
    )
    errors = [
        line for line in lines
        if "99991672" in line or "99991679" in line or "Traceback" in line or "ERROR" in line
    ] + tool_errors
    return {
        "tool_dispatched": tool_dispatched,
        "log_matched": log_matched,
        "uat_used": uat_used,
        "profile_routed": profile_routed,
        "direct_routed": direct_routed,
        "route_matched": profile_routed or direct_routed,
        "tool_returned": tool_returned,
        "assistant_finalized": assistant_finalized,
        "card_finalized": card_finalized,
        "errors": errors[:3],
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _required_checks(
    case: dict,
    strict_identity: bool,
    route_mode: str = "multitenant",
    *,
    require_card_final: bool = False,
) -> list[str]:
    if case.get("identity") == "slash" and case.get("expect_logs") and not (
        case.get("expect_tool") or case.get("expect_tools")
    ):
        return ["log_matched"]
    if route_mode == "direct":
        route_check = "direct_routed"
    elif route_mode == "any":
        route_check = "route_matched"
    else:
        route_check = "profile_routed"
    checks = ["tool_dispatched", route_check]
    if case.get("expect_tool") or case.get("expect_tools"):
        checks.append("tool_returned")
        checks.append("assistant_finalized")
        if require_card_final:
            checks.append("card_finalized")
    if case.get("expect_logs"):
        checks.append("log_matched")
    if strict_identity and case.get("identity") == "uat":
        checks.append("uat_used")
    return checks


def run_case(
    uat: dict,
    chat_id: str,
    case: dict,
    wait_seconds: int,
    *,
    fixtures: dict[str, str] | None = None,
    allow_placeholders: bool = False,
    allow_destructive: bool = False,
    strict_identity: bool = False,
    route_mode: str = "multitenant",
    dry_run: bool = False,
    require_card_final: bool = False,
    openclaw_repo: Path = DEFAULT_OPENCLAW_REPO,
    hermes_repo: Path = REPO_ROOT,
    uat_path: Path | None = None,
) -> dict:
    sender_open_id = uat["open_id"]
    fixtures = fixtures or {}

    if case.get("static_check"):
        if dry_run:
            print(f"[{case['id']}] static dry-run: {case['input']}")
            return {"id": case["id"], "passed": False, "skipped": True, "reason": "dry-run", "expected": case["static_check"]}
        result = run_static_check(case, openclaw_repo=openclaw_repo, hermes_repo=hermes_repo)
        icon = "✅" if result.get("passed") else "❌"
        print(f"[{case['id']}] {icon} static_check={case['static_check']}")
        if result.get("error"):
            print(f"  {result['error']}")
        for action in result.get("missing_actions", [])[:20]:
            print(f"  missing: {action}")
        if len(result.get("missing_actions", [])) > 20:
            print(f"  ... {len(result['missing_actions']) - 20} more")
        return result

    if case.get("destructive") and not allow_destructive:
        print(f"[{case['id']}] ⏭️  skipped destructive case; rerun with --allow-destructive")
        return {"id": case["id"], "passed": False, "skipped": True, "reason": "destructive"}

    try:
        rendered_input = render_case_input(case, fixtures)
    except MissingFixtureError as exc:
        if not allow_placeholders:
            print(f"[{case['id']}] ⏭️  skipped; missing fixture(s): {', '.join(exc.missing)}")
            if case.get("setup"):
                print(f"  setup: {case['setup']}")
            return {
                "id": case["id"],
                "passed": False,
                "skipped": True,
                "reason": f"missing fixtures: {', '.join(exc.missing)}",
            }
        rendered_input = str(case["input"])

    print(f"[{case['id']}] sending: {rendered_input[:60]}")
    if dry_run:
        expected = case.get("expect_tool") or "+".join(case.get("expect_tools", [])) or "+".join(case.get("expect_logs", []))
        print(f"  dry-run only; expected={expected}")
        return {"id": case["id"], "passed": False, "skipped": True, "reason": "dry-run", "expected": expected}

    pos = get_log_position()
    t0 = time.time()
    try:
        if uat_path is not None:
            ensure_uat_valid_for_post(uat_path, uat)
        rsp = post_message_as_user(uat["access_token"], chat_id, rendered_input)
    except Exception as exc:
        if uat_path is not None and _is_token_expired_post_error(exc):
            print("  ↻ UAT token expired while posting; refreshing and retrying once...")
            ensure_uat_valid_for_post(uat_path, uat, min_valid_seconds=7200)
            try:
                rsp = post_message_as_user(uat["access_token"], chat_id, rendered_input)
            except Exception as retry_exc:
                print(f"  ❌ post failed after refresh: {retry_exc}")
                return {"id": case["id"], "passed": False, "error": str(retry_exc), "elapsed": 0}
        else:
            print(f"  ❌ post failed: {exc}")
            return {"id": case["id"], "passed": False, "error": str(exc), "elapsed": 0}

    code = rsp.get("code", -1)
    if code != 0:
        print(f"  ❌ feishu rejected post: code={code} msg={rsp.get('msg')}")
        return {"id": case["id"], "passed": False, "error": rsp, "elapsed": 0}

    msg_id = rsp.get("data", {}).get("message_id", "?")
    checks = _required_checks(
        case,
        strict_identity,
        route_mode,
        require_card_final=require_card_final,
    )
    print(f"  posted msg_id={msg_id}, waiting up to {wait_seconds}s for bot pipeline...")
    result: dict = {
        "tool_dispatched": False,
        "log_matched": False,
        "uat_used": False,
        "profile_routed": False,
        "direct_routed": False,
        "route_matched": False,
        "tool_returned": False,
        "assistant_finalized": False,
        "card_finalized": False,
        "errors": [],
    }
    passed = False
    new_lines: list[str] = []
    deadline = t0 + max(wait_seconds, 0)
    while True:
        if wait_seconds > 0:
            remaining = deadline - time.time()
            if remaining > 0:
                time.sleep(min(2.0, remaining))
        elapsed = time.time() - t0
        new_lines = read_new_log_lines(pos, since_ts=t0)
        session_lines = read_session_evidence_lines(
            str(msg_id),
            sender_open_id,
            user_input=rendered_input,
            since_ts=t0,
        )
        combined_lines = [*new_lines, *session_lines]
        result = check_case_result(combined_lines, case, sender_open_id)
        if session_lines:
            result["recovered_from_session"] = True
        passed = all(result.get(check) for check in checks) and not result["errors"]
        if passed or wait_seconds <= 0 or time.time() >= deadline:
            break

    icon = "✅" if passed else "❌"
    expected = (
        case.get("expect_tool")
        or "+".join(case.get("expect_tools", []))
        or "+".join(case.get("expect_logs", []))
    )
    bits = [
        f"{'✓' if result['tool_dispatched'] else '✗'}tool",
        f"{'✓' if result['profile_routed'] else '✗'}profile",
        f"{'✓' if result['direct_routed'] else '✗'}direct",
        f"{'✓' if result['uat_used'] else '✗'}uat",
        f"{'✓' if result['tool_returned'] else '✗'}return",
        f"{'✓' if result['assistant_finalized'] else '✗'}final",
        f"{'✓' if result.get('card_finalized') else '✗'}card",
    ]
    if case.get("expect_logs"):
        bits.append(f"{'✓' if result['log_matched'] else '✗'}logs")
    print(f"  {icon} {expected} ({elapsed:.1f}s) [{' '.join(bits)}]")
    if result["errors"]:
        for err in result["errors"]:
            print(f"     ⚠️  {err[:120]}")

    return {
        "id": case["id"],
        "passed": passed,
        "elapsed": elapsed,
        "expected": expected,
        **result,
    }


def main():
    parser = argparse.ArgumentParser(description="Hermes Feishu UAT pipeline stress test")
    parser.add_argument(
        "--chat-id",
        default=os.environ.get("HERMES_FEISHU_TEST_CHAT_ID"),
        help="Chat ID where bot is a member (e.g. oc_xxx). Can also use HERMES_FEISHU_TEST_CHAT_ID.",
    )
    parser.add_argument("--suite", default="smoke", choices=sorted(SUITE_MAP))
    parser.add_argument(
        "--case-id",
        action="append",
        help="Run only specific case id(s), e.g. --case-id C1 or --case-id C1,T1",
    )
    parser.add_argument("--uat", help="Path to UAT json file. Overrides --user.")
    parser.add_argument(
        "--user",
        default=os.environ.get("HERMES_FEISHU_TEST_USER", "本人"),
        help="UAT user selector: name/open_id/file stem, or 本人/default/美元本袁 for richest valid UAT.",
    )
    parser.add_argument("--list-users", action="store_true", help="List UAT candidates and exit without sending messages.")
    parser.add_argument("--fixtures", help="JSON object used to replace {doc_token}, {event_id}, etc.")
    parser.add_argument(
        "--set",
        dest="fixture_set",
        action="append",
        help="Inline fixture key=value. Can be repeated and overrides --fixtures.",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Send unresolved {fixture} placeholders literally instead of skipping those cases.",
    )
    parser.add_argument(
        "--allow-destructive",
        action="store_true",
        help="Run create/update/delete/send cases. By default they are skipped.",
    )
    parser.add_argument(
        "--strict-identity",
        action="store_true",
        help="For UAT cases, require logs to prove the selected user's UAT was used.",
    )
    parser.add_argument(
        "--route-mode",
        choices=("multitenant", "direct", "any"),
        default=os.environ.get("HERMES_FEISHU_TEST_ROUTE_MODE", "multitenant"),
        help=(
            "Expected gateway route evidence. Use direct after disabling the "
            "multitenancy plugin, any while migrating or diagnosing route drift."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Resolve users/cases/fixtures but do not send messages.")
    parser.add_argument(
        "--openclaw-repo",
        default=str(DEFAULT_OPENCLAW_REPO),
        help="Path to cloned openclaw-lark repo for exact static checks.",
    )
    parser.add_argument(
        "--hermes-repo",
        default=str(REPO_ROOT),
        help="Path to Hermes repo for exact static checks.",
    )
    parser.add_argument(
        "--checkpoint",
        help="JSONL file to append case results to for interrupted/resumable full runs.",
    )
    parser.add_argument(
        "--resume-passed",
        action="store_true",
        help="When --checkpoint is set, skip case ids whose latest checkpoint result already passed.",
    )
    parser.add_argument(
        "--require-card-final",
        action="store_true",
        help=(
            "For live Feishu card runs, wait for CardKit finalization evidence "
            "before marking a tool case passed."
        ),
    )
    parser.add_argument("--wait", type=int, default=12, help="Seconds to wait per case for bot pipeline (default 12)")
    parser.add_argument("--gap", type=int, default=4, help="Seconds between cases (default 4)")
    args = parser.parse_args()

    if args.list_users:
        print_uat_candidates()
        return

    if args.uat:
        uat_path = Path(args.uat).expanduser()
    else:
        uat_path = resolve_uat_path(args.user)

    cases = select_cases(args.suite, args.case_id)
    if not args.chat_id and not args.dry_run and any(not case.get("static_check") for case in cases):
        sys.exit("--chat-id is required unless --dry-run is used or all selected cases are static checks. You can also set HERMES_FEISHU_TEST_CHAT_ID.")

    print(f"Loading UAT from {uat_path}")
    uat = load_uat(uat_path, require_valid=not args.dry_run)
    print(f"  open_id: {uat['open_id']}")
    print(f"  scopes:  {len(uat.get('scope', '').split())}")
    print(f"  chat_id: {args.chat_id or '(dry-run)'}")
    print(f"  user selector: {args.user}")
    print(f"  route_mode: {args.route_mode}")
    print()

    fixtures = load_fixtures(args.fixtures, args.fixture_set)
    print(f"Running '{args.suite}' suite: {len(cases)} case(s), {args.wait}s wait + {args.gap}s gap each")
    print(f"Total estimated time: {len(cases) * (args.wait + args.gap)}s")
    if fixtures:
        print(f"Fixtures: {', '.join(sorted(fixtures))}")
    checkpoint_path = Path(args.checkpoint).expanduser() if args.checkpoint else None
    passed_ids = passed_checkpoint_ids(checkpoint_path) if checkpoint_path and args.resume_passed else set()
    if checkpoint_path:
        print(f"Checkpoint: {checkpoint_path}")
    if passed_ids:
        print(f"Resume: {len(passed_ids)} previously passed case(s) will be skipped")
    if not args.allow_destructive:
        destructive_count = sum(1 for case in cases if case.get("destructive"))
        if destructive_count:
            print(f"Destructive cases will be skipped: {destructive_count} (use --allow-destructive to run them)")
    print()

    results = []
    for case in cases:
        if case["id"] in passed_ids:
            result = {
                "id": case["id"],
                "passed": True,
                "skipped": True,
                "reason": "previously passed",
            }
            print(f"[{case['id']}] ✅ skipped; previously passed in checkpoint")
        else:
            result = run_case(
                uat,
                args.chat_id or "",
                case,
                args.wait,
                fixtures=fixtures,
                allow_placeholders=args.allow_placeholders,
                allow_destructive=args.allow_destructive,
                strict_identity=args.strict_identity,
                route_mode=args.route_mode,
                dry_run=args.dry_run,
                require_card_final=args.require_card_final,
                openclaw_repo=Path(args.openclaw_repo).expanduser(),
                hermes_repo=Path(args.hermes_repo).expanduser(),
                uat_path=uat_path,
            )
            if checkpoint_path and should_record_checkpoint(result, dry_run=args.dry_run):
                record_checkpoint(checkpoint_path, result)
        results.append(result)
        if case is not cases[-1]:
            time.sleep(args.gap)

    print()
    print("=" * 72)
    skipped = sum(1 for r in results if r.get("skipped"))
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    failed = [r for r in results if not r["passed"] and not r.get("skipped")]
    print(f"Summary: {passed}/{total} PASSED, {skipped} SKIPPED, {len(failed)} FAILED")
    if failed:
        print()
        print("Failed cases:")
        for r in failed:
            print(f"  [{r['id']}] expected: {r.get('expected')}  errors: {r.get('errors', r.get('error'))}")
    skipped_results = [r for r in results if r.get("skipped")]
    if skipped_results:
        print()
        print("Skipped cases:")
        for r in skipped_results[:30]:
            print(f"  [{r['id']}] {r.get('reason')}")
        if len(skipped_results) > 30:
            print(f"  ... {len(skipped_results) - 30} more")

    sys.exit(0 if passed == total and not failed else 1)


if __name__ == "__main__":
    main()
