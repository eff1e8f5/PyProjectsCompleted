# import json
from pathlib import Path

# dir list
dir_data = 'data'
dir_log = 'logs'
dir_main = Path(__file__).parent
dir_tmp = 'tmp'

# load variables data
# variables_data = json.load(
#     open(Path(dir_main, dir_data, 'variables_data.json'), 'r')
# )

# variables
tg_api_hash = '5eb321baf44354c849ba072a6950f85c'
tg_api_id = '10317722'
tg_bot_token = '6129444457:AAE_qMLlYmRcI8eVCjxXL4ONZc0OQoAgbgE'  # @CrowdTestingMirPayBot

# other
group_id = -1001939368056
db_name = 'crowdtesting_test'  # test db
db_user = 'test_user'
db_password = 'testpassword'
db_host = '172.17.0.3'  # in docker
db_port = '5432'
bot_name = '@CrowdTestingMirPayBot'