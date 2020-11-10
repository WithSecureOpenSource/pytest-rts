import pytest
import sys
sys.path.append(".")
from src.car import Car

def test_acceleration():
    car = Car(2,0,1)
    car.accelerate(17)
    assert car.get_speed() == 17
