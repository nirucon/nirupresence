import curses
import unittest
from nirupresence.tui import UI, MENU

class NavigationTests(unittest.TestCase):
    def test_k_always_navigates_up_in_settings(self):
        ui=UI.__new__(UI)
        ui.page='settings';ui.selected=5;ui.note=''
        self.assertTrue(ui.handle(ord('k')))
        self.assertEqual(ui.selected,4)
        self.assertEqual(ui.page,'settings')
    def test_enter_opens_selected_page(self):
        ui=UI.__new__(UI)
        ui.page='overview';ui.selected=3;ui.note=''
        self.assertTrue(ui.handle(10))
        self.assertEqual(ui.page,MENU[3][1])

if __name__=='__main__':unittest.main()
