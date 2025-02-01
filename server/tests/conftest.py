import pytest
import sys
from pathlib import Path

# Add the server directory to Python path for imports
server_path = Path(__file__).parent.parent
sys.path.insert(0, str(server_path)) 