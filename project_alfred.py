import argparse, sys
from Orisa import Orisa



parser = argparse.ArgumentParser(description='Run the bot')
parser.add_argument('environment', metavar="env", type=str, help='test or live environment')
args = parser.parse_args()

if args.environment.lower() == "test":
    try:
        from config_alfred import ALFRED_TOKEN, channels, roles, bot_tasks
        TOKEN = ALFRED_TOKEN
    except ImportError:
        print("Error importing beta config, please make sure you have the right files")
        sys.exit(2)
elif args.environment.lower() == "live":
    try:    
        from config_orisa import ORISA_TOKEN, channels, roles, bot_tasks
        TOKEN = ORISA_TOKEN
    except ImportError:
        print("Error importing live config, please make sure you have the correct files")
        sys.exit(2)
else:
    print("Got argument '{}' for env, expected 'test/live'".format(args.environment))
    sys.exit(1)

o = Orisa(TOKEN, channels, roles, bot_tasks)
o.start()
