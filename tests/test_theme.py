import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui import theme  # noqa: E402

DESIGN = os.path.join(os.path.dirname(__file__), '..', 'DESIGN.md')


def frontmatter_section(name):
    """The key/value lines of one top level section of the DESIGN.md frontmatter"""
    with open(DESIGN, encoding='utf-8') as f:
        text = f.read().split('---')[1]
    match = re.search(rf'^{name}:\n((?:  .*\n)+)', text, re.MULTILINE)
    return match.group(1)


def flat_values(section):
    return {key: value.strip('"') for key, value in re.findall(r'^  ([\w-]+): (.+)$', section, re.MULTILINE)}


class ThemeMatchesDesignTest(unittest.TestCase):
    def test_colors(self):
        self.assertEqual(flat_values(frontmatter_section('colors')), theme.COLORS)

    def test_radius(self):
        design = {key: int(value.rstrip('px')) for key, value in flat_values(frontmatter_section('rounded')).items()}
        self.assertEqual(design, theme.RADIUS)

    def test_spacing(self):
        design = [int(value.rstrip('px')) for value in flat_values(frontmatter_section('spacing')).values()]
        self.assertEqual(design, theme.SPACING)

    def test_typography(self):
        section = frontmatter_section('typography')
        for name, (family, size, weight, line_height) in theme.TYPE.items():
            block = re.search(rf'^  {name}:\n((?:    .*\n)+)', section, re.MULTILINE).group(1)
            self.assertIn(f'fontFamily: "{family},', block, name)
            self.assertIn(f'fontSize: "{size}px"', block, name)
            self.assertIn(f'fontWeight: {weight}', block, name)
            self.assertIn(f'lineHeight: "{line_height}px"', block, name)

    def test_every_weight_used_has_a_bundled_font(self):
        for family, _, weight, _ in theme.TYPE.values():
            self.assertIn((family, weight), theme.FAMILIES)


if __name__ == '__main__':
    unittest.main()
