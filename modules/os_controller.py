from pywinauto.application import Application
from pywinauto import Desktop
from utils.logger import get_logger

logger = get_logger("OS_Controller")

class OSController:
    def click_element(self, app_title, element_title):
        """Interacts directly with the Windows UI tree."""
        logger.info(f"Attempting OS Control: App '{app_title}', Element '{element_title}'")
        try:
            app = Application(backend="uia").connect(title_re=f".*{app_title}.*")
            window = app.top_window()
            # Find the button/element and click it directly via OS API
            window.child_window(title=element_title).click_input()
            logger.info(f"Successfully clicked '{element_title}' via OS Control.")
            return True
        except Exception as e:
            logger.error(f"OS Control Failed: {e}")
            return False
    def focus_app(self, app_name):
        """Forces Windows to bring an app to the front and focus it."""
        try:
            from pywinauto import Application
            # Connect to the app by its name
            app = Application(backend="uia").connect(title_re=f".*{app_name}.*", timeout=10)
            app.top_window().set_focus()
            logger.info(f"Successfully focused: {app_name}")
            return True
        except Exception as e:
            logger.error(f"Could not focus {app_name}: {e}")
            return False

    def list_open_windows(self, limit=30):
        """Returns visible top-level window titles from the OS UI tree."""
        try:
            windows = Desktop(backend="uia").windows()
            titles = []
            seen = set()
            for w in windows:
                title = (w.window_text() or "").strip()
                if not title:
                    continue
                lowered = title.lower()
                if lowered in seen:
                    continue
                # Filter noisy/system windows that are rarely useful to users.
                if lowered in {"program manager", "task switching"}:
                    continue
                seen.add(lowered)
                titles.append(title)

            return titles[:limit]
        except Exception as e:
            logger.error(f"Could not enumerate open windows: {e}")
            return []

    def focus_terminal_window(self):
        """Try to bring a command terminal back to foreground."""
        try:
            terminal_keywords = [
                "command prompt",
                "cmd",
                "powershell",
                "windows terminal",
                "python",
                "main.py",
                "antigravity",
                "antygravity",
            ]
            windows = Desktop(backend="uia").windows()
            for w in windows:
                title = (w.window_text() or "").strip()
                if not title:
                    continue
                lowered = title.lower()
                if any(keyword in lowered for keyword in terminal_keywords):
                    try:
                        w.set_focus()
                        logger.info(f"Focused terminal window: {title}")
                        return True
                    except Exception:
                        continue

            logger.warning("No terminal-like window found to focus.")
            return False
        except Exception as e:
            logger.error(f"Could not refocus terminal window: {e}")
            return False