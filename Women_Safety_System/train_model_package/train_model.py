import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ================= LOAD DATASET =================
df = pd.read_excel("training_dataset.xlsx")

print("Dataset Loaded:", df.shape)

# ================= FEATURES & LABEL =================
X = df[["HeartRate","Sys","Dia","SpO2","Stress"]]
y = df["Risk"]

# ================= SPLIT DATA =================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ================= TRAIN MODEL =================
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)

# ================= EVALUATE =================
pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, pred))
print("\nClassification Report:\n", classification_report(y_test, pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, pred))

# ================= SAVE MODEL =================
joblib.dump(model, "women_safety_model.pkl")

print("\nModel saved as women_safety_model.pkl")
