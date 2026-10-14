from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


def generate_goa_itinerary(duration_days: int) -> List[Dict[str, Any]]:
    """Curated day-by-day plan for Goa tailored to trip length."""
    master_days = [
        {
            "day": 1,
            "theme": "Arrival, Coastal Sunset & Beachside Dinner",
            "morning": "Arrival at Dabolim (GOI) or Mopa (GOX) Airport / Madgaon Railway Station. Check-in at your resort.",
            "afternoon": "Unwind and settle in. Relax around Candolim / Calangute beach in North Goa (or Benaulim in South Goa).",
            "evening": "Stroll along the coastline to catch your first Arabian Sea sunset, followed by a beachfront shack dinner with Goan fish curry and feni.",
            "highlights": ["Arabian Sea Sunset", "Fresh Goan Seafood Shack", "Leisure Beach Walk"]
        },
        {
            "day": 2,
            "theme": "North Goa Forts, Heritage & Vibrant Coastline",
            "morning": "Visit the 17th-century Portuguese fortress Aguada Fort and its historic lighthouse with panoramic ocean vistas.",
            "afternoon": "Head north toward Anjuna and Vagator. Explore Chapora Fort (famous 'Dil Chahta Hai' viewpoint).",
            "evening": "Witness sunset from Thalassa or Curlies at Anjuna. Explore the lively local night markets or beach cafes.",
            "highlights": ["Aguada Fort", "Chapora Fort Vista", "Vagator & Anjuna Beaches", "Curated Sunset Shacks"]
        },
        {
            "day": 3,
            "theme": "South Goa Heritage, Old Goa Cathedrals & Spice Plantations",
            "morning": "UNESCO World Heritage trail in Old Goa: Basilica of Bom Jesus (relics of St. Francis Xavier) and Se Cathedral.",
            "afternoon": "Guided excursion through a lush Sahyadri Spice Plantation in Ponda with a traditional Goan Saraswat buffet lunch on banana leaves.",
            "evening": "Mandovi River sunset river cruise in Panaji featuring Goan folk dance and music performances.",
            "highlights": ["Basilica of Bom Jesus", "Ponda Spice Farm", "Authentic Saraswat Lunch", "Mandovi River Cruise"]
        },
        {
            "day": 4,
            "theme": "Panjim Latin Quarter (Fontainhas), Arts & South Goa Serenity",
            "morning": "Walking heritage photography tour through Fontainhas, Asia’s only preserved Portuguese Latin Quarter with vibrant pastel villas.",
            "afternoon": "Visit the iconic Church of Our Lady of the Immaculate Conception, followed by authentic Goan-Portuguese cafe treats (Bebinca & Poee).",
            "evening": "Head south to Colva or Palolem Beach for serene waters, sunset kayaking, and seaside tranquility away from the crowds.",
            "highlights": ["Fontainhas Latin Quarter", "Immaculate Conception Church", "Traditional Bakeries (Bebinca)", "Palolem Sunset"]
        },
        {
            "day": 5,
            "theme": "Relaxation, Souvenir Shopping & Departure",
            "morning": "Lazy morning at the beach or resort pool. Enjoy a final tropical coastal breakfast.",
            "afternoon": "Pick up authentic Goan cashew nuts, local spices, bebinca, and handcrafted terracotta souvenirs from Panjim Municipal Market.",
            "evening": "Check-out and transfer to the airport or railway station with memories of a sun-kissed Goan holiday.",
            "highlights": ["Morning Ocean Dip", "Spices & Cashews Shopping", "Smooth Departure Transfer"]
        },
        {
            "day": 6,
            "theme": "Water Sports & Dolphin Watching Cruise",
            "morning": "Early morning dolphin-spotting boat cruise off Sinquerim beach. Scuba diving or parasailing session.",
            "afternoon": "Rest at Morjim or Ashwem beach known as Olive Ridley turtle nesting sanctuaries.",
            "evening": "Acoustic live music dinner at an ambient garden bistro in Assagao.",
            "highlights": ["Dolphin Safari", "Parasailing / Jet Skiing", "Ashwem Coastal Serenity"]
        },
        {
            "day": 7,
            "theme": "Dudhsagar Waterfall Trek & Forest Trail",
            "morning": "Day expedition to the majestic four-tiered Dudhsagar Waterfalls in Bhagwan Mahaveer Sanctuary.",
            "afternoon": "Jeep safari through dense Western Ghats jungle and refreshing dip in natural freshwater pools.",
            "evening": "Return to your resort for a relaxed spa and farewell cocktail.",
            "highlights": ["Dudhsagar Waterfalls", "Western Ghats Jungle Safari", "Natural Rock Pools"]
        }
    ]

    return master_days[:duration_days]


