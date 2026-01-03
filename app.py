from fastapi import FastAPI, HTTPException
import uuid

app = FastAPI()


# -----------------------------
# Validators
# -----------------------------

def validate_amount(amount):
    return isinstance(amount, int) and amount >= 1


def validate_currency(currency):
    return isinstance(currency, str) and len(currency) == 3


def validate_email(email):
    return isinstance(email, str) and "@" in email and "." in email


def generate_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# -----------------------------
# Fake Repository
# -----------------------------

class FakeRepository:

    def __init__(self):
        self.customers = {}
        self.payments = {}
        self.refunds = {}

    def save_customer(self, customer):
        self.customers[customer["id"]] = customer
        return customer

    def get_customer(self, cid):
        return self.customers.get(cid)

    def save_payment(self, payment):
        self.payments[payment["id"]] = payment
        return payment

    def get_payment(self, pid):
        return self.payments.get(pid)

    def get_refunds_for_payment(self, pid):
        return [r for r in self.refunds.values() if r["payment_id"] == pid]

    def save_refund(self, refund):
        self.refunds[refund["id"]] = refund
        return refund


# -----------------------------
# Payment Service
# -----------------------------

class PaymentService:

    def __init__(self, repo):
        self.repo = repo

    def create_customer(self, name, email):

        if not name or len(name) > 100:
            raise ValueError("Invalid name")

        if not validate_email(email):
            raise ValueError("Invalid email")

        customer = {
            "id": generate_id("cus"),
            "name": name,
            "email": email
        }

        return self.repo.save_customer(customer)

    def create_payment(self, customer_id, amount, currency):

        if not self.repo.get_customer(customer_id):
            raise ValueError("Customer not found")

        if not validate_amount(amount):
            raise ValueError("Invalid amount")

        if not validate_currency(currency):
            raise ValueError("Invalid currency")

        payment = {
            "id": generate_id("pay"),
            "customer_id": customer_id,
            "amount": amount,
            "currency": currency,
            "status": "pending"
        }

        return self.repo.save_payment(payment)

    def capture(self, payment_id):

        payment = self.repo.get_payment(payment_id)

        if not payment:
            raise ValueError("Payment not found")

        if payment["status"] != "pending":
            raise ValueError("Invalid state")

        payment["status"] = "succeeded"

        return payment

    def fail(self, payment_id):

        payment = self.repo.get_payment(payment_id)

        if not payment:
            raise ValueError("Payment not found")

        if payment["status"] != "pending":
            raise ValueError("Invalid state")

        payment["status"] = "failed"

        return payment

    def refund(self, payment_id, amount):

        payment = self.repo.get_payment(payment_id)

        if not payment:
            raise ValueError("Payment not found")

        if payment["status"] != "succeeded":
            raise ValueError("Cannot refund")

        refunds = self.repo.get_refunds_for_payment(payment_id)

        total_refunded = sum(r["amount"] for r in refunds)

        if total_refunded + amount > payment["amount"]:
            raise ValueError("Refund exceeds payment")

        refund = {
            "id": generate_id("ref"),
            "payment_id": payment_id,
            "amount": amount,
            "status": "succeeded"
        }

        return self.repo.save_refund(refund)


repo = FakeRepository()
service = PaymentService(repo)


# -----------------------------
# API Routes
# -----------------------------

@app.post("/customers")
def create_customer(data: dict):
    try:
        return service.create_customer(data["name"], data["email"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/payments")
def create_payment(data: dict):
    try:
        return service.create_payment(
            data["customer_id"],
            data["amount"],
            data["currency"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/payments/{payment_id}/capture")
def capture(payment_id: str):
    try:
        return service.capture(payment_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/payments/{payment_id}/fail")
def fail(payment_id: str):
    try:
        return service.fail(payment_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))