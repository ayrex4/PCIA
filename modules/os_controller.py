from pywinauto.application import Application
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