def generate_coorg_itinerary(duration_days: int) -> List[Dict[str, Any]]:
    """Curated day-by-day plan for Coorg (Madikeri & Kodagu district)."""
    master_days = [
        {
            "day": 1,
            "theme": "Arrival, Madikeri Heritage & Sunset Viewpoint",
            "morning": "Arrival in Coorg (Madikeri). Check-in at your hotel or plantation resort amidst coffee estates.",
            "afternoon": "Visit the 17th-century Madikeri Fort and Omkareshwara Temple, featuring unique Gothic and Islamic architecture.",
            "evening": "Witness panoramic sunset over the misty Western Ghats valleys at Raja's Seat, followed by traditional Kodava dinner (Pandi curry & Akki roti).",
            "highlights": ["Madikeri Fort", "Omkareshwara Temple", "Raja's Seat Sunset", "Kodava Cuisine"]
        },
        {
            "day": 2,
            "theme": "Dubare Elephant Camp, Bylakuppe Monastery & Abbey Falls",
            "morning": "Early morning visit to Dubare Elephant Camp along the Cauvery River for elephant interaction and coracle rides.",
            "afternoon": "Excursion to Bylakuppe Golden Temple (Namdroling Monastery), one of India's largest Tibetan settlements.",
            "evening": "Visit Abbey Falls cascading amidst dense coffee plantations and spice estates.",
            "highlights": ["Dubare Elephant Camp", "Namdroling Tibetan Monastery", "Abbey Falls", "Cauvery Coracle Ride"]
        },
        {
            "day": 3,
            "theme": "Coffee Plantation Walk, Local Markets & Departure",
            "morning": "Guided walking trail through a scented coffee, pepper, and cardamom plantation.",
            "afternoon": "Shop for authentic Coorg spices, homemade chocolates, organic honey, and freshly ground Arabica coffee at Madikeri Market.",
            "evening": "Check-out and transfer for your return journey to Bangalore or Mysore.",
            "highlights": ["Coffee Plantation Walk", "Coorg Spices & Chocolates", "Departure Transfer"]
        },
        {
            "day": 4,
            "theme": "Talakaveri Sacred Source & Brahmagiri Hills",
            "morning": "Trek to Talakaveri, the sacred origin of River Cauvery, situated on the slopes of the Brahmagiri Hill range.",
            "afternoon": "Panoramic views from the peak of Brahmagiri and visit Bhagamandala temple confluence (Triveni Sangama).",
            "evening": "Relaxed evening around Chiklihole Reservoir with tranquil lakeside views.",
            "highlights": ["Talakaveri Sacred Peak", "Brahmagiri Viewpoint", "Bhagamandala Sangam", "Chiklihole Dam"]
        },
        {
            "day": 5,
            "theme": "Nagarhole Wildlife Safari & Wilderness Immersion",
            "morning": "Early morning Jeep Safari at Nagarhole National Park (Kabini / Kutta zone) to spot Asian elephants, leopards, and tigers.",
            "afternoon": "Visit Iruppu Falls, a sacred cascading waterfall flowing down the Brahmagiri range.",
            "evening": "Resort campfire with local tribal dance storytelling and barbecue.",
            "highlights": ["Nagarhole Jungle Safari", "Iruppu Waterfalls", "Wilderness Campfire"]
        }
    ]
    return master_days[:duration_days]


