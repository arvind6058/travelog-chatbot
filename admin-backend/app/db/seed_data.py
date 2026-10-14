import secrets
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.security import hash_password
from app.models.user import User
from app.models.driver import Driver
from app.models.driver_location import DriverLocation
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.conversation import Conversation, AIMessage
from app.models.audit_log import AuditLog
from app.core.logging import logger



async def seed_initial_data(db: AsyncSession):
    # Check if shipments exist
    stmt = select(func.count(Shipment.id))
    result = await db.execute(stmt)
    count = result.scalar_one()

    if count > 0:
        logger.info("Database already contains data. Skipping initial seeding.")
        return

    logger.info("Seeding initial database records for Travelogix...")

    # 1. Seed Customer Users
    # Demo rows carry a real bcrypt hash of an unguessable random secret: the
    # previous placeholder string ("demo_hashed_password_123") looked like a
    # stored credential but could never validate, and masked genuine errors.
    _demo_secret_hash = hash_password(secrets.token_urlsafe(32))
    cust1 = User(
        id=str(uuid.uuid4()),
        email="rahul.verma@example.com",
        hashed_password=_demo_secret_hash,
        full_name="Rahul Verma",
        phone="+91 98765 12345",
        role="CUSTOMER",
        is_demo=True
    )
    cust2 = User(
        id=str(uuid.uuid4()),
        email="priya.nair@example.com",
        hashed_password=_demo_secret_hash,
        full_name="Priya Nair",
        phone="+91 91234 56789",
        role="CUSTOMER",
        is_demo=True
    )
    db.add_all([cust1, cust2])
    await db.flush()

    # 2. Seed Vehicles
    v1 = Vehicle(
        id=str(uuid.uuid4()),
        vehicle_id="VEH-2026-001",
        registration_number="MH-04-AB-1234",
        vehicle_type="Heavy Container",
        model="Tata Prima 3530.K",
        capacity="20 Tons",
        fuel_type="Diesel",
        status="IN_TRANSIT",
        rc_status="VALID",
        insurance_status="ACTIVE",
        puc_status="VALID",
        fitness_status="VALID",
        permit_status="ALL_INDIA_PERMIT",
        is_demo=True
    )
    v2 = Vehicle(
        id=str(uuid.uuid4()),
        vehicle_id="VEH-2026-002",
        registration_number="DL-01-CD-5678",
        vehicle_type="Medium Truck",
        model="Ashok Leyland Ecomet",
        capacity="10 Tons",
        fuel_type="Diesel",
        status="ACTIVE",
        rc_status="VALID",
        insurance_status="ACTIVE",
        puc_status="VALID",
        fitness_status="VALID",
        permit_status="ALL_INDIA_PERMIT",
        is_demo=True
    )
    v3 = Vehicle(
        id=str(uuid.uuid4()),
        vehicle_id="VEH-2026-003",
        registration_number="KA-03-EF-9012",
        vehicle_type="Delivery Van",
        model="Mahindra Bolero Maxi",
        capacity="3 Tons",
        fuel_type="Diesel",
        status="ACTIVE",
        rc_status="VALID",
        insurance_status="ACTIVE",
        puc_status="VALID",
        fitness_status="VALID",
        permit_status="STATE_PERMIT",
        is_demo=True
    )
    db.add_all([v1, v2, v3])
    await db.flush()

    # 3. Seed Drivers
    d1 = Driver(
        id=str(uuid.uuid4()),
        driver_id="DRV-1001",
        full_name="Rajesh Kumar",
        phone="+91 99887 76655",
        email="rajesh.kumar@driver.travelogix.internal",
        date_of_birth="1988-05-12",
        gender="Male",
        address="12 MG Road, Thane",
        city="Mumbai",
        state="Maharashtra",
        country="India",
        pin="400601",
        kyc_status="VERIFIED",
        masked_aadhaar="XXXX-XXXX-4321",
        license_number="MH0420150012345",
        license_status="VALID",
        joining_date="2022-03-15",
        employment_type="FULL_TIME",
        experience_years=8,
        base_location="Mumbai Hub",
        service_area="Western Freight Corridor",
        status="ON_DELIVERY",
        active_vehicle_id=v1.id,
        current_location="Pune Highway Express Control",
        is_demo=True
    )
    d2 = Driver(
        id=str(uuid.uuid4()),
        driver_id="DRV-1002",
        full_name="Amit Sharma",
        phone="+91 98112 23344",
        email="amit.sharma@driver.travelogix.internal",
        date_of_birth="1992-08-24",
        gender="Male",
        address="45 Connaught Outer",
        city="Delhi",
        state="Delhi",
        country="India",
        pin="110001",
        kyc_status="VERIFIED",
        masked_aadhaar="XXXX-XXXX-8765",
        license_number="DL0120180098765",
        license_status="VALID",
        joining_date="2023-01-10",
        employment_type="FULL_TIME",
        experience_years=5,
        base_location="Delhi Hub",
        service_area="Northern Zone",
        status="AVAILABLE",
        active_vehicle_id=v2.id,
        current_location="Delhi Central Freight Yard",
        is_demo=True
    )
    db.add_all([d1, d2])
    await db.flush()

    # Link current driver to vehicle
    v1.current_driver_id = d1.driver_id
    v2.current_driver_id = d2.driver_id
    await db.flush()

    # 4. Seed Shipments
    s1 = Shipment(
        id=str(uuid.uuid4()),
        tracking_id="TLX-DEMO-100001",
        customer_id=cust1.id,
        customer_name=cust1.full_name,
        customer_email=cust1.email,
        shipper_name="Tata Steel Logistics Hub",
        shipper_phone="+91 98220 11223",
        shipper_address="Plot 45, MIDC Industrial Area",
        shipper_city="Mumbai",
        recipient_name="Delhi Infrastructure Corp",
        recipient_phone="+91 91100 33445",
        recipient_address="Sector 62, Noida Freight Terminal",
        recipient_city="Delhi NCR",
        origin="Mumbai Hub",
        destination="Delhi NCR",
        delivery_type="EXPRESS",
        package_name="Industrial Electrical Equipment",
        package_type="Wooden Crate",
        weight_kg=450.0,
        dimensions="120x100x80 cm",
        pickup_date="2026-09-24",
        expected_delivery_date="2026-09-28",
        cost_inr=18500.0,
        status="IN_TRANSIT",
        assigned_driver_id=d1.id,
        assigned_vehicle_id=v1.id,
        current_location="Mysore Road Highway Transit Hub",
        is_demo=True
    )
    s2 = Shipment(
        id=str(uuid.uuid4()),
        tracking_id="TLX-DEMO-100002",
        customer_id=cust2.id,
        customer_name=cust2.full_name,
        customer_email=cust2.email,
        shipper_name="Reliance Retail Warehousing",
        shipper_phone="+91 97330 44556",
        shipper_address="Logistics Park 12",
        shipper_city="Bangalore",
        recipient_name="Goa Hospitality Distributors",
        recipient_phone="+91 94880 77889",
        recipient_address="Panaji Commercial Complex",
        recipient_city="Goa",
        origin="Bangalore Hub",
        destination="Goa",
        delivery_type="STANDARD",
        package_name="Hotel Supplies & Linens",
        package_type="Corrugated Box Batch",
        weight_kg=85.0,
        dimensions="60x40x40 cm",
        pickup_date="2026-09-25",
        expected_delivery_date="2026-09-27",
        cost_inr=4200.0,
        status="REGISTERED",
        # Left unassigned on purpose: a REGISTERED shipment must not already
        # have a driver, and this keeps one driver available for the
        # admin assignment flow. The previous seed violated both invariants.
        assigned_driver_id=None,
        assigned_vehicle_id=None,
        current_location="Bangalore Hub Depot",
        is_demo=True
    )
    db.add_all([s1, s2])
    await db.flush()

    # 5. Seed Shipment Events
    se1 = ShipmentEvent(
        id=str(uuid.uuid4()),
        shipment_id=s1.id,
        tracking_id=s1.tracking_id,
        event_type="SHIPMENT_REGISTERED",
        status="REGISTERED",
        location="Mumbai Hub",
        message="Consignment registered and ready for dispatch.",
        source="travelogix_ops",
        mode="demo",
        is_mock=True,
        timestamp=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    se2 = ShipmentEvent(
        id=str(uuid.uuid4()),
        shipment_id=s1.id,
        tracking_id=s1.tracking_id,
        event_type="STATUS_IN_TRANSIT",
        status="IN_TRANSIT",
        location="Mysore Road Highway Transit Hub",
        message="Vehicle departed Mumbai Hub. En route to Delhi NCR via NH48.",
        source="travelogix_ops",
        mode="demo",
        is_mock=True,
        timestamp=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    db.add_all([se1, se2])
    await db.flush()

    # 6. Seed AI Conversation
    conv = Conversation(
        id=str(uuid.uuid4()),
        customer_id=cust1.id,
        customer_email=cust1.email,
        title="Plan 5 days trip to Goa",
        status="ACTIVE",
        is_demo=True
    )
    db.add(conv)
    await db.flush()

    msg1 = AIMessage(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        sequence=1,
        role="user",
        content="Plan 5 days trip to Goa",
        intent="TRAVEL_ITINERARY",
        mode="demo",
        source="travelogix_assistant",
        created_at=datetime.now(timezone.utc)
    )
    msg2 = AIMessage(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        sequence=2,
        role="assistant",
        content="### 🌴 5-Day Goa Itinerary\n\n**Day 1:** Arrival in North Goa, Calangute Beach Sunset.\n**Day 2:** Fort Aguada, Candolim & Baga Nightlife.\n**Day 3:** Old Goa Churches & Spice Plantation Tour.\n**Day 4:** South Goa Beach Hopping (Palolem & Agonda).\n**Day 5:** Panaji Heritage Walk & Departure.",
        intent="TRAVEL_ITINERARY",
        mode="demo",
        source="travelogix_assistant",
        created_at=datetime.now(timezone.utc)
    )
    db.add_all([msg1, msg2])
    await db.flush()

    # 7. Seed Audit Log
    al1 = AuditLog(
        id=str(uuid.uuid4()),
        actor="system_seeder",
        action="SYSTEM_INITIALIZED",
        entity_type="SYSTEM",
        entity_id="SYS-001",
        description="Initialized Travelogix seed database with demo freight, drivers, and AI conversations.",
        is_demo=True,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(al1)
    # Seed Driver Locations
    dl1 = DriverLocation(
        id=str(uuid.uuid4()),
        driver_id=d1.id,
        vehicle_id=v1.id,
        shipment_id=s1.id,
        latitude=19.0760,
        longitude=72.8777,
        accuracy=5.0,
        location_name="Mumbai Hub Terminal",
        source="gps",
        mode="demo",
        is_mock=True,
        recorded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    dl2 = DriverLocation(
        id=str(uuid.uuid4()),
        driver_id=d1.id,
        vehicle_id=v1.id,
        shipment_id=s1.id,
        latitude=18.5204,
        longitude=73.8567,
        accuracy=8.5,
        location_name="Pune Highway Express Control",
        source="gps",
        mode="demo",
        is_mock=True,
        recorded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    dl3 = DriverLocation(
        id=str(uuid.uuid4()),
        driver_id=d2.id,
        vehicle_id=v2.id,
        shipment_id=s2.id,
        latitude=28.6139,
        longitude=77.2090,
        accuracy=10.0,
        location_name="Delhi Central Freight Yard",
        source="gps",
        mode="demo",
        is_mock=True,
        recorded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc)
    )
    db.add_all([dl1, dl2, dl3])
    await db.flush()

    logger.info("Database successfully seeded with demo records!")

