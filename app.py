from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from routes import app
from database import init_db

socketio = SocketIO(app)

@socketio.on('send_message')
def handle_send_message_event(data):
    if data['message'].strip() != "":
        app.logger.info(f"{data['username']} has sent message to the room {data['room']}: {data['message']}")
        emit('receive_message', data, room=data['room'])
    else:
        emit('error', {'error': 'Empty message'}, room=request.sid)


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    emit('join_room_announcement', data, room=data['room'])

@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    emit('leave_room_announcement', data, room=data['room'])

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
