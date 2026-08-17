#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容管理模块 (JSON CRUD)
- 通用列表: projects / publications / tools / timeline
- 个人信息: profile
存储: admin_backend/data/*.json (容器挂载持久化)
"""
import json
import os
import re
from functools import wraps

from flask import (Blueprint, jsonify, redirect, render_template,
                   request, session, url_for)

content_mgr_bp = Blueprint("content_mgr", __name__)


def _admin_required(f):
    """与主 app 的 require_admin 保持一致"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ====== 内容 Schema ======
CONTENT_SCHEMAS = {
    "projects": {
        "label": "项目",
        "icon": "bi-kanban",
        "file": "projects.json",
        "fields": [
            {"key": "id", "label": "ID", "type": "text", "required": True,
             "help": "唯一标识(英文小写),如 retrozero"},
            {"key": "name", "label": "名称", "type": "text", "required": True},
            {"key": "full_name", "label": "全称", "type": "text"},
            {"key": "status", "label": "状态", "type": "select",
             "options": [("completed", "已完成"), ("active", "进行中"), ("planned", "计划中")]},
            {"key": "description", "label": "描述", "type": "textarea", "required": True},
            {"key": "tech", "label": "技术栈", "type": "list", "help": "每行一项"},
            {"key": "highlights", "label": "亮点", "type": "list", "help": "每行一项"},
            {"key": "links", "label": "链接", "type": "links", "help": "每行格式: 名称: URL"},
        ],
    },
    "publications": {
        "label": "发表",
        "icon": "bi-journal-richtext",
        "file": "publications.json",
        "fields": [
            {"key": "id", "label": "ID", "type": "text", "required": True,
             "help": "唯一标识(英文小写),如 jctc-retrozero"},
            {"key": "title", "label": "标题", "type": "text", "required": True},
            {"key": "type", "label": "类型", "type": "select",
             "options": [("paper", "论文"), ("preprint", "预印本"),
                         ("project", "项目"), ("conference", "会议"), ("patent", "专利")]},
            {"key": "authors", "label": "作者", "type": "list", "help": "每行一位作者"},
            {"key": "venue", "label": "发表期刊/平台", "type": "text"},
            {"key": "year", "label": "年份", "type": "number"},
            {"key": "volume", "label": "卷", "type": "text"},
            {"key": "issue", "label": "期", "type": "text"},
            {"key": "pages", "label": "页码", "type": "text"},
            {"key": "status", "label": "状态", "type": "select",
             "options": [("published", "已发表"), ("preprint", "预印本"),
                         ("in_progress", "在研/在审")]},
            {"key": "description", "label": "描述", "type": "textarea"},
            {"key": "tags", "label": "标签", "type": "list", "help": "每行一项"},
            {"key": "links", "label": "链接", "type": "links", "help": "每行格式: 名称: URL"},
        ],
    },
    "tools": {
        "label": "工具",
        "icon": "bi-tools",
        "file": "tools.json",
        "fields": [
            {"key": "id", "label": "ID", "type": "text", "required": True,
             "help": "唯一标识(英文小写),如 chemmix"},
            {"key": "name", "label": "名称", "type": "text", "required": True},
            {"key": "description", "label": "描述", "type": "textarea", "required": True},
            {"key": "category", "label": "分类", "type": "text"},
            {"key": "status", "label": "状态", "type": "select",
             "options": [("deployed", "已部署"), ("active", "进行中"), ("offline", "已下线")]},
            {"key": "access_url", "label": "访问链接", "type": "text"},
            {"key": "tags", "label": "标签", "type": "list", "help": "每行一项"},
            {"key": "year", "label": "年份", "type": "number"},
            {"key": "links", "label": "链接", "type": "links", "help": "每行格式: 名称: URL"},
        ],
    },
    "timeline": {
        "label": "时间线",
        "icon": "bi-clock-history",
        "file": "timeline.json",
        "fields": [
            {"key": "period", "label": "时间段", "type": "text", "required": True,
             "help": "如 2019 - 2023"},
            {"key": "title", "label": "标题", "type": "text", "required": True},
            {"key": "org", "label": "机构", "type": "text"},
            {"key": "description", "label": "描述", "type": "textarea"},
        ],
    },
}


def _read_content(key):
    path = os.path.join(DATA_DIR, CONTENT_SCHEMAS[key]["file"])
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _write_content(key, data):
    path = os.path.join(DATA_DIR, CONTENT_SCHEMAS[key]["file"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _parse_list(raw):
    return [x.strip() for x in re.split(r"[,，\n]+", raw) if x.strip()]


def _parse_links(raw):
    links = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            links[k.strip()] = v.strip()
        elif line:
            links[line] = line
    return links


def _fmt_list(items):
    if isinstance(items, list):
        return "\n".join(str(x) for x in items)
    return ""


def _fmt_links(links):
    if isinstance(links, dict):
        return "\n".join(f"{k}: {v}" for k, v in links.items())
    return ""


def _auto_id(entry, key):
    """自动生成条目 id(基于标题/名称/时间段),保证唯一"""
    base = entry.get("title") or entry.get("name") or entry.get("period") or "item"
    slug = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", str(base)).strip("-")
    if not slug:
        slug = "item"
    items = _read_content(key)
    exists = {str(x.get("id", "")) for x in items}
    candidate, n = slug, 2
    while candidate in exists:
        candidate = f"{slug}-{n}"
        n += 1
    return candidate


@content_mgr_bp.app_template_filter("dict_to_lines")
def _dict_to_lines(d):
    if not isinstance(d, dict):
        return ""
    return "\n".join(f"{k}: {v}" for k, v in d.items())


def _load_profile():
    path = os.path.join(DATA_DIR, "profile.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_profile(profile):
    path = os.path.join(DATA_DIR, "profile.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ====== 通用列表 ======
@content_mgr_bp.route("/admin/content/<key>")
@_admin_required
def content_list(key):
    if key not in CONTENT_SCHEMAS:
        return "未知内容类型", 404
    schema = CONTENT_SCHEMAS[key]
    items = _read_content(key)
    # 主显示字段:优先 name/title
    title_field = "name" if key in ("projects", "tools") else "title"
    return render_template("content_list.html", schema=schema, items=items,
                           key=key, title_field=title_field)


@content_mgr_bp.route("/admin/content/<key>/new")
@_admin_required
def content_new(key):
    if key not in CONTENT_SCHEMAS:
        return "未知内容类型", 404
    return render_template("content_edit.html", schema=CONTENT_SCHEMAS[key],
                           key=key, item=None, item_id="", prefill={})


@content_mgr_bp.route("/admin/content/<key>/edit/<item_id>")
@_admin_required
def content_edit(key, item_id):
    if key not in CONTENT_SCHEMAS:
        return "未知内容类型", 404
    schema = CONTENT_SCHEMAS[key]
    items = _read_content(key)
    item = next((x for x in items if str(x.get("id", "")) == item_id), None)
    if item is None:
        return "条目不存在", 404
    return render_template("content_edit.html", schema=schema, key=key,
                           item=item, item_id=item_id, prefill={})


@content_mgr_bp.route("/admin/content/<key>/save", methods=["POST"])
@_admin_required
def content_save(key):
    if key not in CONTENT_SCHEMAS:
        return "未知内容类型", 404
    schema = CONTENT_SCHEMAS[key]
    items = _read_content(key)
    form = request.form
    item_id = form.get("item_id", "").strip()

    entry = {}
    for f in schema["fields"]:
        raw = form.get(f["key"], "")
        ftype = f["type"]
        if ftype == "list":
            entry[f["key"]] = _parse_list(raw)
        elif ftype == "links":
            entry[f["key"]] = _parse_links(raw)
        elif ftype == "number":
            entry[f["key"]] = int(raw) if raw.strip() else None
        else:
            entry[f["key"]] = raw.strip()
    # 剔除空值:links/list 类型始终保留(空 dict/list 也要写,模板依赖字段存在)
    # 仅 text/number/select 的空值剔除
    field_types = {f["key"]: f["type"] for f in schema["fields"]}
    entry = {k: v for k, v in entry.items()
             if field_types.get(k) in ("links", "list") or v not in ("", None)}

    if item_id:
        for i, x in enumerate(items):
            if str(x.get("id", "")) == item_id:
                entry.setdefault("id", x.get("id", ""))
                items[i] = entry
                break
        else:
            items.append(entry)
    else:
        if not entry.get("id"):
            entry["id"] = _auto_id(entry, key)
        items.append(entry)

    _write_content(key, items)
    return redirect(url_for("content_mgr.content_list", key=key))


@content_mgr_bp.route("/admin/content/<key>/delete/<item_id>", methods=["POST"])
@_admin_required
def content_delete(key, item_id):
    if key not in CONTENT_SCHEMAS:
        return redirect(url_for("content_mgr.content_list", key=key))
    items = _read_content(key)
    items = [x for x in items if str(x.get("id", "")) != item_id]
    _write_content(key, items)
    # 普通表单提交,重定向回列表页(返回 JSON 会被浏览器当页面显示)
    return redirect(url_for("content_mgr.content_list", key=key))


# ====== 个人信息 ======
@content_mgr_bp.route("/admin/content/profile", methods=["GET", "POST"])
@_admin_required
def content_profile():
    profile = _load_profile()
    if request.method == "POST":
        form = request.form
        profile = {
            "name": form.get("name", "").strip(),
            "alias": form.get("alias", "").strip(),
            "title": form.get("title", "").strip(),
            "subtitle": form.get("subtitle", "").strip(),
            "bio": form.get("bio", "").strip(),
            "location": form.get("location", "").strip(),
            "email": form.get("email", "").strip(),
            "social": {
                "github": form.get("social_github", "").strip(),
                "blog": form.get("social_blog", "").strip(),
            },
        }
        # highlights 动态行 (icon | label | value)
        hl = []
        icons = form.getlist("hl_icon")
        labels = form.getlist("hl_label")
        values = form.getlist("hl_value")
        for i in range(len(labels)):
            label = labels[i].strip()
            if not label:
                continue
            hl.append({
                "icon": icons[i].strip() if i < len(icons) else "",
                "label": label,
                "value": values[i].strip() if i < len(values) else "",
            })
        if hl:
            profile["highlights"] = hl
        else:
            profile.pop("highlights", None)
        _save_profile(profile)
        return redirect(url_for("content_mgr.content_profile", saved=1))
    saved = request.args.get("saved", "")
    return render_template("content_profile.html", profile=profile, saved=saved)
