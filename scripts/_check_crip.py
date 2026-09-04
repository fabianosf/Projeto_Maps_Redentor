import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from dal_util import create_dal, scalar
dal = create_dal()
print(dal.read('SHOW DATABASES').to_string())
n = scalar(dal, "SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema='crip'", column='n')
print('crip tables:', n)
