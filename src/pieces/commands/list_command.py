from pieces.settings import Settings
from collections.abc import Iterable
from pieces.assets import check_assets_existence, AssetsCommandsApi
from pieces_os_client.api.applications_api import ApplicationsApi
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from typing import List, Tuple
from pieces.assets.assets_command import AssetsCommands  # Import AssetsCommands

class PiecesSelectMenu:
    def __init__(self, menu_options: List[Tuple]):
        self.menu_options = menu_options
        self.current_selection = 0
        self.selected_index = None

    def get_menu_text(self):
        result = []
        for i, option in enumerate(self.menu_options):
            if i == self.current_selection:
                result.append(('class:selected', f'> {option[0]}\n'))
            else:
                result.append(('class:unselected', f'  {option[0]}\n'))
        return result

    def run(self):
        bindings = KeyBindings()

        @bindings.add('up')
        def move_up(event):
            if self.current_selection > 0:
                self.current_selection -= 1
            event.app.layout.focus(self.menu_window)

        @bindings.add('down')
        def move_down(event):
            if self.current_selection < len(self.menu_options) - 1:
                self.current_selection += 1
            event.app.layout.focus(self.menu_window)

        @bindings.add('enter')
        def select_option(event):
            self.selected_index = self.current_selection
            event.app.exit()

        menu_control = FormattedTextControl(text=self.get_menu_text)
        self.menu_window = Window(content=menu_control, always_hide_cursor=True)
        layout = Layout(HSplit([self.menu_window]))
        style = Style.from_dict({
            'selected': 'reverse',
            'unselected': ''
        })
        app = Application(layout=layout, key_bindings=bindings, style=style, full_screen=True)
        app.run()

        return self.selected_index

class ListCommand:
    selected_item = None

    @classmethod
    def list_command(cls, **kwargs):
        type = kwargs.get("type", "assets")
        max_assets = kwargs.get("max_assets", 10)
        if max_assets < 1:
            print("Max assets must be greater than 0")
            max_assets = 10
        
        if type == "assets":
            cls.list_assets(max_assets)
        elif type == "apps":
            cls.list_apps()
        elif type == "models":
            cls.list_models()

    @classmethod
    @check_assets_existence
    def list_assets(cls, max_assets: int = 10):
        assets_snapshot = AssetsCommandsApi().assets_snapshot
        assets = []
        for i, uuid in enumerate(list(assets_snapshot.keys())[:max_assets], start=1):
            asset = assets_snapshot[uuid]
            if not asset:
                asset = AssetsCommandsApi.get_asset_snapshot(uuid)
            assets.append((f"{i}: {asset.name}", uuid))

        select_menu = PiecesSelectMenu(assets)
        selected_index = select_menu.run()
        
        if selected_index is not None:
            cls.selected_item = assets[selected_index][1]  # Store the UUID of the selected asset
            print(f"Selected asset: {assets[selected_index][0]}")
            AssetsCommands.current_asset = cls.selected_item
            AssetsCommands.open_asset()  # Call open_asset from AssetsCommands without arguments
        else:
            print("No asset selected.")

    @classmethod
    def list_models(cls):
        models = [(f"{idx}: {model_name}", model_name) for idx, model_name in enumerate(Settings.models, start=1)]
        models.append((f"Currently using: {Settings.model_name} with uuid {Settings.model_id}", Settings.model_id))

        select_menu = PiecesSelectMenu(models)
        selected_index = select_menu.run()

        if selected_index is not None:
            cls.selected_item = models[selected_index][1]
            print(f"\nSelected model: {models[selected_index][0]}")
        else:
            print("No model selected.")

    @classmethod
    def list_apps(cls):
        applications_api = ApplicationsApi(Settings.api_client)
        application_list = applications_api.applications_snapshot()

        if hasattr(application_list, 'iterable') and isinstance(application_list.iterable, Iterable):
            for i, app in enumerate(application_list.iterable, start=1):
                app_name = getattr(app, 'name', 'Unknown').value if hasattr(app, 'name') and hasattr(app.name, 'value') else 'Unknown'
                app_version = getattr(app, 'version', 'Unknown')
                app_platform = getattr(app, 'platform', 'Unknown').value if hasattr(app, 'platform') and hasattr(app.platform, 'value') else 'Unknown'
                print(f"{i}: {app_name}, {app_version}, {app_platform}")
        else:
            print("Error: The 'Applications' object does not contain an iterable list of applications.")