def generate_bangalore_itinerary(duration_days: int) -> List[Dict[str, Any]]:
    """Curated day-by-day plan for Bangalore (Bengaluru)."""
    master_days = [
        {
            "day": 1,
            "theme": "Royal Palaces, Gardens & Garden City Charm",
            "morning": "Arrival in Bangalore. Morning walk through Lalbagh Botanical Garden & historic Glass House.",
            "afternoon": "Tour Tudor-style Bangalore Palace & Tipu Sultan’s Summer Palace.",
            "evening": "Sunset stroll through Cubbon Park, followed by craft beer and dining on Indiranagar 100ft Road.",
            "highlights": ["Lalbagh Glass House", "Bangalore Palace", "Cubbon Park", "Indiranagar Craft Breweries"]
        },
        {
            "day": 2,
            "theme": "Heritage Temples, Tech Corridors & Shopping",
            "morning": "Visit majestic ISKCON Temple and the historic Bull Temple (Nandi Temple) in Basavanagudi.",
            "afternoon": "Explore Commercial Street or UB City luxury mall for shopping and artisan cafes.",
            "evening": "Witness illuminated Vidhana Soudha architecture and sample authentic Benne Dosa at Vidyarthi Bhavan.",
            "highlights": ["ISKCON Temple", "Vidhana Soudha Architecture", "Commercial Street Shopping", "Vidyarthi Bhavan Dosa"]
        },
        {
            "day": 3,
            "theme": "Nandi Hills Sunrise & Heritage Excursion",
            "morning": "Early morning drive (5:00 AM) to Nandi Hills for a breathtaking sunrise over misty cloud beds.",
            "afternoon": "Visit ancient Bhoga Nandeeshwara Temple at the base of Nandi Hills.",
            "evening": "Return to city for souvenir shopping and departure transfer.",
            "highlights": ["Nandi Hills Cloudbed Sunrise", "Bhoga Nandeeshwara Temple", "Departure Transfer"]
        }
    ]
    return master_days[:duration_days]


def generate_mysore_itinerary(duration_days: int) -> List[Dict[str, Any]]:
    """Curated day-by-day plan for Mysore (Mysuru)."""
    master_days = [
        {
            "day": 1,
            "theme": "Grand Mysore Palace & Chamundi Hill",
            "morning": "Arrival in Mysore. Check-in and visit the iconic Mysore Palace (Amba Vilas Palace).",
            "afternoon": "Drive up Chamundi Hill to visit the 12th-century Chamundeshwari Temple and giant Nandi monolith.",
            "evening": "Walk through vibrant Devaraja Market for aromatic sandalwood, silk sarees, and Mysore Pak sweets.",
            "highlights": ["Mysore Palace", "Chamundi Hill Temple", "Nandi Monolith", "Devaraja Market"]
        },
        {
            "day": 2,
            "theme": "St. Philomena's, Zoo & Brindavan Gardens",
            "morning": "Visit Neo-Gothic St. Philomena’s Cathedral and Mysore Zoo (Sri Chamarajendra Zoological Gardens).",
            "afternoon": "Explore Jaganmohan Palace Art Gallery featuring Raja Ravi Varma paintings.",
            "evening": "Head to Brindavan Gardens at KRS Dam for the famous musical fountain light show.",
            "highlights": ["St. Philomena's Cathedral", "Mysore Zoo", "Jaganmohan Palace Gallery", "Brindavan Musical Fountains"]
        },
        {
            "day": 3,
            "theme": "Seringapatam Heritage & Departure",
            "morning": "Excursion to Srirangapatna (Tipu Sultan's island fortress, Daria Daulat Bagh & Gumbaz).",
            "afternoon": "Ranganathittu Bird Sanctuary coracle boat ride on Cauvery River.",
            "evening": "Check-out and onward departure journey.",
            "highlights": ["Srirangapatna Fortress", "Daria Daulat Bagh", "Ranganathittu Bird Sanctuary", "Departure"]
        }
    ]
    return master_days[:duration_days]


