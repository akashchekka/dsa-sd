"""
=============================================================================
 RideSharing — entry point
=============================================================================
 Run:  python -m ride_sharing   (from machine-coding-py/)
=============================================================================
"""
from __future__ import annotations

from models.actors                    import CabType, Driver, Rider
from models.location                  import Location
from services.ride_service            import RideService
from strategies.distance_based_pricing import DistanceBasedPricing
from strategies.nearest_driver_matching import NearestDriverMatching


def main() -> None:
    svc = RideService(
        matcher=NearestDriverMatching(),
        pricing=DistanceBasedPricing(),
        surge_provider=lambda: 1.5,                            # surge x1.5
    )

    svc.register_driver(Driver("d1", "Aisha", CabType.SEDAN, Location(12.97, 77.59)))
    svc.register_driver(Driver("d2", "Bilal", CabType.SEDAN, Location(12.95, 77.62)))
    svc.register_driver(Driver("d3", "Chen",  CabType.SUV,   Location(12.98, 77.60)))

    rider = Rider("r1", "Diya")
    trip  = svc.request(rider, Location(12.96, 77.60), Location(12.93, 77.65), CabType.SEDAN)
    print(f"Trip {trip.id} status={trip.status.value} "
          f"driver={trip.driver.name if trip.driver else None}")

    svc.start_trip(trip.id)
    done = svc.complete_trip(trip.id)
    print(f"Trip {done.id} fare=Rs.{done.fare} status={done.status.value}")


if __name__ == "__main__":
    main()
