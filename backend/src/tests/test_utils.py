from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db_session(mocker):
    # Mock the session to avoid real database writes
    session = MagicMock(spec=Session)
    mocker.patch("src.init_db.load_data.SessionLocal", return_value=session)
    return session