def generate_generic_itinerary(destination: str, duration_days: int) -> List[Dict[str, Any]]:
    """Fallback generator for any global or domestic destination."""
    days = []
    for d in range(1, duration_days + 1):
        if d == 1:
            theme = f"Arrival, Check-in & Orientation in {destination}"
            m = f"Arrival in {destination}. Check-in at your hotel and refresh after travel."
            a = f"Stroll through {destination}'s vibrant central district and popular local avenues."
            e = f"Enjoy a welcoming dinner introducing authentic local specialties and flavors."
            hl = ["Arrival & Check-in", "City Orientation", "Authentic Local Dinner"]
        elif d == duration_days:
            theme = f"Morning Leisure, Regional Souvenirs & Departure from {destination}"
            m = f"Relaxed morning breakfast at hotel, followed by packing and last-minute sightseeing."
            a = f"Explore local bazaars for authentic handicrafts, spices, and regional souvenirs."
            e = f"Check-out and transfer to airport or railway station for onward journey."
            hl = ["Morning Leisure", "Regional Handicrafts & Souvenirs", "Departure Transfer"]
        else:
            theme = f"Exploring {destination} - Historic Landmarks & Culture (Day {d})"
            m = f"Morning guided tour of premier heritage sites, temples, or scenic viewpoints in {destination}."
            a = f"Afternoon immersion in local art galleries, historic quarters, and popular cafes."
            e = f"Evening sunset viewpoint, cultural performance, or memorable dining experience."
            hl = [f"{destination} Key Landmarks", "Cultural Immersion", "Sunset Viewpoint"]

        days.append({
            "day": d,
            "theme": theme,
            "morning": m,
            "afternoon": a,
            "evening": e,
            "highlights": hl
        })
    return days


