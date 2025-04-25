from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import random
import json
import os
from groq import Groq

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("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"))

# --------------------
# Models
# --------------------
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    completed = db.Column(db.Boolean, default=False)

# --------------------
# Routes
# --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/goals', methods=['GET'])
def get_goals():
    today = date.today().isoformat()
    goals = Goal.query.filter_by(date=today).all()
    return jsonify([{'id': g.id, 'text': g.text, 'completed': g.completed} for g in goals])

@app.route('/add', methods=['POST'])
def add_goal():
    data = request.get_json()
    new_goal = Goal(text=data['text'], date=date.today().isoformat())
    db.session.add(new_goal)
    db.session.commit()
    return jsonify({'message': 'Goal added successfully!'})

@app.route('/complete/<int:goal_id>', methods=['POST'])
def complete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    goal.completed = True
    db.session.commit()
    return jsonify({'message': 'Goal marked as completed!'})

@app.route('/delete/<int:goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Goal deleted successfully!'})

@app.route('/stats', methods=['GET'])
def get_stats():
    all_dates = db.session.query(Goal.date).distinct().all()
    chart_data = []

    for (d,) in all_dates:
        total = Goal.query.filter_by(date=d).count()
        done = Goal.query.filter_by(date=d, completed=True).count()
        chart_data.append({'date': d, 'set': total, 'completed': done})
    
    return jsonify(chart_data)


@app.route('/history', methods=['GET'])
def get_history():
    # Get all unique dates with goals
    dates = db.session.query(Goal.date).distinct().order_by(Goal.date.desc()).all()
    
    history = []
    for (d,) in dates:
        goals = Goal.query.filter_by(date=d).order_by(Goal.completed).all()
        history.append({
            'date': d,
            'goals': [{'text': g.text, 'completed': g.completed} for g in goals]
        })
    
    return jsonify(history)


@app.route('/quote', methods=['GET'])
def get_quote():
    try:
        # Get a motivational quote from Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a motivational coach. Provide a short, inspiring quote about productivity, goal-setting, or personal growth."
                },
                {
                    "role": "user",
                    "content": "Give me a motivational quote to help me achieve my goals today."
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=50
        )
        
        quote = chat_completion.choices[0].message.content
        # Remove quotation marks if they exist
        quote = quote.strip('"').strip("'")
        return jsonify({'quote': quote, 'author': "Motivational Coach"})
    except Exception as e:
        print(f"Error fetching quote from Groq: {e}")
        # Fallback quotes if Groq fails
        fallback_quotes = [
            "Believe you can and you're halfway there.",
            "Do not watch the clock; do what it does. Keep going.",
            "Push yourself, because no one else is going to do it for you.",
            "Success is what comes after you stop making excuses.",
            "The pain you feel today will be the strength you feel tomorrow."
            
            
        ]
        return jsonify({'quote': random.choice(fallback_quotes), 'author': "Unknown"})

# --------------------
# Run Server
# --------------------
if __name__ == '__main__':
    app.run(debug=True)
