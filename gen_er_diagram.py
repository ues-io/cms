#!/usr/bin/env python3
"""Generate an ER diagram (SVG) for the Agent Service schema."""

ROW_H = 22
HEAD_H = 30
CHAR = 7  # approx px per char for monospace sizing

# group colors
CORE = "#2563eb"      # blue
JUNCTION = "#d97706"  # amber
CONV = "#059669"      # green

# Each table: (key, x, y, width, header_color, group_label, rows)
# rows: (text, kind)  kind in {pk, fk, uq, col, audit}
tables = {
    "Agent": dict(x=520, y=60, w=250, color=CORE, label="agent_agents", rows=[
        ("id : uuid", "pk"),
        ("agent_id : varchar  UQ", "uq"),
        ("name : varchar", "col"),
        ("model_provider : varchar", "col"),
        ("model_name : varchar", "col"),
        ("system_prompt : text", "col"),
        ("is_active : bool", "col"),
        ("+ audit (created/updated _at/_by)", "audit"),
    ]),
    "MCPServer": dict(x=1230, y=40, w=250, color=CORE, label="agent_mcp_servers", rows=[
        ("id : uuid", "pk"),
        ("name : varchar  UQ", "uq"),
        ("transport_type : varchar", "col"),
        ("url : varchar", "col"),
        ("config : jsonb", "col"),
        ("is_active : bool", "col"),
        ("+ audit fields", "audit"),
    ]),
    "Tool": dict(x=1230, y=410, w=250, color=CORE, label="agent_tools", rows=[
        ("id : uuid", "pk"),
        ("name : varchar  UQ", "uq"),
        ("tool_type : varchar", "col"),
        ("input_schema : jsonb", "col"),
        ("config : jsonb", "col"),
        ("is_active : bool", "col"),
        ("+ audit fields", "audit"),
    ]),
    "AgentMCPServer": dict(x=900, y=70, w=230, color=JUNCTION, label="agent_mcp_server_links", rows=[
        ("id : uuid", "pk"),
        ("agent_id : uuid", "fk"),
        ("mcp_server_id : uuid", "fk"),
        ("UQ(agent_id, mcp_server_id)", "uq"),
        ("+ audit fields", "audit"),
    ]),
    "AgentTool": dict(x=900, y=430, w=230, color=JUNCTION, label="agent_tool_links", rows=[
        ("id : uuid", "pk"),
        ("agent_id : uuid", "fk"),
        ("tool_id : uuid", "fk"),
        ("UQ(agent_id, tool_id)", "uq"),
        ("+ audit fields", "audit"),
    ]),
    "AgentThread": dict(x=520, y=440, w=250, color=CONV, label="agent_threads", rows=[
        ("id : uuid", "pk"),
        ("thread_id : varchar  UQ", "uq"),
        ("agent_id : uuid", "fk"),
        ("thread_metadata : jsonb", "col"),
        ("+ audit fields", "audit"),
    ]),
    "AgentThreadItem": dict(x=520, y=660, w=250, color=CONV, label="agent_thread_items", rows=[
        ("id : uuid", "pk"),
        ("thread_id : uuid", "fk"),
        ("item_type : varchar", "col"),
        ("role : varchar", "col"),
        ("content : text", "col"),
        ("tool_name : varchar", "col"),
        ("tool_input : jsonb", "col"),
        ("tool_result : jsonb", "col"),
        ("tool_use_id : varchar", "col"),
        ("+ audit fields", "audit"),
    ]),
}


def height(t):
    return HEAD_H + len(t["rows"]) * ROW_H


def render_table(name, t):
    x, y, w = t["x"], t["y"], t["w"]
    h = height(t)
    out = []
    out.append(f'<g>')
    # shadow
    out.append(f'<rect x="{x+3}" y="{y+3}" width="{w}" height="{h}" rx="8" fill="#00000018"/>')
    # body
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>')
    # header
    out.append(f'<path d="M{x},{y+HEAD_H} L{x},{y+8} Q{x},{y} {x+8},{y} L{x+w-8},{y} Q{x+w},{y} {x+w},{y+8} L{x+w},{y+HEAD_H} Z" fill="{t["color"]}"/>')
    out.append(f'<text x="{x+12}" y="{y+15}" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700" fill="#ffffff">{name}</text>')
    out.append(f'<text x="{x+12}" y="{y+26}" font-family="Consolas, monospace" font-size="9.5" fill="#e2e8f0">{t["label"]}</text>')
    # rows
    ry = y + HEAD_H
    for i, (text, kind) in enumerate(t["rows"]):
        if i % 2 == 1:
            out.append(f'<rect x="{x}" y="{ry}" width="{w}" height="{ROW_H}" fill="#f8fafc"/>')
        weight = "700" if kind == "pk" else "400"
        style = "italic" if kind in ("fk",) else "normal"
        color = "#0f172a"
        if kind == "audit":
            color = "#94a3b8"
        elif kind == "fk":
            color = "#b45309"
        elif kind == "uq":
            color = "#1d4ed8"
        badge = ""
        if kind == "pk":
            badge = '<tspan font-weight="700" fill="#2563eb"> PK</tspan>'
        elif kind == "fk":
            badge = '<tspan font-weight="700" fill="#b45309" font-style="normal"> FK</tspan>'
        out.append(
            f'<text x="{x+12}" y="{ry+15}" font-family="Consolas, monospace" font-size="11" '
            f'font-weight="{weight}" font-style="{style}" fill="{color}">{text}{badge}</text>'
        )
        ry += ROW_H
    out.append('</g>')
    return "\n".join(out)


