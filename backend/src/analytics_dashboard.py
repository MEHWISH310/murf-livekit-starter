import http.server
import socketserver
import html
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from db import get_call_stats, get_recent_calls

PORT = 8788

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="10">
<title>Kisan Sahay — Call Analytics</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #f7fee7; margin: 0; padding: 24px; }}
  h1 {{ color: #365314; }}
  .subtitle {{ color: #4d7c0f; margin-bottom: 24px; }}
  .cards {{ display: flex; gap: 16px; margin-bottom: 32px; flex-wrap: wrap; }}
  .card {{ background: white; border-radius: 8px; padding: 20px 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 140px; }}
  .card .num {{ font-size: 32px; font-weight: 700; color: #365314; }}
  .card .label {{ font-size: 13px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}
  .card.success .num {{ color: #166534; }}
  .card.failed .num {{ color: #991b1b; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th, td {{ text-align: left; padding: 12px 16px; border-bottom: 1px solid #e5e5e5; font-size: 14px; }}
  th {{ background: #365314; color: white; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{ padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
  .success {{ background: #dcfce7; color: #166534; }}
  .failure {{ background: #fee2e2; color: #991b1b; }}
  .in_progress {{ background: #fef3c7; color: #92400e; }}
  .empty {{ padding: 40px; text-align: center; color: #6b7280; background: white; border-radius: 8px; }}
</style>
</head>
<body>
  <h1>Kisan Sahay — Call Analytics</h1>
  <p class="subtitle">Auto-refreshes every 10 seconds &middot; Success = weather delivered, scheme info delivered, or escalation created</p>
  <div class="cards">
    <div class="card"><div class="num">{total}</div><div class="label">Total Calls</div></div>
    <div class="card success"><div class="num">{success}</div><div class="label">Successful</div></div>
    <div class="card failed"><div class="num">{failed}</div><div class="label">Failed</div></div>
    <div class="card"><div class="num">{success_rate}%</div><div class="label">Success Rate</div></div>
  </div>
  {content}
</body>
</html>
"""

ROW_TEMPLATE = """
<tr>
  <td>#{id}</td>
  <td>{channel}</td>
  <td>{farmer_name}</td>
  <td><span class="badge {outcome}">{outcome}</span></td>
  <td>{reason}</td>
  <td>{started_at}</td>
</tr>
"""


class AnalyticsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        stats = get_call_stats()
        calls = get_recent_calls()

        success_rate = round((stats["success"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0

        if not calls:
            content = '<div class="empty">No calls recorded yet.</div>'
        else:
            rows = ""
            for c in calls:
                rows += ROW_TEMPLATE.format(
                    id=c["id"],
                    channel=html.escape(c["channel"]),
                    farmer_name=html.escape(c["farmer_name"] or "-"),
                    outcome=html.escape(c["outcome"]),
                    reason=html.escape(c["reason"] or "-"),
                    started_at=html.escape(c["started_at"]),
                )
            content = f"""
            <table>
              <tr>
                <th>ID</th><th>Channel</th><th>Farmer</th><th>Outcome</th><th>Reason</th><th>Started</th>
              </tr>
              {rows}
            </table>
            """

        page = PAGE_TEMPLATE.format(
            total=stats["total"],
            success=stats["success"],
            failed=stats["failed"],
            success_rate=success_rate,
            content=content,
        )

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), AnalyticsHandler) as httpd:
        print(f"Analytics dashboard running at http://localhost:{PORT}")
        httpd.serve_forever()