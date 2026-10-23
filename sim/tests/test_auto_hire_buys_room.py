"""auto_hire_buys_room: a staffing closure with no room left reopens once the household can pay for room (Complaint 525).
The room purchase is a rule on built inputs; its callers are in
test_hire_buying_room_wiring."""
QUICK_TOPIC = True

from sim.labour.labour_staff_controls import housing_places_to_buy

from .harness import check

check("room that already holds the new people buys no housing", housing_places_to_buy(3, 5.0, 100.0, 10.0, 1.0e9) == 0)
check("housing is bought for the people the room is short of",
      housing_places_to_buy(3, 1.0, 100.0, 10.0, 1.0e9) == 2)
check("negative room counts as none", housing_places_to_buy(2, -4.0, 100.0, 10.0, 1.0e9) == 2)
check("housing and the hiring outlay together within the budget are bought",
      housing_places_to_buy(1, 0.0, 100.0, 50.0, 150.0) == 1)
check("a purse that cannot pay for housing and the hire together buys no room",
      housing_places_to_buy(1, 0.0, 100.0, 50.0, 149.0) == 0)
