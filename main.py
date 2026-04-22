import sys
import os

if sys.platform == "darwin":
    os.environ.setdefault("CTK_SCALE", "1.0")

from wizard.app import WizardApp

if __name__ == "__main__":
    app = WizardApp()
    app.mainloop()
