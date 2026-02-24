import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from .config import COUNTRIES, CITIES, MERCHANT_CATEGORIES, PERSONAS, CURRENCIES

fake = Faker()

def _choice_weighted(items, weights):
    probs = np.array(weights, dtype=float)
    probs = probs / probs.sum()
    return items[np.random.choice(len(items), p=probs)]

def generate(
    seed: int = 42,
    days: int = 30,
    users: int = 5000,
    merchants: int = 800,
    attempts: int = 200000,
    out_dir: str = "data"
):
    np.random.seed(seed)
    Faker.seed(seed)
    os.makedirs(out_dir, exist_ok=True)

    # ---- Users
    user_rows = []
    for i in range(users):
        country = np.random.choice(COUNTRIES, p=[0.28, 0.10, 0.22, 0.25, 0.15])
        city = np.random.choice(CITIES[country])
        persona = _choice_weighted(PERSONAS, [0.45, 0.30, 0.10, 0.15])
        signup_date = fake.date_between(start_date="-180d", end_date="-1d")
        risk_profile = _choice_weighted(["low", "medium", "high"], [0.75, 0.20, 0.05])

        user_rows.append({
            "user_id": f"u_{i:07d}",
            "country": country,
            "city": city,
            "persona": persona,
            "signup_date": signup_date,
            "risk_profile": risk_profile
        })
    users_df = pd.DataFrame(user_rows)

    # ---- Merchants
    merchant_rows = []
    for i in range(merchants):
        country = np.random.choice(COUNTRIES, p=[0.25, 0.12, 0.22, 0.26, 0.15])
        city = np.random.choice(CITIES[country])
        category = np.random.choice(MERCHANT_CATEGORIES)
        onboarding_date = fake.date_between(start_date="-365d", end_date="-10d")

        merchant_rows.append({
            "merchant_id": f"m_{i:06d}",
            "country": country,
            "city": city,
            "category": category,
            "onboarding_date": onboarding_date
        })
    merchants_df = pd.DataFrame(merchant_rows)

    # ---- Devices (1 device per user for MVP)
    device_types = ["android", "ios", "web"]
    devices_df = pd.DataFrame({
        "device_id": [f"d_{i:07d}" for i in range(users)],
        "user_id": users_df["user_id"].values,
        "device_type": np.random.choice(device_types, size=users, p=[0.65, 0.25, 0.10]),
        "first_seen": [fake.date_between(start_date="-120d", end_date="-1d") for _ in range(users)]
    })

    # ---- Payment attempts (event-style)
    start = datetime.utcnow() - timedelta(days=days)
    timestamps = [start + timedelta(seconds=int(np.random.rand() * days * 24 * 3600)) for _ in range(attempts)]
    timestamps.sort()

    user_ids = users_df["user_id"].values
    merchant_ids = merchants_df["merchant_id"].values

    # Amount by category (rough but realistic)
    cat_amount = {
        "grocery": (5, 80),
        "cafe": (2, 20),
        "restaurant": (8, 120),
        "fuel": (10, 100),
        "telecom": (2, 50),
        "transport": (1, 30),
        "electronics": (30, 1500),
        "pharmacy": (3, 90),
        "services": (5, 250),
    }

    rows = []
    # Faster lookup maps (avoid repeated dataframe filtering)
    user_map = users_df.set_index("user_id").to_dict(orient="index")
    merchant_map = merchants_df.set_index("merchant_id").to_dict(orient="index")
    device_map = devices_df.set_index("user_id")["device_id"].to_dict()

    for i in range(attempts):
        uid = np.random.choice(user_ids)
        user = user_map[uid]
        did = device_map[uid]

        mid = np.random.choice(merchant_ids)
        merch = merchant_map[mid]

        cur = CURRENCIES[user["country"]]
        low, high = cat_amount[merch["category"]]

        # lognormal -> more small txns than big ones
        amount = float(np.round(np.random.lognormal(mean=np.log((low + high) / 2), sigma=0.6), 2))
        amount = float(np.clip(amount, low, high))

        channel = np.random.choice(["qr", "inapp", "pos", "online"], p=[0.35, 0.30, 0.20, 0.15])

        base_fail = 0.06
        if user["risk_profile"] == "medium":
            base_fail += 0.02
        elif user["risk_profile"] == "high":
            base_fail += 0.06

        status = "approved" if np.random.rand() > base_fail else "failed"
        failure_reason = None
        if status == "failed":
            failure_reason = np.random.choice(
                ["insufficient_funds", "network_error", "issuer_declined", "risk_block"],
                p=[0.35, 0.25, 0.30, 0.10]
            )

        rows.append({
            "attempt_id": f"a_{i:09d}",
            "ts": timestamps[i],
            "user_id": uid,
            "device_id": did,
            "merchant_id": mid,
            "user_country": user["country"],
            "merchant_country": merch["country"],
            "amount": amount,
            "currency": cur,
            "channel": channel,
            "status": status,
            "failure_reason": failure_reason
        })

    attempts_df = pd.DataFrame(rows)

    # Save as Parquet
    users_df.to_parquet(os.path.join(out_dir, "users.parquet"), index=False)
    merchants_df.to_parquet(os.path.join(out_dir, "merchants.parquet"), index=False)
    devices_df.to_parquet(os.path.join(out_dir, "devices.parquet"), index=False)
    attempts_df.to_parquet(os.path.join(out_dir, "payment_attempts.parquet"), index=False)

    print(f"✅ Generated dataset in ./{out_dir}")
    print(f"users={len(users_df)} merchants={len(merchants_df)} devices={len(devices_df)} attempts={len(attempts_df)}")

if __name__ == "__main__":
    generate()