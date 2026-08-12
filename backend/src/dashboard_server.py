import http.server
import socketserver
import html
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from db import get_all_escalations

PORT = 8787

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="10">
<title>Kisan Sahay — Escalation Requests</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #f7fee7; margin: 0; padding: 24px; }}
  h1 {{ color: #365314; }}
  .subtitle {{ color: #4d7c0f; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th, td {{ text-align: left; padding: 12px 16px; border-bottom: 1px solid #e5e5e5; font-size: 14px; }}
  th {{ background: #365314; color: white; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{ padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
  .open {{ background: #fef3c7; color: #92400e; }}
  .resolved {{ background: #dcfce7; color: #166534; }}
  .urgency-emergency {{ background: #fee2e2; color: #991b1b; }}
  .urgency-high {{ background: #ffedd5; color: #9a3412; }}
  .urgency-medium {{ background: #fef9c3; color: #854d0e; }}
  .urgency-low {{ background: #f0fdf4; color: #166534; }}
  .empty {{ padding: 40px; text-align: center; color: #6b7280; background: white; border-radius: 8px; }}
</style>
</head>
<body>
  <h1>Kisan Sahay — Human Help Requests</h1>
  <p class="subtitle">Auto-refreshes every 10 seconds &middot; {count} total request(s)</p>
  {content}
</body>
</html>
"""

ROW_TEMPLATE = """
<tr>
  <td>#{id}</td>
  <td>{farmer_name}</td>
  <td>{reason_category}</td>
  <td>{summary}</td>
  <td><span class="badge urgency-{urgency}">{urgency}</span></td>
  <td>{language}</td>
  <td>{follow_up_method}</td>
  <td><span class="badge {status}">{status}</span></td>
  <td>{created_at}</td>
</tr>
"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        escalations = get_all_escalations()

        if not escalations:
            content = '<div class="empty">No escalation requests yet.</div>'
        else:
            rows = ""
            for e in escalations:
                rows += ROW_TEMPLATE.format(
                    id=e["id"],
                    farmer_name=html.escape(e["farmer_name"]),
                    reason_category=html.escape(e["reason_category"]),
                    summary=html.escape(e["summary"]),
                    urgency=html.escape(e["urgency"]),
                    language=html.escape(e["language"] or "-"),
                    follow_up_method=html.escape(e["follow_up_method"] or "-"),
                    status=html.escape(e["status"]),
                    created_at=html.escape(e["created_at"]),
                )
            content = f"""
            <table>
              <tr>
                <th>ID</th><th>Farmer</th><th>Reason</th><th>Summary</th>
                <th>Urgency</th><th>Language</th><th>Follow-up</th><th>Status</th><th>Created</th>
              </tr>
              {rows}
            </table>
            """

        page = PAGE_TEMPLATE.format(count=len(escalations), content=content)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # keep terminal clean


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Dashboard running at http://localhost:{PORT}")
        httpd.serve_forever()