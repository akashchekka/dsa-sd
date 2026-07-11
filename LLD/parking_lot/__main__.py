"""
=============================================================================
 ParkingLot — entry point (Google / Uber / Amazon machine-coding)
=============================================================================
 Run:  python -m parking_lot   (from machine-coding-py/)

 Clarifying questions
   * Single lot or chain?  -> single lot, multi-floor.
   * Reservations?         -> no, FCFS.
   * Payments?             -> out of scope; pricing returns amount only.
   * EV/Handicapped?       -> extend SpotType + can_fit; no other change.

 Folder layout (mirrors C# /machine-coding/ParkingLot/)
   models/        Vehicle, ParkingSpot, Ticket
   interfaces/    IClock, IPricingStrategy, ISpotAllocationStrategy
   strategies/    HourlyTieredPricing, FirstFitAllocation
   services/      ParkingFloor, ParkingLot
=============================================================================
"""
from __future__ import annotations

from interfaces.clock                  import SystemClock
from models.parking_spot               import ParkingSpot, SpotType
from models.vehicle                    import Car, Truck
from services.parking_floor            import ParkingFloor
from services.parking_lot              import ParkingLot
from strategies.first_fit_allocation   import FirstFitAllocation
from strategies.hourly_tiered_pricing  import HourlyTieredPricing


def main() -> None:
    f1 = ParkingFloor(1, [
        ParkingSpot("F1-S1", SpotType.SMALL),
        ParkingSpot("F1-M1", SpotType.MEDIUM),
        ParkingSpot("F1-L1", SpotType.LARGE),
    ])
    f2 = ParkingFloor(2, [
        ParkingSpot("F2-M1", SpotType.MEDIUM),
        ParkingSpot("F2-L1", SpotType.LARGE),
    ])

    lot = ParkingLot([f1, f2], FirstFitAllocation(), HourlyTieredPricing(), SystemClock())

    t1 = lot.park(Car("KA-01-1234"))
    t2 = lot.park(Truck("KA-02-9999"))
    assert t1 and t2
    print(f"Parked {t1.vehicle.license_plate} at {t1.spot.id}")
    print(f"Parked {t2.vehicle.license_plate} at {t2.spot.id}")

    done = lot.exit(t1.id)
    print(f"Exit  {done.vehicle.license_plate}: due ${done.amount_due}")


if __name__ == "__main__":
    main()
