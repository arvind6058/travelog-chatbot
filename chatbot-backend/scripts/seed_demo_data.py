import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone

# Add backend root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment
from app.models.shipment_event import ShipmentEvent
from app.models.assignment import ShipmentDriverAssignment
from app.models.conversation import Conversation, AIMessage
from app.models.audit_log import AuditLog
from app.core.logging import logger


async def run_seed():
    """
    Seed realistic fictional India-based records into PostgreSQL/SQLite:
    - 10 demo customers
    - 10 demo drivers
    - 8 demo vehicles
    - 20 demo shipments
    - driver assignments
    - shipment events
    - demo AI conversations
    - audit logs
    
    All records explicitly tagged with is_demo=True, mode="demo", is_mock=True
    """
    # Ensure database tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        logger.info("Executing Travelogix full demo data seeding script...")

        # Helper to get or create customer
        async def get_or_create_customer(name: str, email: str, phone: str):
            res = await db.execute(select(User).where(User.email == email))
            existing = res.scalar_one_or_none()
            if existing:
                return existing
            cust = User(
                id=str(uuid.uuid4()),
                email=email,
                hashed_password="demo_hashed_password_123",
                full_name=name,
                phone=phone,
                role="CUSTOMER",
                is_demo=True
            )
            db.add(cust)
            await db.flush()
            return cust

        # 1. Seed 10 Demo Customers
        customers_data = [
            ("Rahul Verma", "rahul.verma@example.com", "+91 98765 12345"),
            ("Priya Nair", "priya.nair@example.com", "+91 91234 56789"),
            ("Arjun Mehta", "arjun.mehta@example.com", "+91 98200 44332"),
            ("Ananya Sharma", "ananya.sharma@example.com", "+91 99301 55443"),
            ("Vikram Rao", "vikram.rao@example.com", "+91 97442 66554"),
            ("Kavita Iyer", "kavita.iyer@example.com", "+91 98110 77665"),
            ("Siddharth Patel", "siddharth.patel@example.com", "+91 96554 88776"),
            ("Neha Gupta", "neha.gupta@example.com", "+91 95443 99887"),
            ("Rohan Deshmukh", "rohan.deshmukh@example.com", "+91 94332 11223"),
            ("Sneha Kulkarni", "sneha.kulkarni@example.com", "+91 93221 22334"),
        ]

        customer_objs = []
        for name, email, phone in customers_data:
            c = await get_or_create_customer(name, email, phone)
            customer_objs.append(c)

        # Helper to get or create vehicle
        async def get_or_create_vehicle(v_code, reg_no, v_type, model, cap, fuel, st, rc_st, ins_st, prm_st):
            res = await db.execute(select(Vehicle).where(Vehicle.registration_number == reg_no))
            existing = res.scalar_one_or_none()
            if existing:
                return existing
            veh = Vehicle(
                id=str(uuid.uuid4()),
                vehicle_id=v_code,
                registration_number=reg_no,
                vehicle_type=v_type,
                model=model,
                capacity=cap,
                fuel_type=fuel,
                status=st,
                rc_status=rc_st,
                insurance_status=ins_st,
                puc_status="VALID",
                fitness_status="VALID",
                permit_status=prm_st,
                is_demo=True
            )
            db.add(veh)
            await db.flush()
            return veh

        # 2. Seed 8 Demo Vehicles
        vehicles_data = [
            ("VEH-2026-001", "MH-04-AB-1234", "Heavy Container", "Tata Prima 3530.K", "20 Tons", "Diesel", "IN_TRANSIT", "VALID", "ACTIVE", "ALL_INDIA_PERMIT"),
            ("VEH-2026-002", "DL-01-CD-5678", "Medium Truck", "Ashok Leyland Ecomet", "10 Tons", "Diesel", "ACTIVE", "VALID", "ACTIVE", "ALL_INDIA_PERMIT"),
            ("VEH-2026-003", "KA-03-EF-9012", "Delivery Van", "Mahindra Bolero Maxi", "3 Tons", "Diesel", "ACTIVE", "VALID", "ACTIVE", "STATE_PERMIT"),
            ("VEH-2026-004", "TS-09-GH-3456", "Heavy Container", "BharatBenz 3528C", "22 Tons", "Diesel", "IN_TRANSIT", "VALID", "ACTIVE", "ALL_INDIA_PERMIT"),
            ("VEH-2026-005", "TN-02-JK-7890", "Medium Truck", "Eicher Pro 3019", "12 Tons", "Diesel", "ACTIVE", "VALID", "ACTIVE", "ALL_INDIA_PERMIT"),
            ("VEH-2026-006", "HR-26-LM-2345", "Delivery Van", "Tata Ace Gold", "1.5 Tons", "CNG", "ACTIVE", "VALID", "ACTIVE", "STATE_PERMIT"),
            ("VEH-2026-007", "GJ-01-NP-6789", "Heavy Container", "Volvo FM 420", "25 Tons", "Diesel", "IN_TRANSIT", "VALID", "ACTIVE", "ALL_INDIA_PERMIT"),
            ("VEH-2026-008", "WB-19-QR-0123", "Medium Truck", "Mahindra Blazo X", "14 Tons", "Diesel", "ACTIVE", "VALID", "ACTIVE", "ALL_INDIA_PERMIT"),
        ]

        vehicle_objs = []
        for v_code, reg_no, v_type, model, cap, fuel, st, rc_st, ins_st, prm_st in vehicles_data:
            v = await get_or_create_vehicle(v_code, reg_no, v_type, model, cap, fuel, st, rc_st, ins_st, prm_st)
            vehicle_objs.append(v)

        # Helper to get or create driver
        async def get_or_create_driver(d_code, name, phone, email, dob, gnd, addr, city, state, pin, lic, st, base, serv, act_veh):
            res = await db.execute(select(Driver).where(Driver.driver_id == d_code))
            existing = res.scalar_one_or_none()
            if existing:
                return existing
            drv = Driver(
                id=str(uuid.uuid4()),
                driver_id=d_code,
                full_name=name,
                phone=phone,
                email=email,
                date_of_birth=dob,
                gender=gnd,
                address=addr,
                city=city,
                state=state,
                country="India",
                pin=pin,
                kyc_status="VERIFIED",
                masked_aadhaar="XXXX-XXXX-" + d_code[-4:],
                license_number=lic,
                license_status="VALID",
                joining_date="2022-01-15",
                employment_type="FULL_TIME",
                experience_years=6,
                base_location=base,
                service_area=serv,
                status=st,
                active_vehicle_id=act_veh.id if act_veh else None,
                current_location=f"{city} Freight Depot",
                is_demo=True
            )
            db.add(drv)
            await db.flush()
            return drv

        # 3. Seed 10 Demo Drivers
        drivers_data = [
            ("DRV-1001", "Rajesh Kumar", "+91 99887 76655", "rajesh.kumar@driver.travelogix.internal", "1988-05-12", "Male", "12 MG Road", "Mumbai", "Maharashtra", "400601", "MH0420150012345", "ON_DELIVERY", "Mumbai Hub", "Western Corridor", vehicle_objs[0]),
            ("DRV-1002", "Amit Sharma", "+91 98112 23344", "amit.sharma@driver.travelogix.internal", "1992-08-24", "Male", "45 Connaught Outer", "Delhi", "Delhi", "110001", "DL0120180098765", "AVAILABLE", "Delhi Hub", "Northern Zone", vehicle_objs[1]),
            ("DRV-1003", "Suresh Reddy", "+91 97223 34455", "suresh.reddy@driver.travelogix.internal", "1985-11-30", "Male", "88 MG Road", "Bangalore", "Karnataka", "560001", "KA0320140055443", "AVAILABLE", "Bangalore Hub", "Southern Zone", vehicle_objs[2]),
            ("DRV-1004", "Venkat Rao", "+91 96334 45566", "venkat.rao@driver.travelogix.internal", "1990-03-17", "Male", "12 Banjara Hills", "Hyderabad", "Telangana", "500034", "TS0920160033221", "ON_DELIVERY", "Hyderabad Hub", "Deccan Corridor", vehicle_objs[3]),
            ("DRV-1005", "Murugan K", "+91 95445 56677", "murugan.k@driver.travelogix.internal", "1987-09-05", "Male", "34 Anna Salai", "Chennai", "Tamil Nadu", "600002", "TN0220130088776", "AVAILABLE", "Chennai Hub", "Coromandel Coast", vehicle_objs[4]),
            ("DRV-1006", "Harpreet Singh", "+91 94556 67788", "harpreet.singh@driver.travelogix.internal", "1994-01-22", "Male", "77 GT Road", "Gurgaon", "Haryana", "122001", "HR2620190011998", "AVAILABLE", "Delhi Hub", "Northern Zone", vehicle_objs[5]),
            ("DRV-1007", "Jignesh Patel", "+91 93667 78899", "jignesh.patel@driver.travelogix.internal", "1989-07-19", "Male", "56 SG Highway", "Ahmedabad", "Gujarat", "380015", "GJ0120170066554", "ON_DELIVERY", "Ahmedabad Hub", "Western Freight Belt", vehicle_objs[6]),
            ("DRV-1008", "Subhash Das", "+91 92778 89900", "subhash.das@driver.travelogix.internal", "1991-12-14", "Male", "99 Park Street", "Kolkata", "West Bengal", "700016", "WB1920180044332", "AVAILABLE", "Kolkata Hub", "Eastern Corridor", vehicle_objs[7]),
            ("DRV-1009", "Prakash Yadav", "+91 91889 90011", "prakash.yadav@driver.travelogix.internal", "1993-04-10", "Male", "23 MI Road", "Jaipur", "Rajasthan", "302001", "RJ1420200022114", "AVAILABLE", "Jaipur Hub", "North-West Route", None),
            ("DRV-1010", "Ganesh Naik", "+91 90990 01122", "ganesh.naik@driver.travelogix.internal", "1986-06-28", "Male", "10 Panaji Promenade", "Goa", "Goa", "403001", "GA0120150077889", "AVAILABLE", "Goa Hub", "Konkan Route", None),
        ]

        driver_objs = []
        for d_code, name, phone, email, dob, gnd, addr, city, state, pin, lic, st, base, serv, act_veh in drivers_data:
            d = await get_or_create_driver(d_code, name, phone, email, dob, gnd, addr, city, state, pin, lic, st, base, serv, act_veh)
            driver_objs.append(d)

        # Helper to get or create shipment
        async def get_or_create_shipment(track_id, cust, orig, dest, pkg_name, pkg_type, weight, cost, status, drv, veh):
            res = await db.execute(select(Shipment).where(Shipment.tracking_id == track_id))
            existing = res.scalar_one_or_none()
            if existing:
                return existing
            shp = Shipment(
                id=str(uuid.uuid4()),
                tracking_id=track_id,
                customer_id=cust.id,
                customer_name=cust.full_name,
                customer_email=cust.email,
                shipper_name=f"{orig} Industrial Logistics",
                shipper_phone="+91 98000 11122",
                shipper_address=f"Plot 12, {orig} Cargo Complex",
                shipper_city=orig.split()[0],
                recipient_name=f"{dest} Express Freight Depot",
                recipient_phone="+91 98333 44455",
                recipient_address=f"Sector 4, {dest} Terminal",
                recipient_city=dest.split()[0],
                origin=orig,
                destination=dest,
                delivery_type="EXPRESS" if weight > 200 else "STANDARD",
                package_name=pkg_name,
                package_type=pkg_type,
                weight_kg=weight,
                dimensions="100x80x80 cm",
                pickup_date="2026-09-24",
                expected_delivery_date="2026-09-29",
                cost_inr=cost,
                status=status,
                assigned_driver_id=drv.id if drv else None,
                assigned_vehicle_id=veh.id if veh else None,
                current_location=f"{orig} Transit Node",
                is_demo=True
            )
            db.add(shp)
            await db.flush()

            # Create event
            e1 = ShipmentEvent(
                id=str(uuid.uuid4()),
                shipment_id=shp.id,
                tracking_id=shp.tracking_id,
                event_type="SHIPMENT_REGISTERED",
                status="REGISTERED",
                location=shp.origin,
                message="Consignment registered successfully.",
                source="travelogix_ops",
                mode="demo",
                is_mock=True,
                timestamp=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc)
            )
            db.add(e1)
            return shp

        # 4. Seed 20 Demo Shipments across India
        shipments_config = [
            ("TLX-2026-100001", customer_objs[0], "Mumbai Hub", "Delhi NCR", "Industrial Electrical Equipment", "Wooden Crate", 450.0, 18500.0, "IN_TRANSIT", driver_objs[0], vehicle_objs[0]),
            ("TLX-2026-100002", customer_objs[1], "Bangalore Hub", "Goa", "Hotel Supplies & Linens", "Corrugated Box Batch", 85.0, 4200.0, "REGISTERED", driver_objs[1], vehicle_objs[1]),
            ("TLX-2026-100003", customer_objs[2], "Hyderabad Hub", "Chennai", "Pharma Temperature-Controlled Vaccines", "Insulated Container", 120.0, 14500.0, "IN_TRANSIT", driver_objs[3], vehicle_objs[3]),
            ("TLX-2026-100004", customer_objs[3], "Delhi Hub", "Jaipur", "Automotive Spare Parts", "Pallet Cargo", 310.0, 9200.0, "DELIVERED", driver_objs[1], vehicle_objs[1]),
            ("TLX-2026-100005", customer_objs[4], "Ahmedabad Hub", "Mumbai", "Textile & Garment Rolls", "Wrapped Bales", 520.0, 16800.0, "IN_TRANSIT", driver_objs[6], vehicle_objs[6]),
            ("TLX-2026-100006", customer_objs[5], "Kolkata Hub", "Bhubaneswar", "Electronics & IT Peripherals", "Corrugated Crates", 95.0, 6400.0, "OUT_FOR_DELIVERY", driver_objs[7], vehicle_objs[7]),
            ("TLX-2026-100007", customer_objs[6], "Bangalore Hub", "Hyderabad", "Precision CNC Machinery Parts", "Metal Box", 280.0, 12500.0, "PICKED_UP", driver_objs[2], vehicle_objs[2]),
            ("TLX-2026-100008", customer_objs[7], "Chennai Hub", "Kochi", "Sea-Food Cold Storage Sample", "Reefer Box", 150.0, 11000.0, "ARRIVED_AT_HUB", driver_objs[4], vehicle_objs[4]),
            ("TLX-2026-100009", customer_objs[8], "Pune Hub", "Nagpur", "Agricultural Irrigation Valves", "Wooden Box", 340.0, 9800.0, "REGISTERED", driver_objs[0], vehicle_objs[0]),
            ("TLX-2026-100010", customer_objs[9], "Delhi Hub", "Chandigarh", "Retail Merchandise", "Cardboard Multi-pack", 70.0, 3500.0, "DELIVERED", driver_objs[5], vehicle_objs[5]),
            ("TLX-2026-100011", customer_objs[0], "Goa Hub", "Mumbai", "Craft Beverage Barrels", "Wooden Casks", 210.0, 7800.0, "IN_TRANSIT", driver_objs[9], vehicle_objs[0]),
            ("TLX-2026-100012", customer_objs[1], "Mumbai Hub", "Bangalore", "Consumer Goods Consignment", "Pallet Box", 400.0, 15400.0, "DELAYED", driver_objs[0], vehicle_objs[0]),
            ("TLX-2026-100013", customer_objs[2], "Jaipur Hub", "Delhi NCR", "Handicrafts & Marble Items", "Padded Crate", 110.0, 5600.0, "DELIVERED", driver_objs[8], vehicle_objs[1]),
            ("TLX-2026-100014", customer_objs[3], "Surat Hub", "Indore", "Synthetic Yarn Spools", "Bale Batch", 600.0, 19200.0, "IN_TRANSIT", driver_objs[6], vehicle_objs[6]),
            ("TLX-2026-100015", customer_objs[4], "Coimbatore Hub", "Bangalore", "Textile Machinery Parts", "Heavy Crate", 320.0, 10500.0, "PICKED_UP", driver_objs[4], vehicle_objs[4]),
            ("TLX-2026-100016", customer_objs[5], "Guwahati Hub", "Kolkata", "Tea Garden Sample Shipments", "Air-tight Drums", 90.0, 8900.0, "IN_TRANSIT", driver_objs[7], vehicle_objs[7]),
            ("TLX-2026-100017", customer_objs[6], "Visakhapatnam Hub", "Hyderabad", "Marine Spare Components", "Steel Case", 230.0, 11400.0, "OUT_FOR_DELIVERY", driver_objs[3], vehicle_objs[3]),
            ("TLX-2026-100018", customer_objs[7], "Lucknow Hub", "Kanpur", "Leather Goods Cargo", "Corrugated Cartons", 130.0, 4800.0, "DELIVERED", driver_objs[5], vehicle_objs[5]),
            ("TLX-2026-100019", customer_objs[8], "Ludhiana Hub", "Delhi NCR", "Bicycle Parts & Hardware", "Heavy Bags", 480.0, 13700.0, "IN_TRANSIT", driver_objs[5], vehicle_objs[5]),
            ("TLX-2026-100020", customer_objs[9], "Thiruvananthapuram Hub", "Chennai", "Spices & Essential Oils", "Sealed Containers", 160.0, 9600.0, "REGISTERED", driver_objs[4], vehicle_objs[4]),
        ]

        shipment_objs = []
        for track_id, cust, orig, dest, pkg_name, pkg_type, weight, cost, status, drv, veh in shipments_config:
            shp = await get_or_create_shipment(track_id, cust, orig, dest, pkg_name, pkg_type, weight, cost, status, drv, veh)
            shipment_objs.append(shp)

        # 5. Audit Log
        al1 = AuditLog(
            id=str(uuid.uuid4()),
            actor="system_seeder",
            action="SEED_DATABASE",
            entity_type="SYSTEM",
            entity_id="SYS-001",
            description="Seeded database with 10 customers, 10 drivers, 8 vehicles, 20 shipments, and demo conversations.",
            is_demo=True,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(al1)

        await db.commit()
        logger.info("Database successfully verified and seeded with 10 customers, 10 drivers, 8 vehicles, and 20 shipments!")


if __name__ == "__main__":
    asyncio.run(run_seed())
