from html import escape
from typing import Dict

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from config import DROP_ZONE
from hardware.robot_arm import RobotArm
from llm.parser import parse_command
from logger import append_csv, read_csv
from robotics.ik import inverse_kinematics
from robotics.simulator import render_robot_simulation
from safety.gate import safety_check
from vision.detect import capture_vision_state

app = FastAPI(title="AIoT Robot Pick & Place - Phú")
robot = RobotArm()

OBJECT_LABELS = {
    "chai_nuoc": "Chai nước",
    "coc": "Cốc",
    "but": "Bút",
    "dien_thoai": "Điện thoại",
    "hop": "Hộp",
    "keo": "Kéo",
}

STYLES = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body {
  margin: 0; color: #e2e8f0; font-family: Inter, system-ui, Arial, sans-serif;
  background: radial-gradient(circle at top left, #16325c 0, #0b1220 38%, #060a12 100%);
  min-height: 100vh;
}
.shell { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 38px 0 56px; }
.eyebrow { color: #38bdf8; font-size: 12px; font-weight: 800; letter-spacing: .18em; }
h1 { margin: 8px 0 10px; font-size: clamp(30px, 5vw, 52px); line-height: 1.05; }
.lead { color: #94a3b8; margin: 0 0 28px; max-width: 720px; }
.card {
  background: rgba(15, 23, 42, .82); border: 1px solid #26344c; border-radius: 20px;
  box-shadow: 0 18px 55px rgba(0, 0, 0, .28); padding: 24px;
}
.command-form { display: flex; gap: 12px; }
input {
  flex: 1; min-width: 0; border: 1px solid #334155; border-radius: 12px; padding: 15px 16px;
  background: #0b1220; color: white; font-size: 16px; outline: none;
}
input:focus { border-color: #38bdf8; box-shadow: 0 0 0 3px rgba(56, 189, 248, .12); }
button {
  border: 0; border-radius: 12px; padding: 0 22px; background: linear-gradient(135deg, #38bdf8, #2563eb);
  color: white; font-weight: 800; cursor: pointer;
}
.toolbar { display: flex; justify-content: flex-end; margin-bottom: 18px; }
.button-link {
  display: inline-flex; align-items: center; justify-content: center; border: 1px solid #334155;
  border-radius: 12px; padding: 11px 16px; background: rgba(15, 23, 42, .72);
  color: #e2e8f0; font-weight: 750; text-decoration: none;
}
.button-link:hover { border-color: #38bdf8; color: #7dd3fc; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 18px; }
.section-title { margin: 0 0 16px; font-size: 13px; color: #7dd3fc; letter-spacing: .14em; }
.row { display: flex; justify-content: space-between; gap: 16px; padding: 9px 0; border-bottom: 1px solid #1e293b; }
.row:last-child { border: 0; }
.muted { color: #94a3b8; }
.ok { color: #4ade80; font-weight: 750; }
.bad { color: #fb7185; font-weight: 750; }
.pill {
  display: inline-block; border: 1px solid #334155; border-radius: 999px; padding: 5px 10px;
  color: #cbd5e1; background: #111c30; font-size: 12px;
}
.objects { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
.object { padding: 10px 13px; border-radius: 10px; background: rgba(30, 41, 59, .75); color: #cbd5e1; }
.vision-grid { display: grid; grid-template-columns: 1.35fr .9fr; gap: 18px; margin-top: 18px; }
.camera-box {
  min-height: 330px; border: 1px solid #26344c; border-radius: 16px; overflow: hidden;
  background: #050914; display: flex; align-items: center; justify-content: center;
}
.camera-box img { display: block; width: 100%; height: 100%; object-fit: contain; }
.camera-placeholder { color: #64748b; text-align: center; padding: 32px; }
.detections { display: grid; gap: 10px; }
.detection {
  border: 1px solid #26344c; border-radius: 14px; padding: 12px 14px;
  background: rgba(15, 23, 42, .76);
}
.detection-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.coord { color: #94a3b8; font-size: 13px; line-height: 1.55; }
.sim { margin-top: 18px; }
.sim img { display: block; width: 100%; border-radius: 14px; border: 1px solid #26344c; }
.back { display: inline-block; margin-top: 18px; color: #7dd3fc; text-decoration: none; }
.warning { margin-top: 15px; color: #fbbf24; font-size: 13px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { padding: 14px 12px; border-bottom: 1px solid #1e293b; text-align: left; }
th { color: #7dd3fc; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }
td { color: #cbd5e1; }
tr:last-child td { border-bottom: 0; }
.result-pill {
  display: inline-block; min-width: 88px; border-radius: 999px; padding: 5px 10px;
  text-align: center; font-size: 12px; font-weight: 800;
}
.result-success { color: #86efac; background: rgba(34, 197, 94, .13); border: 1px solid rgba(34, 197, 94, .3); }
.result-rejected { color: #fda4af; background: rgba(244, 63, 94, .12); border: 1px solid rgba(244, 63, 94, .3); }
.empty { color: #94a3b8; text-align: center; padding: 36px 12px; }
@media (max-width: 800px) {
  .grid { grid-template-columns: 1fr; }
  .vision-grid { grid-template-columns: 1fr; }
  .command-form { flex-direction: column; }
  button { padding: 15px; }
}
"""


def page(content: str) -> str:
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>AIoT Robot Dashboard</title><style>{STYLES}</style></head>
<body><main class="shell">{content}</main></body></html>"""


def object_name(value: str | None) -> str:
    return OBJECT_LABELS.get(value or "", value or "Chưa xác định")


def format_bbox(obj: Dict) -> str:
    bbox = obj.get("bbox")
    if not bbox:
        return "bbox: chưa có"
    return (
        f"bbox: ({bbox['x1']:.0f}, {bbox['y1']:.0f}) → "
        f"({bbox['x2']:.0f}, {bbox['y2']:.0f})"
    )


def render_detection_card(obj: Dict) -> str:
    pixel = "pixel: chưa có"
    if "u" in obj and "v" in obj:
        pixel = f"pixel: ({obj['u']:.0f}, {obj['v']:.0f})"

    return f"""
      <div class="detection">
        <div class="detection-head">
          <strong>{escape(object_name(obj.get("class_name")))}</strong>
          <span class="pill">{obj.get("confidence", 0):.0%}</span>
        </div>
        <div class="coord">{escape(pixel)}</div>
        <div class="coord">robot: ({obj["x_mm"]:.1f}, {obj["y_mm"]:.1f}, {obj["z_mm"]:.1f}) mm</div>
        <div class="coord">{escape(format_bbox(obj))}</div>
      </div>
    """


def execute_command(command: str) -> Dict:
    vision_state = capture_vision_state()
    detected_objects = vision_state["objects"]

    if not vision_state["fallback_used"]:
        for obj in detected_objects:
            append_csv("detection_log.csv", {
                "class": obj.get("class_name"),
                "confidence": obj.get("confidence"),
                "u_px": obj.get("u", ""),
                "v_px": obj.get("v", ""),
                "x_mm": obj.get("x_mm"),
                "y_mm": obj.get("y_mm"),
                "z_mm": obj.get("z_mm"),
                "backend": vision_state["backend"],
            })

    parsed = parse_command(command)
    decision = safety_check(parsed, detected_objects)

    append_csv("decision_log.csv", {
        "command": command,
        "parser": parsed.get("parser"),
        "target": decision.get("target_object"),
        "confidence": decision.get("confidence", ""),
        "allowed": decision.get("control_allowed"),
        "reason": decision.get("blocked_reason", ""),
    })

    result = {
        "parsed_command": parsed,
        "decision": decision,
        "vision": {
            "backend": vision_state["backend"],
            "fallback_used": vision_state["fallback_used"],
            "warning": vision_state["warning"],
            "camera_frame": vision_state["camera_frame"],
        },
        "detected_objects": detected_objects,
        "status": "REJECTED",
    }
    if not decision["control_allowed"]:
        return result

    try:
        pose = decision["target_pose"]
        ik_pick = inverse_kinematics(pose["x_mm"], pose["y_mm"], pose["z_mm"])
        ik_drop = inverse_kinematics(
            DROP_ZONE["x_mm"], DROP_ZONE["y_mm"], DROP_ZONE["z_mm"]
        )

        robot.home_all()
        robot.gripper(open=True)
        robot.move_joints(ik_pick["joints_deg"])
        robot.gripper(open=False)
        robot.move_joints(ik_drop["joints_deg"])
        robot.gripper(open=True)

        result.update({
            "ik_pick": ik_pick,
            "ik_drop": ik_drop,
            "robot_pose": robot.get_pose(),
            "simulation_image": render_robot_simulation(pose, ik_pick),
            "pick_success": True,
            "place_success": True,
            "status": "SIMULATED_SUCCESS",
        })
        append_csv("action_log.csv", {
            "target": decision.get("target_object"),
            "pick_joints": ik_pick["joints_deg"],
            "drop_joints": ik_drop["joints_deg"],
            "result": "simulated_success",
        })
    except (ValueError, RuntimeError) as exc:
        result["decision"]["control_allowed"] = False
        result["decision"]["blocked_reason"] = str(exc)
        result["status"] = "CONTROL_REJECTED"
        append_csv("action_log.csv", {
            "target": decision.get("target_object"),
            "pick_joints": result.get("ik_pick", {}).get("joints_deg", ""),
            "drop_joints": result.get("ik_drop", {}).get("joints_deg", ""),
            "result": "failed",
            "reason": str(exc),
        })

    return result


@app.get("/", response_class=HTMLResponse)
def home():
    vision_state = capture_vision_state()
    objects = vision_state["objects"]
    objects_html = "".join(
        f"""<div class="object"><strong>{escape(object_name(o["class_name"]))}</strong>
        · {o["confidence"]:.0%} · ({o["x_mm"]:.1f}, {o["y_mm"]:.1f}, {o["z_mm"]:.1f}) mm</div>"""
        for o in objects
    )
    detections_html = "".join(render_detection_card(o) for o in objects) or (
        '<div class="empty">Camera chưa phát hiện vật thể.</div>'
    )
    camera_html = (
        f'<img src="{vision_state["camera_frame"]}" alt="Camera YOLO bounding boxes">'
        if vision_state["camera_frame"]
        else '<div class="camera-placeholder">Chưa có frame camera.<br>Dashboard đang dùng dữ liệu fallback/mock.</div>'
    )
    warning_html = (
        f'<div class="warning">⚠ Vision warning: {escape(vision_state["warning"])}</div>'
        if vision_state["warning"] else ""
    )
    return page(f"""
      <div class="eyebrow">AIOT ROBOT CONTROL</div>
      <h1>Pick & Place Dashboard</h1>
      <p class="lead">Nhập lệnh tiếng Việt. Ollama phân tích ý định, Safety Gate kiểm tra
      vật thể và vùng làm việc, sau đó IK điều khiển robot mô phỏng.</p>
      <div class="toolbar">
        <a class="button-link" href="/history">☷ Command History</a>
      </div>
      <section class="card">
        <form class="command-form" action="/command" method="post">
          <input name="command" aria-label="Lệnh robot" value="gắp chai nước"
                 placeholder="Ví dụ: gắp chai nước" required autofocus>
          <button type="submit">Chạy lệnh</button>
        </form>
        <div class="objects">{objects_html}</div>
        {warning_html}
      </section>
      <section class="card sim">
        <h2 class="section-title">CAMERA + YOLO11N</h2>
        <div class="row"><span class="muted">Backend</span><span class="pill">{escape(vision_state["backend"])}</span></div>
        <div class="vision-grid">
          <div class="camera-box">{camera_html}</div>
          <div class="detections">{detections_html}</div>
        </div>
      </section>
    """)


@app.get("/history", response_class=HTMLResponse)
def command_history():
    records = read_csv("decision_log.csv", limit=100)
    if records:
        rows_html = "".join(history_row(record) for record in records)
        table_html = f"""
          <div class="table-wrap">
            <table>
              <thead><tr>
                <th>Time</th><th>Command</th><th>Object</th><th>Confidence</th>
                <th>Result</th><th>Parser</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
        """
    else:
        table_html = '<div class="empty">Chưa có lệnh nào được ghi lại.</div>'

    return page(f"""
      <div class="eyebrow">SYSTEM MONITORING</div>
      <h1>Command History</h1>
      <p class="lead">100 quyết định gần nhất từ Safety Gate, mới nhất hiển thị trước.</p>
      <section class="card">{table_html}</section>
      <a class="back" href="/">← Quay lại Dashboard</a>
    """)


def history_row(record: Dict) -> str:
    allowed = str(record.get("allowed", "")).strip().lower() == "true"
    result_text = "✓ Success" if allowed else "✕ Rejected"
    result_class = "result-success" if allowed else "result-rejected"
    timestamp = record.get("time", "")
    display_time = timestamp.replace("T", " ")
    confidence = record.get("confidence", "") or "—"
    target = object_name(record.get("target"))
    parser = record.get("parser", "") or "legacy"
    reason = record.get("reason", "")
    result_title = f' title="{escape(reason)}"' if reason else ""

    return f"""
      <tr>
        <td>{escape(display_time)}</td>
        <td><strong>{escape(record.get("command", ""))}</strong></td>
        <td>{escape(target)}</td>
        <td>{escape(confidence)}</td>
        <td><span class="result-pill {result_class}"{result_title}>{result_text}</span></td>
        <td><span class="pill">{escape(parser)}</span></td>
      </tr>
    """


@app.post("/command", response_class=HTMLResponse)
def run_command(command: str = Form(...)):
    result = execute_command(command)
    parsed = result["parsed_command"]
    decision = result["decision"]
    vision_state = result["vision"]
    allowed = decision["control_allowed"]
    confidence = decision.get("confidence")
    confidence_text = f"{confidence:.2f}" if confidence is not None else "N/A"
    parser_warning = parsed.get("parser_warning")
    target_prefix = "✓ " if decision.get("target_object") else ""

    if allowed:
        joints = result["ik_pick"]["joints_deg"]
        ik_html = "".join(
            f'<div class="row"><span>J{i}</span><strong>{angle:.2f}°</strong></div>'
            for i, angle in enumerate(joints, start=1)
        )
        robot_html = """
          <div class="row"><span>Pick</span><span class="ok">✓ Success</span></div>
          <div class="row"><span>Place</span><span class="ok">✓ Success</span></div>
        """
        simulation = f"""<section class="card sim">
          <h2 class="section-title">ROBOT 2D SIMULATION</h2>
          <img src="{result["simulation_image"]}" alt="Mô phỏng cánh tay robot">
        </section>"""
    else:
        ik_html = f'<div class="bad">Không chạy IK: {escape(decision["blocked_reason"])}</div>'
        robot_html = '<div class="row"><span>Thao tác</span><span class="bad">✕ Bị chặn an toàn</span></div>'
        simulation = ""

    warning_html = (
        f'<div class="warning">⚠ {escape(parser_warning)}</div>' if parser_warning else ""
    )
    vision_warning_html = (
        f'<div class="warning">⚠ Vision warning: {escape(vision_state["warning"])}</div>'
        if vision_state.get("warning") else ""
    )
    camera_html = (
        f'<img src="{vision_state["camera_frame"]}" alt="Camera YOLO bounding boxes">'
        if vision_state.get("camera_frame")
        else '<div class="camera-placeholder">Chưa có frame camera.<br>Đang dùng dữ liệu fallback/mock.</div>'
    )
    detections_html = "".join(
        render_detection_card(o) for o in result["detected_objects"]
    ) or '<div class="empty">Camera chưa phát hiện vật thể.</div>'
    allowed_html = (
        '<span class="ok">✓ Cho phép thao tác</span>'
        if allowed else '<span class="bad">✕ Không cho phép</span>'
    )

    return page(f"""
      <div class="eyebrow">COMMAND RESULT</div>
      <h1>{escape(command)}</h1>
      <p class="lead">Kết quả xử lý hoàn chỉnh từ ngôn ngữ tự nhiên đến robot mô phỏng.</p>
      <div class="grid">
        <section class="card">
          <h2 class="section-title">AI DECISION</h2>
          <div class="row"><span class="muted">Vật thể</span><strong>{target_prefix}{escape(object_name(decision.get("target_object")))}</strong></div>
          <div class="row"><span class="muted">Confidence</span><strong>{confidence_text}</strong></div>
          <div class="row"><span class="muted">Safety Gate</span>{allowed_html}</div>
          <div class="row"><span class="muted">Parser</span><span class="pill">{escape(parsed.get("parser", "unknown"))}</span></div>
          {warning_html}
        </section>
        <section class="card">
          <h2 class="section-title">IK RESULT</h2>
          {ik_html}
        </section>
        <section class="card">
          <h2 class="section-title">ROBOT STATUS</h2>
          {robot_html}
        </section>
      </div>
      <section class="card sim">
        <h2 class="section-title">CAMERA + YOLO11N</h2>
        <div class="row"><span class="muted">Backend</span><span class="pill">{escape(vision_state["backend"])}</span></div>
        {vision_warning_html}
        <div class="vision-grid">
          <div class="camera-box">{camera_html}</div>
          <div class="detections">{detections_html}</div>
        </div>
      </section>
      {simulation}
      <a class="back" href="/">← Nhập lệnh khác</a>
      &nbsp;&nbsp;·&nbsp;&nbsp;
      <a class="back" href="/history">Command History</a>
    """)


@app.post("/api/command")
def run_command_api(command: str = Form(...)):
    """Endpoint JSON dành cho tích hợp và kiểm thử."""
    result = execute_command(command)
    result.pop("simulation_image", None)
    result.get("vision", {}).pop("camera_frame", None)
    return result
