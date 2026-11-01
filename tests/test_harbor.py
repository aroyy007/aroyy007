import copy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'render_harbor.py'
if SCRIPT.exists():
    spec = importlib.util.spec_from_file_location('harbor', SCRIPT)
    harbor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harbor)
else:
    harbor = None


class HarborTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            'account_id': 120275227,
            'contribution_history': {
                'observed_on': '2026-10-31',
                'days': [
                    {'date': '2026-10-29', 'contribution_count': 2},
                    {'date': '2026-10-30', 'contribution_count': 0},
                    {'date': '2026-10-31', 'contribution_count': 5},
                ],
            },
        }
        self.repos = [
            {'id': 1, 'name': 'ML_Study_Buddy', 'size': 100, 'fork': False, 'private': False, 'language': 'Python'},
            {'id': 2, 'name': 'fork', 'size': 300, 'fork': True, 'private': False},
            {'id': 3, 'name': 'private', 'size': 300, 'fork': False, 'private': True},
        ]

    def test_counts_real_activity_and_excludes_forks_and_private_repositories(self):
        self.assertIsNotNone(harbor, 'The harbor generator is missing')
        model = harbor.build_model(self.snapshot, self.repos)
        self.assertEqual(model['total'], 7)
        self.assertEqual(model['recent'], 7)
        self.assertEqual(model['active_days'], 2)
        self.assertEqual(model['public_repos'], 1)
        self.assertEqual([r['name'] for r in model['buildings']], ['ML_Study_Buddy'])

    def test_refuses_incomplete_history_instead_of_inventing_zero_activity(self):
        self.assertIsNotNone(harbor, 'The harbor generator is missing')
        broken = copy.deepcopy(self.snapshot)
        del broken['contribution_history']['days'][1]
        with self.assertRaises(ValueError):
            harbor.build_model(broken, self.repos)

    def test_external_repository_text_cannot_inject_svg_markup(self):
        self.assertIsNotNone(harbor, 'The harbor generator is missing')
        self.repos[0]['language'] = '<script>bad()</script>&'
        model = harbor.build_model(self.snapshot, self.repos)
        image = harbor.render(model, 'night', 'dark')
        parsed = ET.fromstring(image)
        self.assertIsNone(parsed.find('.//{http://www.w3.org/2000/svg}script'))
        self.assertIn('&lt;script&gt;', image)
        self.assertIn('7 contributions', ''.join(parsed.itertext()))

    def test_zero_activity_and_no_repositories_still_make_a_valid_city(self):
        self.assertIsNotNone(harbor, 'The harbor generator is missing')
        for day in self.snapshot['contribution_history']['days']:
            day['contribution_count'] = 0
        model = harbor.build_model(self.snapshot, [])
        self.assertEqual(model['active_days'], 0)
        for phase in ('dawn', 'day', 'dusk', 'night'):
            for theme in ('light', 'dark'):
                parsed = ET.fromstring(harbor.render(model, phase, theme))
                self.assertIn('0 contributions', ''.join(parsed.itertext()))

    def test_activity_chart_preserves_dates_and_does_not_invent_unobserved_days(self):
        self.assertIsNotNone(harbor, 'The harbor generator is missing')
        self.assertTrue(hasattr(harbor, 'render_activity'), 'The activity renderer is missing')
        model = harbor.build_model(self.snapshot, self.repos)
        parsed = ET.fromstring(harbor.render_activity(model, 'dark'))
        points = parsed.findall('.//{http://www.w3.org/2000/svg}circle')
        values = {p.get('data-date'): int(p.get('data-count')) for p in points}
        self.assertEqual(values, {'2026-10-29': 2, '2026-10-30': 0, '2026-10-31': 5})
        self.assertIn('7 contributions', ''.join(parsed.itertext()))


if __name__ == '__main__':
    unittest.main()
