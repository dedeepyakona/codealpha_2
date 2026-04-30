from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# Load intents
with open('intents.json', encoding="utf-8") as file:
    data = json.load(file)

# ---------------- INTENT RESPONSE ----------------
def get_intent_response(message):
    message = message.lower()
    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            if pattern in message:
                return intent["responses"][0]
    return "Type 'start' to begin 💡"

# ---------------- BODY TYPE LOGIC ----------------
def detect_body_shape(inputs):
    waist = inputs.get("waist")
    shoulders = inputs.get("shoulders")
    hips = inputs.get("hips")
    bust = inputs.get("bust")
    height = inputs.get("height")
    size = inputs.get("size")

    if height == "1":
        return "Petite"
    elif size == "3":
        return "Plus Size"
    elif waist == "1" and shoulders == "2" and hips == "2":
        return "Hourglass"
    elif waist == "3":
        return "Apple"
    elif hips == "1" and shoulders == "3":
        return "Pear"
    elif shoulders == "1" and hips == "3":
        return "Inverted Triangle"
    elif shoulders == "3" and hips == "3" and bust == "3":
        return "Lean Rectangle"
    else:
        return "Rectangle"

# ---------------- RECOMMENDATIONS ----------------
def jeans_recommendation(shape):
    if shape in ["Hourglass", "Pear"]:
        return ["Bootcut High-Rise Jeans"]
    elif shape in ["Apple", "Inverted Triangle"]:
        return ["Straight Fit Jeans"]
    elif shape == "Petite":
        return ["Skinny Jeans"]
    else:
        return ["Wide-Leg Jeans"]

def tops_recommendation(shape):
    if shape == "Apple":
        return ["V-Neck Tops"]
    elif shape == "Pear":
        return ["Off-Shoulder Tops"]
    elif shape == "Hourglass":
        return ["Fitted Tops"]
    else:
        return ["Peplum Tops"]

def ethnic_recommendation(shape):
    if shape == "Hourglass":
        return ["Sarees / Anarkali"]
    elif shape == "Pear":
        return ["A-Line Lehenga"]
    else:
        return ["Straight Kurtis"]

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip().lower()
        state = data.get("state", {})

        if user_message in ["quit", "exit", "bye"]:
            return jsonify({
                "reply": "Goodbye! Stay stylish 💫",
                "state": {}
            })

        if user_message == "start":
            return jsonify({
                "reply": "✨ What would you like to do?\n1. Body Shape Detection\n2. Outfit Suggestions",
                "state": {"step": "main_menu"}
            })

        if state.get("step") == "main_menu":
            if user_message == "1":
                return jsonify({
                    "reply": "💃 Let's find your body type!\nWaist (1. defined / 2. medium / 3. not defined):",
                    "state": {"step": "waist"}
                })
            elif user_message == "2":
                return jsonify({
                    "reply": "👗 Choose body type:\n1. Hourglass 2. Apple 3. Pear 4. Inverted Triangle 5. Rectangle 6. Petite 7. Plus Size",
                    "state": {"step": "manual_shape"}
                })

        steps = ["waist", "shoulders", "hips", "bust", "height", "size"]

        questions = {
            "waist": "Shoulders (1. broad / 2. medium / 3. narrow):",
            "shoulders": "Hips (1. wide / 2. medium / 3. narrow):",
            "hips": "Bust (1. full / 2. medium / 3. small):",
            "bust": "Height (1. short / 2. avg / 3. tall):",
            "height": "Body size (1. slim / 2. medium / 3. plus):"
        }

        if state.get("step") in steps:
            state[state["step"]] = user_message

            if state["step"] != "size":
                next_step = steps[steps.index(state["step"]) + 1]
                return jsonify({
                    "reply": questions[state["step"]],
                    "state": {**state, "step": next_step}
                })
            else:
                shape = detect_body_shape(state)
                return jsonify({
                    "reply": f"🎯 Your body type: {shape}\n\n💡 Can I suggest outfits for you? (yes/no)",
                    "state": {"step": "ask_suggestion", "shape": shape}
                })

        if state.get("step") == "manual_shape":
            mapping = {
                "1": "Hourglass",
                "2": "Apple",
                "3": "Pear",
                "4": "Inverted Triangle",
                "5": "Rectangle",
                "6": "Petite",
                "7": "Plus Size"
            }

            shape = mapping.get(user_message, "Rectangle")

            return jsonify({
                "reply": f"🎯 Your body type: {shape}\n\n💡 Can I suggest outfits for you? (yes/no)",
                "state": {"step": "ask_suggestion", "shape": shape}
            })

        if state.get("step") == "ask_suggestion":
            if user_message in ["yes", "y"]:
                return jsonify({
                    "reply": "📍 Occasion:\n1. Casual 2. Party 3. College",
                    "state": {"step": "occasion", "shape": state["shape"]}
                })
            else:
                return jsonify({
                    "reply": "👍 Okay! Type 'start' anytime 💖",
                    "state": {}
                })

        if state.get("step") == "occasion":
            return jsonify({
                "reply": "✨ What do you want?\n1. Jeans 2. Tops 3. Ethnic",
                "state": {"step": "outfit", "shape": state["shape"]}
            })

        if state.get("step") == "outfit":
            shape = state.get("shape")

            if user_message == "1":
                items = jeans_recommendation(shape)
                title = "👖 Jeans Recommendations"
            elif user_message == "2":
                items = tops_recommendation(shape)
                title = "👚 Top Recommendations"
            elif user_message == "3":
                items = ethnic_recommendation(shape)
                title = "👗 Ethnic Wear"
            else:
                return jsonify({"reply": "Invalid choice ❌", "state": state})

            response = f"{title}:\n" + "\n".join([f"✔ {i}" for i in items])
            response += "\n\n💡 Type 'start' to begin"

            return jsonify({"reply": response, "state": {}})

        return jsonify({
            "reply": get_intent_response(user_message),
            "state": state
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"reply": "⚠ Server error", "state": {}})

# ---------------- RUN (RAILWAY SAFE) ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
