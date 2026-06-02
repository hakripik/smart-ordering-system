import streamlit as st
import pandas as pd
from recommender import load_data, get_recommendations, explain_recommendation, save_rating

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Food Court",
    page_icon="🍽️",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .food-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #ff6b35;
    }
    .rec-card {
        background: #fff8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #ffa500;
    }
    .explain-text {
        color: #666;
        font-size: 0.85em;
        font-style: italic;
    }
    .tag-pill {
        display: inline-block;
        background: #e8f4f8;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.78em;
        margin: 2px;
        color: #2c7a9e;
    }
    .order-summary {
        background: #f0fff4;
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid #38a169;
    }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
foods, users, interactions = load_data()

# ── Session state ─────────────────────────────────────────────────────────────
if "cart" not in st.session_state:
    st.session_state.cart = []
if "order_placed" not in st.session_state:
    st.session_state.order_placed = False
if "ratings_submitted" not in st.session_state:
    st.session_state.ratings_submitted = False

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🍽️ Smart Food Court")
st.caption("AI-powered ordering system — personalized just for you")
st.divider()

# ── Sidebar: User selection ───────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Select User")
    user_names = users["name"].tolist()
    selected_name = st.selectbox("Who are you?", user_names)
    selected_user = users[users["name"] == selected_name].iloc[0]
    user_id = selected_user["user_id"]

    st.divider()
    st.subheader("Your preferences")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Budget", f"${selected_user['budget']}")
        st.metric("Spicy", "✅ Yes" if selected_user["likes_spicy"] else "❌ No")
    with col2:
        st.metric("Halal", "✅ Yes" if selected_user["halal_required"] else "Any")
        st.metric("Veg", "✅ Yes" if selected_user["vegetarian"] else "No")

    st.divider()
    # Cart summary in sidebar
    st.subheader("🛒 Your Cart")
    if st.session_state.cart:
        total = 0
        for item_id in st.session_state.cart:
            item = foods[foods["food_id"] == item_id].iloc[0]
            st.write(f"• {item['name']} — ${item['price']}")
            total += item["price"]
        st.metric("Total", f"${total:.2f}")
        if not st.session_state.order_placed:
            if st.button("✅ Place Order", use_container_width=True, type="primary"):
                st.session_state.order_placed = True
                st.rerun()
    else:
        st.caption("Nothing added yet")

# ── Main content: 3 tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🤖 AI Recommendations", "🍜 Full Menu", "⭐ Rate & Feedback"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — AI Recommendations
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader(f"Picks for you, {selected_name} 👋")
    st.caption("Based on your taste profile and what similar users enjoyed")

    recs = get_recommendations(user_id, foods, users, interactions, top_n=3)

    if recs.empty:
        st.info("You've tried everything on the menu! Check the Full Menu tab.")
    else:
        for _, food in recs.iterrows():
            explanation = explain_recommendation(food, selected_user)

            with st.container():
                st.markdown(f"""
                <div class="rec-card">
                    <strong>🍴 {food['name']}</strong> &nbsp;
                    <span style="color:#888">({food['cuisine']} cuisine)</span><br>
                    <span style="font-size:1.1em; color:#e07b00"><strong>${food['price']}</strong></span>
                    &nbsp;&nbsp;
                    {'🌶️ Spicy' if food['spicy'] else ''}
                    {'🌿 Vegetarian' if food['vegetarian'] else ''}
                    {'✅ Halal' if food['halal'] else ''}
                    <br><br>
                    <span class="explain-text">💡 {explanation}</span>
                </div>
                """, unsafe_allow_html=True)

                col_add, col_skip = st.columns([1, 4])
                with col_add:
                    if food["food_id"] not in st.session_state.cart:
                        if st.button(f"Add to cart", key=f"rec_add_{food['food_id']}"):
                            st.session_state.cart.append(food["food_id"])
                            st.rerun()
                    else:
                        st.success("In cart ✓")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Full Menu
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Browse all stalls")

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        cuisine_filter = st.multiselect(
            "Cuisine", options=foods["cuisine"].unique(), default=[]
        )
    with col_f2:
        max_price = st.slider("Max price ($)", 3.0, 8.0, 6.0, step=0.5)
    with col_f3:
        diet_filter = st.multiselect(
            "Dietary", options=["Halal", "Vegetarian", "Spicy"], default=[]
        )

    # Apply filters
    filtered = foods.copy()
    if cuisine_filter:
        filtered = filtered[filtered["cuisine"].isin(cuisine_filter)]
    filtered = filtered[filtered["price"] <= max_price]
    if "Halal" in diet_filter:
        filtered = filtered[filtered["halal"] == 1]
    if "Vegetarian" in diet_filter:
        filtered = filtered[filtered["vegetarian"] == 1]
    if "Spicy" in diet_filter:
        filtered = filtered[filtered["spicy"] == 1]

    st.caption(f"Showing {len(filtered)} items")

    for _, food in filtered.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="food-card">
                <strong>{food['name']}</strong>
                <span style="color:#888; font-size:0.9em"> — {food['cuisine']}</span><br>
                <span style="color:#e07b00"><strong>${food['price']}</strong></span>
                &nbsp;
                {'🌶️' if food['spicy'] else ''}
                {'🌿' if food['vegetarian'] else ''}
                {'✅' if food['halal'] else ''}
                <br>
                <span class="tag-pill">{food['tags']}</span>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns([1, 5])
            with col_a:
                if food["food_id"] not in st.session_state.cart:
                    if st.button("+ Add", key=f"menu_add_{food['food_id']}"):
                        st.session_state.cart.append(food["food_id"])
                        st.rerun()
                else:
                    st.success("✓ Added")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Rate & Feedback
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.order_placed:
        st.info("Place your order first, then come back here to rate your meal.")
    elif st.session_state.ratings_submitted:
        st.success("🎉 Thanks! Your ratings have been saved. AI recommendations will improve next time.")
        st.balloons()
    else:
        st.subheader("How was your meal?")
        st.caption("Your ratings directly improve future recommendations")

        ratings = {}
        for item_id in st.session_state.cart:
            item = foods[foods["food_id"] == item_id].iloc[0]
            st.markdown(f"**{item['name']}**")
            rating = st.slider(
                f"Rate {item['name']}",
                1, 5, 3,
                key=f"rating_{item_id}",
                label_visibility="collapsed"
            )
            st.caption(f"{'⭐' * rating}")
            ratings[item_id] = rating
            st.write("")

        if st.button("Submit ratings", type="primary"):
            for food_id, rating in ratings.items():
                save_rating(user_id, food_id, rating)
            st.session_state.ratings_submitted = True
            st.rerun()
            

# cant add new user
# chatbot not interactive
# text messy
# add name and pics
