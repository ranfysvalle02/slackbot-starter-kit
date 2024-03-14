from flask import Flask, request, jsonify

app = Flask(__name__)

actions = [{
    "type": "actions",
    "elements": [
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "emoji": True,
                "text": ":+1:"
            },
            "value": ":+1:",
            "action_id": "thumbs_up"
        },
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "emoji": True,
                "text": ":-1:"
            },
            "value": ":-1:",
            "action_id": "thumbs_down"
        }
    ]
}]

# Hardcoded responses and sources for testing
hardcoded_data = {
    "What is the meaning of life?": {
        "response":  [
            {"type": "section", "text": {"type": "mrkdwn", "text": "*The meaning of life is a philosophical question. Here are some possible perspectives:*\n\n* **Existentialism:** Create your own meaning.\n* **Religion:** Find meaning through faith.\n* **Hedonism:** Seek pleasure and happiness."}},
        ],
        "sources": [
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Source 1: Wikipedia - Meaning of Life* https://en.wikipedia.org/wiki/Meaning_of_life"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Source 2: Philosophybasics - The Meaning of Life* https://www.philosophybasics.com/branch_meaning_of_life.html"}}
        ]
    },
}


@app.route('/rag_service', methods=['GET'])
def rag_service():
    question = request.args.get('question')

    if question in hardcoded_data:
        answer_data = hardcoded_data[question]
    else:
        answer_data = {
            "response":  [
                {"type": "section", "text": {"type": "mrkdwn", "text": "I don't have an answer for that yet."}},
            ],
            "sources": []
        }

    return jsonify({
        "question_asked": question,
        "sources-blocks": answer_data['sources'],
        "response-blocks": answer_data['response'],
        "action-blocks": actions
    })
@app.route('/thread_rag_service', methods=['POST'])
def thread_rag_service():
    data = request.get_json()
    history = data.get('history')
    question = request.form.get('question')
    print(history)
    if question in hardcoded_data:
        answer_data = hardcoded_data[question]
    else:
        answer_data = {
            "response":  [
                {"type": "section", "text": {"type": "mrkdwn", "text": "THREAD RESPONSE: \n\n `"+str(history)[:2500]+"`"}},
            ],
            "sources": []
        }

    return jsonify({
        "question_asked": question,
        "sources-blocks": answer_data['sources'],
        "response-blocks": answer_data['response'],
        "action-blocks": actions
    })

if __name__ == '__main__':
    app.run(debug=True)