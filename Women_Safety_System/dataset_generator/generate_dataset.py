import pandas as pd
import random
import math

ROWS = 5000

data = []

hr = 75
sys = 120
dia = 80
spo2 = 98
stress = 0

for t in range(ROWS):

    # -------- NORMAL BODY VARIATION --------
    hr += random.randint(-3,3)
    sys += random.randint(-2,2)
    dia += random.randint(-2,2)
    spo2 += random.choice([-1,0,1])

    # clamp
    hr = max(55,min(130,hr))
    sys = max(100,min(160,sys))
    dia = max(60,min(100,dia))
    spo2 = max(85,min(100,spo2))

    # -------- STRESS DRIFT --------
    if random.random() < 0.05:
        stress = min(2, stress+1)
    elif random.random() < 0.03:
        stress = max(0, stress-1)

    # -------- PANIC EVENT --------
    if random.random() < 0.02:
        hr += random.randint(25,45)
        stress = 2

    # -------- LOW OXYGEN EVENT --------
    if random.random() < 0.01:
        spo2 -= random.randint(5,10)

    # -------- ATTACK EVENT --------
    if random.random() < 0.005:
        hr += random.randint(40,60)
        sys += random.randint(20,30)
        spo2 -= random.randint(10,15)
        stress = 2

    # -------- SENSOR NOISE --------
    hr += random.randint(-2,2)
    spo2 += random.choice([-1,0,1])

    # clamp again
    hr = max(55,min(150,hr))
    sys = max(100,min(180,sys))
    dia = max(60,min(120,dia))
    spo2 = max(80,min(100,spo2))

    # -------- RISK SCORE --------
    risk_score = 0

    if hr > 120 or hr < 55:
        risk_score += 2
    elif hr > 100:
        risk_score += 1

    if spo2 < 90:
        risk_score += 2
    elif spo2 < 95:
        risk_score += 1

    if sys > 150 or dia > 100:
        risk_score += 2
    elif sys > 140:
        risk_score += 1

    risk_score += stress

    # -------- FINAL LABEL --------
    if risk_score >= 5:
        risk = 2
    elif risk_score >= 2:
        risk = 1
    else:
        risk = 0

    data.append([hr,sys,dia,spo2,stress,risk])

# -------- SAVE --------
df = pd.DataFrame(data,columns=[
    "HeartRate","Sys","Dia","SpO2","Stress","Risk"
])

df.to_excel("training_dataset.xlsx", index=False)

print("Advanced dataset generated successfully.")
