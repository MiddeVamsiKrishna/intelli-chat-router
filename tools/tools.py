"""
tools/tools.py

Real tool functions for the Healthcare Support Chatbot.
Unlike Day 1's dummy versions, these persist data to local JSON files
acting as a lightweight mock database — good enough for a prototype,
no real DB server needed.

Each function still returns a dict with "status" and "message" so the
response layer can turn it into a natural-language reply.
"""

import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.json")
REFILLS_FILE = os.path.join(DATA_DIR, "refills.json")
ESCALATIONS_FILE = os.path.join(DATA_DIR, "escalations.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(filepath):
    _ensure_data_dir()
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        return json.load(f)


def _save_json(filepath, data):
    _ensure_data_dir()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def book_appointment(patient_name: str, department: str, date: str) -> dict:
    """Book a new appointment and persist it to appointments.json."""
    appointments = _load_json(APPOINTMENTS_FILE)
    appointment_id = f"APT-{uuid.uuid4().hex[:6].upper()}"

    appointments[appointment_id] = {
        "patient_name": patient_name,
        "department": department,
        "date": date,
        "status": "Confirmed",
        "created_at": datetime.now().isoformat(),
    }
    _save_json(APPOINTMENTS_FILE, appointments)

    return {
        "status": "success",
        "tool": "book_appointment",
        "appointment_id": appointment_id,
        "message": (
            f"Appointment booked for {patient_name} in {department} "
            f"on {date}. Your appointment ID is {appointment_id}."
        ),
    }


def cancel_appointment(appointment_id: str) -> dict:
    """Cancel an existing appointment by ID."""
    appointments = _load_json(APPOINTMENTS_FILE)

    if appointment_id not in appointments:
        return {
            "status": "error",
            "tool": "cancel_appointment",
            "message": f"Could not find appointment with ID {appointment_id}.",
        }

    appointments[appointment_id]["status"] = "Cancelled"
    _save_json(APPOINTMENTS_FILE, appointments)

    return {
        "status": "success",
        "tool": "cancel_appointment",
        "appointment_id": appointment_id,
        "message": f"Appointment {appointment_id} has been cancelled successfully.",
    }


def check_appointment_status(appointment_id: str) -> dict:
    """Check the real status of an existing appointment."""
    appointments = _load_json(APPOINTMENTS_FILE)

    if appointment_id not in appointments:
        return {
            "status": "error",
            "tool": "check_appointment_status",
            "message": f"Could not find appointment with ID {appointment_id}.",
        }

    appt = appointments[appointment_id]
    return {
        "status": "success",
        "tool": "check_appointment_status",
        "appointment_id": appointment_id,
        "appointment_status": appt["status"],
        "message": (
            f"Appointment {appointment_id} ({appt['department']}, "
            f"{appt['date']}) is currently '{appt['status']}'."
        ),
    }


def request_refill(patient_id: str, medication: str) -> dict:
    """Request a prescription refill and persist it to refills.json."""
    refills = _load_json(REFILLS_FILE)
    request_id = f"RX-{uuid.uuid4().hex[:6].upper()}"

    refills[request_id] = {
        "patient_id": patient_id,
        "medication": medication,
        "status": "Pending pharmacist approval",
        "created_at": datetime.now().isoformat(),
    }
    _save_json(REFILLS_FILE, refills)

    return {
        "status": "success",
        "tool": "request_refill",
        "request_id": request_id,
        "message": (
            f"Refill request for '{medication}' submitted for patient {patient_id}. "
            f"Request ID: {request_id}. A pharmacist will review and approve it."
        ),
    }


def find_doctor(specialty: str) -> dict:
    """Find available doctors for a given specialty/department (static lookup table)."""
    doctors_directory = {
        "cardiology": ["Dr. A. Rao", "Dr. S. Mehta"],
        "dermatology": ["Dr. K. Iyer"],
        "general medicine": ["Dr. P. Sharma", "Dr. N. Gupta"],
        "orthopedics": ["Dr. R. Verma"],
        "skin": ["Dr. K. Iyer"],  # alias for dermatology
    }
    doctors = doctors_directory.get(specialty.lower(), ["Dr. J. Smith (General)"])
    return {
        "status": "success",
        "tool": "find_doctor",
        "specialty": specialty,
        "doctors": doctors,
        "message": f"Available doctors for {specialty}: {', '.join(doctors)}.",
    }


def escalate_to_human(reason: str = "medical query outside chatbot scope") -> dict:
    """Escalate to a human, logging the escalation to escalations.json."""
    escalations = _load_json(ESCALATIONS_FILE)
    ticket_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"

    escalations[ticket_id] = {
        "reason": reason,
        "created_at": datetime.now().isoformat(),
    }
    _save_json(ESCALATIONS_FILE, escalations)

    return {
        "status": "escalated",
        "tool": "escalate_to_human",
        "ticket_id": ticket_id,
        "message": (
            "I'm not able to provide medical advice or diagnoses. "
            f"I've created escalation ticket {ticket_id} so a healthcare "
            "professional can assist you directly."
        ),
    }


# Maps intent names (from intent/router.py) to their corresponding tool function.
# app.py will use this to call the right tool based on detected intent.
TOOL_REGISTRY = {
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "check_appointment_status": check_appointment_status,
    "request_refill": request_refill,
    "find_doctor": find_doctor,
    "escalate_to_human": escalate_to_human,
}


if __name__ == "__main__":
    # Smoke test — also verifies data persists to tools/data/*.json
    result = book_appointment("John Doe", "Cardiology", "2026-08-10")
    print(result)
    appt_id = result["appointment_id"]

    print(check_appointment_status(appt_id))
    print(cancel_appointment(appt_id))
    print(request_refill("PID-9981", "Metformin"))
    print(find_doctor("Cardiology"))
    print(escalate_to_human("Patient asked about chest pain symptoms"))
    print(f"\nData persisted to: {DATA_DIR}")
