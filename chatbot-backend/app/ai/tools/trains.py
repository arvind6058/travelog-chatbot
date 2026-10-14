"""Train tools. Live running status is never fabricated."""
from typing import Dict, Any, Optional

from app.core.config import get_settings
from app.providers.trains import TrainProvider


def _provider() -> TrainProvider:
    return TrainProvider(mode=get_settings().TRAIN_PROVIDER)


def searchTrains(origin: str, destination: str) -> Dict[str, Any]:
    """Execute searchTrains tool using TrainProvider."""
    return _provider().search_trains(origin=origin, destination=destination)


def getTrainStatus(train_number_or_name: Optional[str]) -> Dict[str, Any]:
    """Execute getTrainStatus tool using TrainProvider."""
    return _provider().get_train_status(train_number_or_name=train_number_or_name or "")
