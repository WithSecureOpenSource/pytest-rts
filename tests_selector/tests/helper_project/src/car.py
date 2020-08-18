class Car:

    def __init__(self,seats,speed,passengers):
        self.seats = seats
        self.speed = speed
        self.passengers = passengers

    def get_speed(self):
        return self.speed

    def accelerate(self, amount):
        self.speed = self.speed + amount

    def get_passengers(self):
        return self.passengers

    def add_passenger(self):
        if self.passengers + 1 <= self.seats:
            self.passengers = self.passengers + 1
        
    def remove_passenger(self):
        if self.passengers > 0:
            self.passengers = self.passengers - 1