            Settings.show_error("No changes found", "Please make sure you have added some files to your staging area")
        Settings.show_error(f"Error fetching current working changes: {e}")
        Settings.show_error("Error in getting the commit message",e)