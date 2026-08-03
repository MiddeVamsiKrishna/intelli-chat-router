"""
tools/tools.py

Dummy (placeholder) tool functions for the Healthcare Support Chatbot.
These simulate real backend actions (appointments, prescriptions, doctor lookup)
with mock/fake data. Real logic (DB calls, external APIs) will be added on Day 3.

Each function:
- Takes structured arguments extracted by the intent/LLM layer
- Returns a dict with a "status" and a "message" (and any relevant data)
  so the response layer can turn it into a natural-language reply.
"""

from datetime import datetime
import random
import uuid


def book_appointment(patient_name: str, department: str, date: str) -> dict:
    """
    Book a new appointment for a patient with a given department on a given date.
    """
    appointment_id = f"APT-{uuid.uuid4().hex[:6].upper()}"
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
    """
    Cancel or reschedule an existing appointment by ID.
    """
    # Dummy logic: randomly simulate found/not found
    if appointment_id.startswith("APT-"):
        return {
            "status": "success",
            "tool": "cancel_appointment",
            "appointment_id": appointment_id,
            "message": f"Appointment {appointment_id} has been cancelled successfully.",
        }
    return {
        "status": "error",
        "tool": "cancel_appointment",
        "message": f"Could not find appointment with ID {appointment_id}.",
    }


def check_appointment_status(appointment_id: str) -> dict:
    """
    Check the status of an existing appointment.
    """
    dummy_statuses = ["Confirmed", "Pending", "Completed", "Cancelled"]
    status = random.choice(dummy_statuses)
    return {
        "status": "success",
        "tool": "check_appointment_status",
        "appointment_id": appointment_id,
        "appointment_status": status,
        "message": f"Appointment {appointment_id} is currently '{status}'.",
    }


def request_refill(patient_id: str, medication: str) -> dict:
    """
    Request a prescription refill for a given patient and medication.
    NOTE: This is administrative only — it does NOT approve dosages or
    give medical advice. A pharmacist/doctor must approve the refill.
    """
    request_id = f"RX-{uuid.uuid4().hex[:6].upper()}"
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
    """
    Find available doctors for a given specialty/department.
    """
    dummy_doctors = {
        "cardiology": ["Dr. A. Rao", "Dr. S. Mehta"],
        "dermatology": ["Dr. K. Iyer"],
        "general medicine": ["Dr. P. Sharma", "Dr. N. Gupta"],
        "orthopedics": ["Dr. R. Verma"],
    }
    doctors = dummy_doctors.get(specialty.lower(), ["Dr. J. Smith (General)"])
    return {
        "status": "success",
        "tool": "find_doctor",
        "specialty": specialty,
        "doctors": doctors,
        "message": f"Available doctors for {specialty}: {', '.join(doctors)}.",
    }


def escalate_to_human(reason: str = "medical query outside chatbot scope") -> dict:
    """
    Escalation tool — used whenever a user asks something the chatbot should
    NOT answer directly (e.g. diagnosis, symptoms, medical advice, or any
    request involving sensitive personal health information the bot can't verify).
    This is an important safety guardrail for the healthcare domain.
    """
    ticket_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"
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


if __name__ == "__main__":
    # Quick manual smoke test
    print(book_appointment("John Doe", "Cardiology", "2026-08-10"))
    print(cancel_appointment("APT-123ABC"))
    print(check_appointment_status("APT-123ABC"))
    print(request_refill("PID-9981", "Metformin"))
    print(find_doctor("Cardiology"))
    print(escalate_to_human("Patient asked about chest pain symptoms"))
