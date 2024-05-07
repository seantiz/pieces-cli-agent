import os
import pyperclip

from pieces.utils import get_file_extension,extract_code_from_markdown,sanitize_filename
from .assets_api import AssetsCommandsApi
from pieces.gui import show_error,print_model_details,space_below,double_line
from pieces.settings import Settings


def check_assets_existence(func):
    """Decorator to ensure user has assets."""
    def wrapper(*args, **kwargs):
        try:
            assets = AssetsCommandsApi.get_asset_ids(1) # Check if there is an asset
            if not assets:
                raise Exception("No assets found")
            return func(*args, **kwargs)
        except:
            return show_error("No assets found", "Please create an asset first.")
        
    return wrapper


def check_asset_selected(func):
    """
    Decorator to check if there is a selected asset or not and if it is valid id.
    If valid id it returns the asset_data to the called function.
    """
    def wrapper(*args, **kwargs):
        if current_asset is None:
            return show_error("No asset selected.", "Please open an asset first using pieces open.")
        try: 
            asset_data = AssetsCommandsApi.get_asset_by_id(current_asset)
            return func(asset_data=asset_data,*args, **kwargs)
        except:
            # The selected asset is deleted
            return show_error("Error occured in the command", "Please make sure the selected asset is valid.")
            
            
    return wrapper

class AssetsCommands:
    current_asset = None

    @check_assets_existence
    def open_asset(**kwargs):
        global current_asset
        item_index = kwargs.get('ITEM_INDEX',1)
        if not item_index: item_index = 1
        asset_ids = AssetsCommandsApi.get_assets_info_list(item_index)
        try:
            asset_id = asset_ids[item_index-1].get('id') # because we begin from 1
        except IndexError:
            show_error("Invalid asset index or asset not found.","Please choose from the list or use 'pieces list assets'")
            return
        
        current_asset = asset_id  
        open_asset = AssetsCommandsApi.get_asset_by_id(asset_id)
        asset_dict = AssetsCommandsApi.extract_asset_info(open_asset)
        

        filepath = extract_code_from_markdown(asset_dict["raw"], asset_dict["name"], asset_dict["language"])

        print_model_details(asset_dict["name"],asset_dict["created_at"],asset_dict["updated_at"],asset_dict["type"],asset_dict["language"],filepath)



    @check_asset_selected
    def update_asset(asset_data,**kwargs):
        asset = AssetsCommandsApi.extract_asset_info(asset_data)
        file_path = os.path.join(Settings.open_snippet_dir , f"{sanitize_filename(asset["name"])}{get_file_extension(asset["language"])}")
        print(f"Saving {file_path} to {asset['name']} snippet with uuid {current_asset}")

        
        # Pass asset and file name
        AssetsCommandsApi.update_asset_value(file_path, current_asset)


    @check_asset_selected
    def edit_asset(asset_data,**kwargs):
        global current_asset
        asset_dict = AssetsCommandsApi.extract_asset_info(asset_data)
        print_model_details(asset_dict["name"],asset_dict["created_at"],asset_dict["updated_at"],asset_dict["type"],asset_dict["language"])
        
        name = kwargs.get('name', '')
        classification = kwargs.get('classification', '')

        if not name and not classification: # If no name or no classification is provided
            # Ask the user for a new name
            name = input("Enter the new name for the asset[leave blank to keep the same]: ").strip()
            classification = input("Enter the classification for the asset[leave blank to keep the same]: ").strip()

        # Check if the user actually entered a name
        if name:
            AssetsCommandsApi.edit_asset_name(current_asset, name)
        if classification:
            AssetsCommandsApi.reclassify_asset(current_asset, classification)

    @check_asset_selected
    def delete_asset(asset_data,**kwargs):
        global current_asset
        # Ask the user for confirmation before deleting
        # print()
        # open_asset()
        asset_dict = AssetsCommandsApi.extract_asset_info(asset_data)
        print_model_details(asset_dict["name"],asset_dict["created_at"],asset_dict["updated_at"],asset_dict["type"],asset_dict["language"])

        confirm = input("Are you sure you really want to delete this asset? This action cannot be undone. (y/n): ").strip().lower()
        if confirm == 'y':
            print("Deleting asset...")
            AssetsCommandsApi.delete_asset_by_id(current_asset)
            current_asset = None
            space_below("Asset Deleted")
        elif confirm == 'n':
            print("Deletion cancelled.")
        else:
            print("Invalid input. Please type 'y' to confirm or 'n' to cancel.")
        

    def create_asset(**kwargs):
        global current_asset
        # TODO add more ways to create an asset such as an entire file

        # Save text copied to the clipboard as an asset
        try:
            text = pyperclip.paste()
            double_line("Content to save: ")
            space_below(text)

            # Ask the user for confirmation to save
            user_input = input("Do you want to save this content? (y/n): ").strip().lower()
            if user_input == 'y':
                space_below("Saving Content...")
                new_asset = AssetsCommandsApi.create_new_asset(Settings.application, raw_string=text, metadata=None)
        
                current_asset = new_asset.id
                print(f"Asset Created use 'open' to view")

                return new_asset
                # Add your saving logic here
            elif user_input == 'n':
                space_below("Save Cancelled")
            else:
                print("Invalid input. Please type 'y' to save or 'n' to cancel.")

        except pyperclip.PyperclipException as e:
            show_error("Error accessing clipboard:", str(e))





