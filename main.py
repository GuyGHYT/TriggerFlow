import os
from dotenv import load_dotenv

# Determine which .env file to use
env_file = 'creatoruser.env'
if not os.path.exists(env_file):
    env_file = 'user.env'

# Load the environment variables from the chosen file
if os.path.exists(env_file):
    print(f"Loading environment variables from {env_file}")
    load_dotenv(dotenv_path=env_file)
else:
    print("Warning: No .env file found (checked for creatoruser.env and user.env).")


import triggerflowlib as tfl

root = tfl.ui.CreateButtonLayout()
root.mainloop()
