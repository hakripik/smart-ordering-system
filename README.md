# Smart AI Ordering System

An AI-powered food ordering system built on a smart table concept.
Uses a recommendation engine to personalise food suggestions for each user.

## Features
- Content-based filtering using cosine similarity
- Collaborative boost from user interaction data
- Explainable recommendations ("suggested because: spicy, within budget")
- Feedback loop — ratings improve future recommendations
- Full Streamlit UI with menu filtering, cart, and rating system

## How to run
pip install -r requirements.txt
streamlit run app.py

## Tech stack
Python, Pandas, Scikit-learn, Streamlit

## Project context
Built as an extension of a self-cleaning smart table hardware project.
The AI system handles the ordering and personalisation layer.