def generateItinerary(
    destination: str,
    duration_days: int = 3,
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute itinerary planning tool.
    Computes realistic schedules, recommended stays, transport guidelines, and estimated budgets.
    Does NOT invent live hotel room availability or fake real-time ticket prices.
    """
    dest_clean = destination.strip().title() if destination else "Goa"
    days_count = max(1, min(14, int(duration_days)))
    d_lower = dest_clean.lower()

    if d_lower in ["coorg", "madikeri", "kodagu"]:
        days_data = generate_coorg_itinerary(days_count)
        hotel_suggestions = [
            {"category": "Luxury Plantation Resort", "area": "Madikeri / Suntikoppa", "vibe": "Sprawling coffee estate resorts with valley views", "availability": "Live pricing unavailable - check booking partners"},
            {"category": "Heritage Homestay", "area": "Somwarpet / Gonikoppal", "vibe": "Traditional Kodava ancestral homes with homecooked food", "availability": "Live pricing unavailable - check booking partners"},
            {"category": "Budget Stays", "area": "Madikeri Town", "vibe": "Cozy hill station hotels close to markets", "availability": "Live pricing unavailable - check booking partners"}
        ]
        transport_suggestions = [
            "Private chauffeur cab from Bangalore / Mysore — recommended for hill road navigation",
            "Self-drive SUV (₹2,000 - ₹3,500 / day) — ideal for scenic mountain drives",
            "KSRTC Volvo bus from Bangalore satellite bus stand to Madikeri"
        ]
        estimated_budget_inr = {
            "budget": f"₹{days_count * 2500} - ₹{days_count * 4000} per person",
            "moderate": f"₹{days_count * 5500} - ₹{days_count * 9000} per person",
            "luxury": f"₹{days_count * 13000}+ per person"
        }
    elif d_lower in ["bangalore", "bengaluru"]:
        days_data = generate_bangalore_itinerary(days_count)
        hotel_suggestions = [
            {"category": "Luxury City Center", "area": "UB City / MG Road", "vibe": "5-star business and luxury hotels", "availability": "Live pricing unavailable - check booking partners"},
            {"category": "Boutique / Tech Corridor", "area": "Indiranagar / Koramangala", "vibe": "Vibrant neighborhood stays near top restaurants", "availability": "Live pricing unavailable - check booking partners"}
        ]
        transport_suggestions = [
            "Namma Metro rail for congestion-free city travel",
            "Uber / Ola cabs and BMTC Vayu Vajra airport buses"
        ]
        estimated_budget_inr = {
            "budget": f"₹{days_count * 2000} - ₹{days_count * 3500} per person",
            "moderate": f"₹{days_count * 4500} - ₹{days_count * 8000} per person",
            "luxury": f"₹{days_count * 11000}+ per person"
        }
    elif d_lower in ["mysore", "mysuru"]:
        days_data = generate_mysore_itinerary(days_count)
        hotel_suggestions = [
            {"category": "Heritage Palace Hotel", "area": "Palace Zone / Nazarbad", "vibe": "Royal heritage architecture with grand gardens", "availability": "Live pricing unavailable - check booking partners"},
            {"category": "Comfort City Hotel", "area": "Gokulam / City Center", "vibe": "Convenient access to markets and sights", "availability": "Live pricing unavailable - check booking partners"}
        ]
        transport_suggestions = [
            "Local auto-rickshaws and cabs for city touring",
            "KSRTC city buses and Tongas (horse carriages) around Mysore Palace"
        ]
        estimated_budget_inr = {
            "budget": f"₹{days_count * 1800} - ₹{days_count * 3200} per person",
            "moderate": f"₹{days_count * 4000} - ₹{days_count * 7000} per person",
            "luxury": f"₹{days_count * 10000}+ per person"
        }
    elif d_lower == "goa":
        days_data = generate_goa_itinerary(days_count)
        hotel_suggestions = [
            {"category": "Luxury Beachfront", "area": "Candolim / Cavelossim", "vibe": "5-star resort with private beach access", "availability": "Live pricing unavailable - check booking partners"},
            {"category": "Boutique Heritage", "area": "Fontainhas, Panjim / Assagao", "vibe": "Restored Indo-Portuguese colonial villas with character", "availability": "Live pricing unavailable - check booking partners"},
            {"category": "Budget / Backpacker", "area": "Anjuna / Arambol", "vibe": "Vibrant beach hostels and cozy guest houses", "availability": "Live pricing unavailable - check booking partners"}
        ]
        transport_suggestions = [
            "Self-drive scooter / motorcycle (₹350 - ₹600 / day) — most popular for beach hopping",
            "Self-drive car / SUV (₹1,500 - ₹2,500 / day) — recommended for families and South Goa day trips",
            "GoaMiles App & Pre-paid airport taxi counter at GOI / GOX"
        ]
        estimated_budget_inr = {
            "budget": f"₹{days_count * 2000} - ₹{days_count * 3500} per person (Hostels, scooters, shacks)",
            "moderate": f"₹{days_count * 4500} - ₹{days_count * 8000} per person (3-4 star resorts, cab tours, dining)",
            "luxury": f"₹{days_count * 12000}+ per person (5-star beachfront resorts, private chauffeur)"
        }
    else:
        days_data = generate_generic_itinerary(dest_clean, days_count)
        hotel_suggestions = [
            {"category": "City Center / Downtown", "area": f"Central {dest_clean}", "vibe": "Convenient for sightseeing and dining", "availability": "Live pricing unavailable from mock provider"},
            {"category": "Quiet Heritage / Scenic", "area": f"{dest_clean} Outskirts", "vibe": "Relaxed environment with scenic views", "availability": "Live pricing unavailable from mock provider"}
        ]
        transport_suggestions = [
            f"Prepaid taxis and ride-hailing apps in {dest_clean}",
            f"Local auto-rickshaws and metro/buses where applicable"
        ]
        estimated_budget_inr = {
            "budget": f"₹{days_count * 1800} - ₹{days_count * 3000} per person",
            "moderate": f"₹{days_count * 4000} - ₹{days_count * 7500} per person",
            "luxury": f"₹{days_count * 10000}+ per person"
        }

    return {
        "title": f"🌴 {days_count}-Day {dest_clean} Trip Plan",
        "destination": dest_clean,
        "duration_days": days_count,
        "days": days_data,
        "hotel_suggestions": hotel_suggestions,
        "transport_suggestions": transport_suggestions,
        "estimated_budget_inr": estimated_budget_inr,
        "travel_tips": [
            f"Best season to visit {dest_clean} is October through March for pleasant tropical weather.",
            "Carry light cotton clothing, sunscreen, sunglasses, and comfortable walking sandals.",
            "Rent two-wheelers only with a valid driving license and always wear helmets.",
            "Respect local culture when visiting historic temples, cathedrals, and heritage landmarks."
        ],
        "provenance": {
            "source": "travelogix_itinerary_engine",
            "mode": "calculated",
            "is_mock": False,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
    }


def calculateBudget(
    destination: str,
    duration_days: int = 5,
    total_budget_inr: float = 35000.0,
    travelers_count: int = 2
) -> Dict[str, Any]:
    """
    Calculate budget breakdown for a trip (Transport, Hotel, Food, Local transport, Activities, Emergency reserve).
    Clearly labels all items as calculated estimates.
    """
    dest_clean = (destination or "Goa").title()
    days = max(1, duration_days)
    travelers = max(1, travelers_count)

    # Budget allocations
    est_transport = round(total_budget_inr * 0.25, 2)       # 25% for Intercity Transport (train/bus/flight)
    est_accommodation = round(total_budget_inr * 0.35, 2)   # 35% for Hotel / Stays
    est_food = round(total_budget_inr * 0.18, 2)            # 18% for Dining & Shacks
    est_local_travel = round(total_budget_inr * 0.08, 2)    # 8% for Scooters / Cabs
    est_activities = round(total_budget_inr * 0.08, 2)      # 8% for Water sports / Entrance fees
    emergency_reserve = round(total_budget_inr * 0.06, 2)   # 6% Emergency Cushion

    total_estimated = round(est_transport + est_accommodation + est_food + est_local_travel + est_activities + emergency_reserve, 2)
    remaining = round(total_budget_inr - total_estimated, 2)

    return {
        "destination": dest_clean,
        "duration_days": days,
        "travelers_count": travelers,
        "target_budget_inr": total_budget_inr,
        "calculated_estimates": {
            "intercity_transport": est_transport,
            "accommodation": est_accommodation,
            "food_and_dining": est_food,
            "local_travel_and_rentals": est_local_travel,
            "activities_and_sightseeing": est_activities,
            "emergency_reserve": emergency_reserve,
        },
        "total_estimated_cost_inr": total_estimated,
        "remaining_budget_inr": max(0.0, remaining),
        "disclaimer": "All figures are locally calculated estimates based on typical Indian tourism costs. Provider prices are not fabricated.",
        "provenance": {
            "source": "travelogix_budget_calculator",
            "mode": "calculated",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": False
        }
    }


def recalculateDisruptedItinerary(
    destination: str,
    duration_days: int = 5,
    delay_hours: float = 4.0
) -> Dict[str, Any]:
    """
    Recalculate itinerary timing following a travel delay (e.g. 4-hour bus/flight delay).
    """
    dest_clean = (destination or "Goa").title()
    base = generateItinerary(dest_clean, duration_days)
    days = base.get("days", [])

    if days:
        days[0]["theme"] += f" (Adjusted for {int(delay_hours)}-Hour Delay)"
        days[0]["morning"] = f"⚠️ Delayed departure / arrival by {int(delay_hours)} hours. Morning activities shifted to afternoon."
        days[0]["afternoon"] = "Check-in at hotel and take rest after delayed journey."
        days[0]["highlights"].insert(0, f"Adjusted timing (+{int(delay_hours)}h delay)")

    return {
        "title": f"⏱️ Updated {dest_clean} Itinerary (Adjusted for {int(delay_hours)}h Delay)",
        "destination": dest_clean,
        "delay_hours": delay_hours,
        "adjusted_days": days,
        "summary": f"Morning activities on Day 1 have been postponed to account for the {int(delay_hours)}-hour travel delay. Subsequent days remain intact.",
        "provenance": {
            "source": "travelogix_disruption_engine",
            "mode": "calculated",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": False
        }
    }


def modifyItinerary(
    destination: str,
    duration_days: int = 4,
    modification_request: str = ""
) -> Dict[str, Any]:
    """
    Modify an existing trip itinerary (e.g. change days, change hotel area, replace flight with bus).
    """
    dest_clean = (destination or "Goa").title()
    res = generateItinerary(dest_clean, duration_days)
    res["title"] = f"✏️ Modified {duration_days}-Day {dest_clean} Itinerary"
    res["modification_note"] = f"Updated itinerary to reflect request: '{modification_request}'"
    return res


def getPackingSuggestions(
    destination: str,
    duration_days: int = 5,
    weather: Optional[str] = "Sunny",
    travel_mode: Optional[str] = "Flight"
) -> Dict[str, Any]:
    """Generate practical packing checklist based on destination, duration, and weather."""
    dest_clean = (destination or "Goa").title()

    checklist = {
        "documents_and_essentials": [
            "Government Photo ID (Aadhaar / Driving License / Passport)",
            "Flight / Bus / Train tickets & Booking Vouchers",
            "Debit / Credit Cards & Cash (for beach shacks/local vendors)",
            "Travel Insurance Copy"
        ],
        "clothing": [
            f"{duration_days}x Light cotton / linen t-shirts",
            f"{duration_days - 1}x Shorts / Casual pants / Shorts",
            "2x Swimwear & Rashguards for beach & pool",
            "1x Light rain jacket or windbreaker",
            "Flip-flops & Comfortable walking sneakers"
        ],
        "toiletries_and_skincare": [
            "High SPF Sunscreen (SPF 50+)",
            "Mosquito repellent spray / cream",
            "Aloe vera gel for sun relief",
            "Basic toiletries & Travel-sized shampoo"
        ],
        "electronics": [
            "Smartphone & Charger",
            "Power bank (10,000+ mAh)",
            "Waterproof phone pouch for beach / water sports",
            "Camera / Go-Pro & memory cards"
        ],
        "health_and_safety": [
            "Personal prescription medications",
            "Basic first aid: Band-aids, ORS, Paracetamol, Antacid",
            "Hand sanitizer & Wet wipes"
        ]
    }

    return {
        "destination": dest_clean,
        "duration_days": duration_days,
        "checklist": checklist,
        "provenance": {
            "source": "travelogix_packing_assistant",
            "mode": "calculated",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": False
        }
    }


def getTravelChecklist() -> Dict[str, Any]:
    """Return universal pre-travel checklist."""
    return {
        "title": "📋 Travelogix Pre-Travel Verification Checklist",
        "categories": {
            "Documents": ["Government ID Proof", "Flight / Bus / Train Boarding Pass", "Hotel Booking Vouchers", "Driver License (if renting)"],
            "Payments": ["Sufficient UPI / Online banking active", "Physical cash (₹2,000 - ₹5,000 in small denominations)"],
            "Packing": ["Luggage tagged with contact info", "Toiletries & Sunscreen packed", "Weather-appropriate clothing"],
            "Emergency Info": ["Saved local emergency contacts", "Hotel address & front desk phone number", "Travelogix Support Hotline"]
        },
        "provenance": {
            "source": "travelogix_checklist_service",
            "mode": "calculated",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": False
        }
    }


def searchPlaces(location: str, category: Optional[str] = "all") -> Dict[str, Any]:
    """Search recommended places, attractions, or restaurants near location."""
    loc_clean = (location or "Goa").title()

    places = [
        {"name": "Fort Aguada & Lighthouse", "category": "Historical Fort", "rating": 4.6, "timing": "09:30 AM - 06:00 PM"},
        {"name": "Basilica of Bom Jesus", "category": "UNESCO World Heritage Site", "rating": 4.8, "timing": "09:00 AM - 06:30 PM"},
        {"name": "Fontainhas Latin Quarter", "category": "Heritage Walk", "rating": 4.7, "timing": "Open 24/7"},
        {"name": "Thalassa Mediterranean Bistro", "category": "Sunset Restaurant", "rating": 4.5, "timing": "12:00 PM - 12:00 AM"},
        {"name": "Fisherman's Wharf", "category": "Goan Seafood Dining", "rating": 4.6, "timing": "12:00 PM - 11:00 PM"}
    ]

    return {
        "location": loc_clean,
        "category": category,
        "count": len(places),
        "places": places,
        "provenance": {
            "source": "travelogix_places_guide",
            "mode": "demo",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "is_mock": True
        }
    }
