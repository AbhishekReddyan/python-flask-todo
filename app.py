import os
from flask import Flask, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from database import SessionLocal, engine
from models import Base, Todo

def create_app():
    app = Flask(__name__)

    # Create tables on first run; safe for simple services
    Base.metadata.create_all(bind=engine)

    @app.route('/health', methods=['GET'])
    def health():
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return jsonify({'status': 'ok', 'database': 'reachable'}), 200
        except Exception as e:
            return jsonify({'status': 'degraded', 'database': 'unreachable', 'error': str(e)}), 503

    @app.route('/todos', methods=['GET'])
    def list_todos():
        db = SessionLocal()
        try:
            todos = db.query(Todo).order_by(Todo.id.asc()).all()
            return jsonify([t.as_dict() for t in todos])
        finally:
            db.close()

    @app.route('/todos', methods=['POST'])
    def create_todo():
        db = SessionLocal()
        data = request.get_json(silent=True) or {}
        title = data.get('title')
        if not title:
            return jsonify({'error': 'title is required'}), 400
        try:
            todo = Todo(title=title, done=bool(data.get('done', False)))
            db.add(todo)
            db.commit()
            db.refresh(todo)
            return jsonify(todo.as_dict()), 201
        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/todos/<int:todo_id>', methods=['PUT', 'PATCH'])
    def update_todo(todo_id):
        db = SessionLocal()
        data = request.get_json(silent=True) or {}
        try:
            todo = db.get(Todo, todo_id)  # SQLAlchemy 2.x style
            if not todo:
                return jsonify({'error': 'not found'}), 404
            if 'title' in data:
                todo.title = data['title']
            if 'done' in data:
                todo.done = bool(data['done'])
            db.commit()
            db.refresh(todo)
            return jsonify(todo.as_dict())
        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/todos/<int:todo_id>', methods=['DELETE'])
    def delete_todo(todo_id):
        db = SessionLocal()
        try:
            todo = db.get(Todo, todo_id)  # SQLAlchemy 2.x style
            if not todo:
                return jsonify({'error': 'not found'}), 404
            db.delete(todo)
            db.commit()
            return ('', 204)
        except SQLAlchemyError as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
