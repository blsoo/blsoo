import unittest
from datetime import date
from unittest.mock import patch

from bs4 import BeautifulSoup

from app.checker import (
    EMAIL_RE,
    NAME_RE,
    PHONE_RE,
    _candidate_links,
    _date_end,
    _extract_dates,
    _field_text,
    _telegram_wrapper_check,
    _utm_evidence,
    validate_target,
)


class CheckerHelpersTest(unittest.TestCase):
    def test_conflicting_dates_are_extractable(self):
        dates = _extract_dates("Конференция 13–14 марта 2026. FAQ: 13-14.04.2026")
        self.assertTrue(any(".03.2026" in value for value in dates), dates)
        self.assertTrue(any(".04.2026" in value for value in dates), dates)

    def test_date_end_understands_ranges(self):
        self.assertEqual(_date_end("13-14.04.2026"), date(2026, 4, 14))
        self.assertEqual(_date_end("13.04.2026"), date(2026, 4, 13))
        self.assertIsNone(_date_end("13-14.03.????"))

    def test_registration_fields(self):
        html = '''<form>
        <label for="n">Имя</label><input id="n" name="name" required>
        <input type="tel" name="phone" placeholder="Телефон">
        <input type="email" name="email" placeholder="Email">
        </form>'''
        soup = BeautifulSoup(html, "html.parser")
        fields = soup.find_all("input")
        texts = [_field_text(field) for field in fields]
        self.assertTrue(any(NAME_RE.search(value) for value in texts))
        self.assertTrue(any(PHONE_RE.search(value) for value in texts))
        self.assertTrue(any(EMAIL_RE.search(value) for value in texts))

    def test_links_are_deduplicated(self):
        soup = BeautifulSoup('<a href="/a">A</a><a href="/a">A2</a>', "html.parser")
        self.assertEqual(_candidate_links(soup, "https://example.com/x"), ["https://example.com/a"])

    def test_utm_dojim_is_detected(self):
        links = [
            "https://example.com/?utm_source=telegram&utm_medium=dojim",
            "https://example.com/a?utm_source=telegram&utm_medium=organic",
        ]
        utm, dojim = _utm_evidence(links)
        self.assertEqual(len(utm), 2)
        self.assertEqual(dojim, [links[0]])

    def test_telegram_startapp_is_marked_manual(self):
        check = _telegram_wrapper_check("https://t.me/test_bot/aboutme?startapp=a_123")
        self.assertIsNotNone(check)
        self.assertEqual(check.status, "manual")

    def test_credentials_in_url_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_target("https://user:password@example.com")

    @patch("app.checker._host_is_public", return_value=False)
    def test_private_target_is_rejected(self, _mock):
        with self.assertRaises(ValueError):
            validate_target("http://127.0.0.1")


if __name__ == "__main__":
    unittest.main()
