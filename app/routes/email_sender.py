from flask import Blueprint, request, jsonify, url_for
import logging
import app.utils.email_sender as email_sender

email_sender_bp = Blueprint('email_sender', __name__)

@email_sender_bp.route('/email/send', methods=['POST'])
def send_email():
    try:
        data = request.get_json()
        email=data.get('email')
        msg=data.get('message')
        logging.info("Sending message : "+msg)
        email_sender.send_email(email,msg,False)
        logging.info("Message Sent")
        return jsonify({"message": "Email sent successfully"}), 200 

    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return jsonify({"message": "Error occured while sending messge.Pls try again"}), 500