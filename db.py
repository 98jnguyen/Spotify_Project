from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy


db_app = Flask(__name__)

db_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(db_app)

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(512), nullable=False)
    refresh_token = db.Column(db.String(512), nullable=False)

    def to_dict(self):
        return {
            'id':self.id,
            'access_token':self.access_token,
            'refresh_token':self.refresh_token
        }
    
with db_app.app_context():
    db.create_all()

@db_app.route('/data', methods=['GET'])
def get_data():
    items = UserData.query.all()
    return jsonify([item.to_dict() for item in items])



@db_app.route('/store', methods=['POST'])
def store_token():
    data = request.get_json()
    #print(data)
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    
    if access_token and refresh_token:
        try:
            existing_token = UserData.query.first()
            if existing_token:
                existing_token.access_token = access_token
                existing_token.refresh_token = refresh_token
                db.session.commit()
                return jsonify(existing_token.to_dict()),200
            else:
                new_token = UserData(access_token=access_token, refresh_token=refresh_token)
                db.session.add(new_token)
                db.session.commit()
                return jsonify(new_token.to_dict()), 201
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error:": str(e)}), 500
    return jsonify({"error": "No access token provided"}), 400

@db_app.route('/delete/<int:id>', methods=['DELETE'])
def delete_entries(id):
    try:
        token_to_delete = UserData.query.get(id)
        if token_to_delete:
            db.session.delete(token_to_delete)
            db.session.commit()
            return jsonify({"message": "Token deleted successfully"}), 200
        else:
            return jsonify({"message":"Failed to delete token"}),404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    db_app.run(port=5000, debug=True)