def edge_path(x1, y1, x2, y2):
    # simple orthogonal-ish: horizontal then to target
    mx = (x1 + x2) / 2
    return f"M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}"


def one_marker(x, y, orient):
    if orient == "h":
        return f'<path d="M{x},{y-7} L{x},{y+7}" stroke="#475569" stroke-width="1.8"/>'
    return f'<path d="M{x-7},{y} L{x+7},{y}" stroke="#475569" stroke-width="1.8"/>'


def many_marker(x, y, orient, approach):
    # approach: direction the line comes FROM ('left','right','top','bottom')
    if approach == "left":
        bx = x - 14
        return (f'<path d="M{x},{y} L{bx},{y-7} M{x},{y} L{bx},{y} M{x},{y} L{bx},{y+7}" '
                f'fill="none" stroke="#475569" stroke-width="1.6"/>')
    if approach == "top":
        by = y - 14
        return (f'<path d="M{x},{y} L{x-7},{by} M{x},{y} L{x},{by} M{x},{y} L{x+7},{by}" '
                f'fill="none" stroke="#475569" stroke-width="1.6"/>')
    return ""


def render_edge(a, ay, b, by, label, side_a="right", side_b="left"):
    ta, tb = tables[a], tables[b]
    if side_a == "right":
        x1 = ta["x"] + ta["w"]
    elif side_a == "left":
        x1 = ta["x"]
    elif side_a == "bottom":
        x1 = ta["x"] + ta["w"] / 2
    y1 = ay
    if side_b == "left":
        x2 = tb["x"]
    elif side_b == "right":
        x2 = tb["x"] + tb["w"]
    elif side_b == "top":
        x2 = tb["x"] + tb["w"] / 2
    y2 = by
    if side_a == "bottom":
        y1 = ta["y"] + height(ta)
        p = f"M{x1},{y1} C{x1},{(y1+y2)/2} {x2},{(y1+y2)/2} {x2},{y2}"
        one = one_marker(x1, y1, "v")
        many = many_marker(x2, y2, "v", "top")
    else:
        p = edge_path(x1, y1, x2, y2)
        one = one_marker(x1, y1, "h")
        many = many_marker(x2, y2, "h", "left")
    out = [f'<path d="{p}" fill="none" stroke="#64748b" stroke-width="1.6"/>', one, many]
    lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 6
    out.append(f'<rect x="{lx-88}" y="{ly-13}" width="176" height="18" rx="4" fill="#ffffff" opacity="0.92"/>')
    out.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.5" fill="#334155">{label}</text>')
    return "\n".join(out)


def row_y(t, idx):
    return t["y"] + HEAD_H + idx * ROW_H + ROW_H / 2


parts = []
W, H = 1520, 940
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Arial, sans-serif">')
parts.append('<defs>')
parts.append('<marker id="many" markerWidth="22" markerHeight="22" refX="2" refY="11" orient="auto"><path d="M2,11 L20,3 M2,11 L20,11 M2,11 L20,19" fill="none" stroke="#64748b" stroke-width="1.6"/></marker>')
parts.append('<marker id="one" markerWidth="16" markerHeight="22" refX="10" refY="11" orient="auto"><path d="M10,4 L10,18" stroke="#64748b" stroke-width="1.8"/></marker>')
parts.append('</defs>')
parts.append(f'<rect width="{W}" height="{H}" fill="#f1f5f9"/>')
parts.append(f'<text x="40" y="40" font-size="22" font-weight="700" fill="#0f172a">Agent Service — Database Schema (ER Diagram)</text>')

# legend
lg = [("Core entity", CORE), ("Junction (M:N)", JUNCTION), ("Conversation", CONV)]
lx = 1050
for label, col in lg:
    parts.append(f'<rect x="{lx}" y="26" width="16" height="16" rx="3" fill="{col}"/>')
    parts.append(f'<text x="{lx+22}" y="39" font-size="12" fill="#334155">{label}</text>')
    lx += 150

# edges (draw before tables so tables sit on top)
A = tables
parts.append(render_edge("Agent", row_y(A["Agent"], 0), "AgentMCPServer", row_y(A["AgentMCPServer"], 1), "1 : N  has", "right", "left"))
parts.append(render_edge("AgentMCPServer", row_y(A["AgentMCPServer"], 2), "MCPServer", row_y(A["MCPServer"], 0), "N : 1  references", "right", "left"))
parts.append(render_edge("Agent", row_y(A["Agent"], 3), "AgentTool", row_y(A["AgentTool"], 1), "1 : N  has", "right", "left"))
parts.append(render_edge("AgentTool", row_y(A["AgentTool"], 2), "Tool", row_y(A["Tool"], 0), "N : 1  references", "right", "left"))
parts.append(render_edge("Agent", 0, "AgentThread", row_y(A["AgentThread"], 0), "1 : N  owns", "bottom", "top"))
parts.append(render_edge("AgentThread", 0, "AgentThreadItem", row_y(A["AgentThreadItem"], 0), "1 : N  contains", "bottom", "top"))

for name, t in tables.items():
    parts.append(render_table(name, t))

parts.append('<text x="40" y="915" font-size="11" fill="#94a3b8">PK = primary key (uuid) · FK = foreign key (ON DELETE CASCADE) · UQ = unique · every table carries created/updated _at and _by audit columns</text>')
parts.append('</svg>')

with open("agent_service_er_diagram.svg", "w") as f:
    f.write("\n".join(parts))
print("wrote agent_service_er_diagram.svg")
