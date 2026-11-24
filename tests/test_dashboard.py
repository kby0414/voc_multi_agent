"""고객 문의 화면과 관리자 화면 경로·정적 자산 검증."""

from __future__ import annotations

import unittest
from pathlib import Path

from app.main import STATIC_DIR, admin_dashboard, admin_inbox, app, customer_voc, dashboard


class DashboardTests(unittest.TestCase):
    def test_admin_dashboard_is_available(self) -> None:
        response = admin_dashboard()
        html = Path(response.path).read_text(encoding="utf-8")
        self.assertIn(
            "/admin",
            {route.path for route in app.routes if hasattr(route, "path")},
        )
        self.assertIn("해결 우선순위", html)
        self.assertIn("실시간 문의함", html)
        self.assertNotIn('id="live-voc-form"', html)
        self.assertIn("/static/dashboard.js", html)

    def test_customer_portal_and_admin_inbox_are_separated(self) -> None:
        customer_html = Path(customer_voc().path).read_text(encoding="utf-8")
        inbox_html = Path(admin_inbox().path).read_text(encoding="utf-8")
        self.assertIn('id="voc-form"', customer_html)
        self.assertIn("게임 이름", customer_html)
        self.assertIn("플랫폼", customer_html)
        self.assertNotIn("유입 채널", customer_html)
        self.assertNotIn("관리자 화면", customer_html)
        self.assertIn("문의가 정상적으로", customer_html)
        self.assertIn('id="inbox-list"', inbox_html)
        self.assertIn('id="inbox-detail"', inbox_html)

    def test_old_dashboard_route_redirects_to_admin(self) -> None:
        response = dashboard()
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/admin")

    def test_dashboard_assets_are_available(self) -> None:
        css = (STATIC_DIR / "dashboard.css").read_text(encoding="utf-8")
        javascript = (STATIC_DIR / "dashboard.js").read_text(encoding="utf-8")
        customer_js = (STATIC_DIR / "voc.js").read_text(encoding="utf-8")
        inbox_js = (STATIC_DIR / "inbox.js").read_text(encoding="utf-8")
        self.assertIn("priority-panel", css)
        self.assertIn("inbox-layout", css)
        self.assertIn("loadDashboard", javascript)
        self.assertNotIn("live-demo-panel", css)
        self.assertIn("/api/v1/vocs/intake", customer_js)
        self.assertIn("/api/v1/admin/vocs", inbox_js)


if __name__ == "__main__":
    unittest.main()
