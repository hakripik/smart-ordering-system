import pandas as pd #pandas is for data manipulation and analysis 
from sklearn.metrics.pairwise import cosine_similarity #
import numpy as np #handle arrays. also for scipy

def load_data():
    foods = pd.read_csv("data/foods.csv")
    users = pd.read_csv("data/users.csv")
    interactions = pd.read_csv("data/interactions.csv")
    return foods, users, interactions #returns DataFrame object

def get_recommendations(user_id, foods, users, interactions, top_n=3):
    user = users[users["user_id"] == user_id].iloc[0]

    # --- Content-based filtering ---
    # Build feature vectors for each food
    feature_cols = ["spicy", "sweet", "halal", "vegetarian"]
    food_features = foods[feature_cols].values.astype(float)

    # Build user preference vector from their profile
    user_vector = np.array([
        user["likes_spicy"],
        0,  # sweet — neutral
        user["halal_required"],
        user["vegetarian"]
    ]).reshape(1, -1).astype(float)

    # Compute similarity
    similarities = cosine_similarity(user_vector, food_features)[0]
    foods = foods.copy()
    foods["score"] = similarities

    # --- Filter by budget ---
    foods = foods[foods["price"] <= user["budget"]]

    # --- Filter out already rated items ---
    rated = interactions[interactions["user_id"] == user_id]["food_id"].tolist()
    foods = foods[~foods["food_id"].isin(rated)]

    # --- Collaborative boost ---
    # Find users with similar taste (also liked spicy/halal etc.)
    for _, row in interactions.iterrows():
        if row["user_id"] == user_id:
            continue
        other_user = users[users["user_id"] == row["user_id"]].iloc[0]
        # Simple check: if other user has same spicy/halal preference
        if (other_user["likes_spicy"] == user["likes_spicy"] and
            other_user["halal_required"] == user["halal_required"]):
            # Boost food score slightly if similar user rated it highly
            if row["rating"] >= 4:
                foods.loc[foods["food_id"] == row["food_id"], "score"] += 0.1

    # Sort and return top N
    top = foods.sort_values("score", ascending=False).head(top_n)
    return top

def explain_recommendation(food_row, user_row):
    reasons = []
    if food_row["spicy"] and user_row["likes_spicy"]:
        reasons.append("you like spicy food")
    if food_row["halal"] and user_row["halal_required"]:
        reasons.append("it's halal")
    if food_row["vegetarian"] and user_row["vegetarian"]:
        reasons.append("it's vegetarian")
    if food_row["price"] <= user_row["budget"]:
        reasons.append(f"within your ${user_row['budget']} budget")
    if not reasons:
        reasons.append("it matches your general preferences")
    return "Recommended because: " + ", ".join(reasons)

def save_rating(user_id, food_id, rating):
    interactions = pd.read_csv("data/interactions.csv")
    # Update if exists, else append
    mask = (interactions["user_id"] == user_id) & (interactions["food_id"] == food_id)
    if mask.any():
        interactions.loc[mask, "rating"] = rating
    else:
        new_row = pd.DataFrame([{"user_id": user_id, "food_id": food_id, "rating": rating}])
        interactions = pd.concat([interactions, new_row], ignore_index=True)
    interactions.to_csv("data/interactions.csv", index=False)
